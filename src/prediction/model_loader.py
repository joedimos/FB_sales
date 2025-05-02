import joblib
import os
from src.config import settings

MODEL_PATH = settings.get("model", {}).get("path")
if MODEL_PATH is None:
     raise ValueError("Model path not specified in settings.yaml")

def load_model_pipeline():
    """Loads the trained model pipeline from the file system."""
    if not os.path.exists(MODEL_PATH):
        print(f"Warning: Model file not found at {MODEL_PATH}. Prediction service will not work.")
        return None
    try:
        print(f"Loading model from {MODEL_PATH}...")
        model_pipeline = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
        return model_pipeline
    except Exception as e:
        print(f"Error loading model from {MODEL_PATH}: {e}")
        return None

# Global variable to hold the loaded model
# Initialized to None, loaded on application startup
model_pipeline = None
