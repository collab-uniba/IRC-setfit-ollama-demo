import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class ModelConfig:
    name: str
    path: str
    default: bool = False

class ModelConfigLoader:
    def __init__(self, config_path: str = "models/models_config.yaml"):
        self.config_path = config_path
        self.setfit_models: List[ModelConfig] = []
        self.ollama_models: List[ModelConfig] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load model configurations from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            # Load SetFit models
            for model in config.get('setfit_models', []):
                self.setfit_models.append(ModelConfig(**model))
                
            # Load Ollama models
            for model in config.get('ollama_models', []):
                self.ollama_models.append(ModelConfig(**model))
                
            logger.info(f"Loaded {len(self.setfit_models)} SetFit models and {len(self.ollama_models)} Ollama models")
        except Exception as e:
            logger.error(f"Error loading model config: {str(e)}")
            raise

    def get_model_choices(self, model_type: str) -> List[str]:
        """Get list of model paths for the specified type"""
        models = self.setfit_models if model_type == "setfit" else self.ollama_models
        return [model.path for model in models]

    def get_model_names(self, model_type: str) -> List[str]:
        """Get list of model display names for the specified type"""
        models = self.setfit_models if model_type == "setfit" else self.ollama_models
        return [model.name for model in models]

    def get_default_model(self, model_type: str) -> Optional[str]:
        """Get the default model path for the specified type"""
        models = self.setfit_models if model_type == "setfit" else self.ollama_models
        for model in models:
            if model.default:
                return model.path
        return models[0].path if models else None
