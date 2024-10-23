#!/usr/bin/env python3
import yaml
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
from loguru import logger

def setup_logging():
    """Configure logging format"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )

def load_model_config(config_path: str) -> dict:
    """Load model configuration from YAML file"""
    try:
        # Look for config file in parent directory of the script
        config_file = Path(config_path)
        if not config_file.is_file():
            # Try looking in the parent directory
            parent_config = Path(__file__).parent.parent / config_path
            if parent_config.is_file():
                config_file = parent_config
            else:
                raise FileNotFoundError(f"Config file not found in {config_path} or parent directory")
        
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        sys.exit(1)

def pull_setfit_model(model_path: str):
    """Pull SetFit model from Hugging Face Hub using default cache location"""
    try:
        logger.info(f"Pulling SetFit model: {model_path}")
        snapshot_download(
            repo_id=model_path,
            ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.pkl"]
        )
        logger.success(f"Successfully pulled {model_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to pull {model_path}: {e}")
        return False

def main():
    setup_logging()
    logger.info("Starting SetFit model pull process")
    
    config = load_model_config("models/models_config.yaml")
    
    # Pull all SetFit models
    success = True
    for model in config.get('setfit_models', []):
        if not pull_setfit_model(model['path']):
            success = False
    
    # Summary
    logger.info("\n=== Pull Summary ===")
    if success:
        logger.success("✓ All SetFit models pulled successfully")
    else:
        logger.warning("⚠ Some SetFit models failed to pull")
        sys.exit(1)

if __name__ == "__main__":
    main()