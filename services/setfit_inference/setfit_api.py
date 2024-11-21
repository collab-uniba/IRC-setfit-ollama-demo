from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from setfit import SetFitModel
import logging
import yaml
from pathlib import Path
from common.issue import Issue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables to store the loaded model and configuration
loaded_model = None
current_model_name = None
model_configs = {}

class Issue(BaseModel):
    """Pydantic model for issue data"""
    title: str
    body: str
    classification: Optional[str] = None

class ClassificationRequest(BaseModel):
    """Pydantic model for classification request"""
    issues: List[Issue]
    model_name: Optional[str] = None  # Will be set to default model if None

def load_config() -> Dict:
    """
    Load configuration from YAML file
    """
    config_path = Path("config/models_config.yaml")
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise RuntimeError(f"Failed to load configuration: {str(e)}") from e

def get_default_model_path() -> str:
    """
    Get the path of the default SetFit model from configuration
    """
    for model in model_configs.get('setfit_models', []):
        if model.get('default', False):
            return model['path']
    # Fallback to first model if no default is specified
    return model_configs.get('setfit_models', [{}])[0].get('path')

def load_model(model_name: Optional[str] = None) -> SetFitModel:
    """
    Loads the SetFit model if it's not already loaded or if a different model is requested.
    """
    global loaded_model, current_model_name

    # If no model specified, use default
    if model_name is None:
        model_name = get_default_model_path()

    # Validate model exists in config
    valid_models = {model['path'] for model in model_configs.get('setfit_models', [])}
    if model_name not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model name. Available models: {valid_models}")

    if loaded_model is None or current_model_name != model_name:
        try:
            logger.info(f"Loading model: {model_name}")
            loaded_model = SetFitModel.from_pretrained(model_name)
            current_model_name = model_name
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to load model: {str(e)}"
            ) from e

    return loaded_model

def preprocess_issues(issues: List[Issue]) -> List[str]:
    """
    Preprocesses the issues for SetFit model.
    """
    return [f"{issue.title}\n\n{issue.body}" for issue in issues]

def response_postprocess(responses: List[str], issues: List[Issue]) -> List[Issue]:
    """
    Postprocesses the responses from SetFit model.
    """
    for r, i in zip(responses, issues):
        i.classification = r
    return issues

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Load configuration and default model
    logger.info("Starting up the API...")
    try:
        global model_configs
        model_configs = load_config()
        default_model = get_default_model_path()
        load_model(default_model)
        yield
    finally:
        # Shutdown: Clean up resources
        logger.info("Shutting down the API...")
        global loaded_model, current_model_name
        loaded_model = None
        current_model_name = None

# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="SetFit Classification API",
    lifespan=lifespan
)

@app.post("/classify", response_model=List[Issue])
async def classify_issues(request: ClassificationRequest):
    """
    Classifies the provided issues using the SetFit model.
    """
    try:
        # Load or get the appropriate model
        model = load_model(request.model_name)

        # Preprocess issues
        processed_issues = preprocess_issues(request.issues)

        # Get predictions
        logger.info(f"Classifying {len(request.issues)} issues")
        responses = model.predict(processed_issues)

        return response_postprocess(responses, request.issues)
    except Exception as e:
        logger.error(f"Error during classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/models")
async def get_available_models():
    """
    Returns information about available models and currently loaded model.
    """
    return {
        "current_model": current_model_name,
        "model_loaded": loaded_model is not None,
        "available_models": model_configs.get('setfit_models', []),
        "default_model": get_default_model_path()
    }