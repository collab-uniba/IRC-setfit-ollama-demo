"""
Thread-safe manager for reading and writing label configuration.
"""
import yaml
import os
from threading import Lock
from typing import List, Dict, Optional
from pathlib import Path

class LabelConfigManager:
    """Manages reading and writing of label configuration with thread safety."""
    
    def __init__(self, config_path: str = None):
        """Initialize the label config manager.
        
        Args:
            config_path: Path to the labels_config.yaml file. 
                        Defaults to labels_config.yaml in the same directory.
        """
        if config_path is None:
            # Default to labels_config.yaml in the same directory as this file
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'labels_config.yaml'
            )
        self.config_path = config_path
        self._lock = Lock()
        
    def read_labels(self) -> List[Dict[str, str]]:
        """Read labels from the configuration file.
        
        Returns:
            List of label dictionaries with 'name' and 'description' keys.
        """
        with self._lock:
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('labels', [])
            except FileNotFoundError:
                # Return default labels if file doesn't exist
                return [
                    {
                        'name': 'bug',
                        'description': "The 'bug' label is used to identify an issue report that describes a problem or error within the software or codebase."
                    },
                    {
                        'name': 'non-bug',
                        'description': "The 'non-bug' label is applied to any issue that is not a bug."
                    }
                ]
            except Exception as e:
                raise Exception(f"Error reading labels config: {str(e)}")
    
    def write_labels(self, labels: List[Dict[str, str]]) -> None:
        """Write labels to the configuration file.
        
        Args:
            labels: List of label dictionaries with 'name' and 'description' keys.
        """
        with self._lock:
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                config = {'labels': labels}
                with open(self.config_path, 'w') as f:
                    yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            except Exception as e:
                raise Exception(f"Error writing labels config: {str(e)}")
    
    def get_label_names(self) -> List[str]:
        """Get list of label names.
        
        Returns:
            List of label names.
        """
        labels = self.read_labels()
        return [label['name'] for label in labels]
    
    def get_label_descriptions(self) -> Dict[str, str]:
        """Get dictionary mapping label names to descriptions.
        
        Returns:
            Dictionary with label names as keys and descriptions as values.
        """
        labels = self.read_labels()
        return {label['name']: label['description'] for label in labels}
    
    def add_label(self, name: str, description: str) -> None:
        """Add a new label to the configuration.
        
        Args:
            name: Name of the label.
            description: Description of the label.
        
        Raises:
            ValueError: If label with the same name already exists.
        """
        labels = self.read_labels()
        
        # Check if label already exists
        if any(label['name'] == name for label in labels):
            raise ValueError(f"Label '{name}' already exists")
        
        labels.append({'name': name, 'description': description})
        self.write_labels(labels)
    
    def update_label(self, old_name: str, new_name: str, description: str) -> None:
        """Update an existing label.
        
        Args:
            old_name: Current name of the label.
            new_name: New name for the label.
            description: New description for the label.
        
        Raises:
            ValueError: If label doesn't exist or new name conflicts with existing label.
        """
        labels = self.read_labels()
        
        # Find the label to update
        label_found = False
        for i, label in enumerate(labels):
            if label['name'] == old_name:
                label_found = True
                # Check if new name conflicts with another label
                if new_name != old_name and any(l['name'] == new_name for l in labels):
                    raise ValueError(f"Label '{new_name}' already exists")
                labels[i] = {'name': new_name, 'description': description}
                break
        
        if not label_found:
            raise ValueError(f"Label '{old_name}' not found")
        
        self.write_labels(labels)
    
    def delete_label(self, name: str) -> None:
        """Delete a label from the configuration.
        
        Args:
            name: Name of the label to delete.
        
        Raises:
            ValueError: If label doesn't exist or trying to delete the last label.
        """
        labels = self.read_labels()
        
        if len(labels) <= 1:
            raise ValueError("Cannot delete the last label. At least one label must exist.")
        
        # Filter out the label to delete
        new_labels = [label for label in labels if label['name'] != name]
        
        if len(new_labels) == len(labels):
            raise ValueError(f"Label '{name}' not found")
        
        self.write_labels(new_labels)
    
    def format_label_explanations(self) -> str:
        """Format label explanations for use in prompts.
        
        Returns:
            Formatted string with all label explanations.
        """
        labels = self.read_labels()
        explanations = []
        for label in labels:
            explanations.append(f'The "{label["name"]}" label: {label["description"]}')
        return '\n'.join(explanations)
    
    def get_label_list_string(self) -> str:
        """Get a comma-separated string of label names for prompts.
        
        Returns:
            String like '"bug", "non-bug"'
        """
        names = self.get_label_names()
        return ', '.join([f'"{name}"' for name in names])


# Global instance
_label_manager = None

def get_label_manager() -> LabelConfigManager:
    """Get the global label config manager instance.
    
    Returns:
        The global LabelConfigManager instance.
    """
    global _label_manager
    if _label_manager is None:
        _label_manager = LabelConfigManager()
    return _label_manager
