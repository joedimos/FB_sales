from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import joblib
import os
import pandas as pd
from sqlalchemy.orm import Session
from src.storage.database import get_db # Assuming get_db yields a session
from src.storage.models import Lead, Vehicle # Assuming you'll fetch data by ID

# Define Pydantic model for incoming data (or use Lead ID)
class LeadPredictInput(BaseModel):
    # These fields should match the standardized data structure needed for feature engineering
    crm_lead_id: str
    crm_source: str
    created_at: str # Or datetime object
    vehicle_id: int
    # Add all other necessary fields

# --- Model Loading ---
# Load model when the application starts
MODEL_PATH = "models/latest_model_pipeline.joblib" # Path to saved pipeline
model_pipeline = None # Global variable to hold the loaded model

def load_model():
    global model_pipeline
    if os.path.exists(MODEL_PATH):
        print(f"Loading model from {MODEL_PATH}")
        model_pipeline = joblib.load(MODEL_PATH)
        print("Model loaded successfully.")
    else:
        print(f"Model file not found at {MODEL_PATH}. Prediction service will not work.")
        model_pipeline = None # Ensure it's None if file not found

# Call load_model when app starts (FastAPI startup event)
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    load_model()

# --- API Endpoint ---
@app.post("/predict")
async def predict_lead_likelihood(
    lead_data_input: LeadPredictInput,
    db: Session = Depends(get_db)
):
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")

    # Fetch additional data needed from DB using lead_data_input (e.g., vehicle details by vehicle_id)
    # Or assume lead_data_input contains ALL necessary fields directly

    # Example: Fetch data from DB using lead_data_input.crm_lead_id (need a mapping)
    # For simplicity, let's assume input contains everything needed or you map it here
    # In a real scenario, you'd fetch related data (vehicle, customer, interactions)

    # For demo, convert input data to DataFrame row
    # THIS MAPPING MUST MATCH WHAT create_features EXPECTS!
    # Need to handle vehicle_id -> actual vehicle data here if not in input
    # This part is oversimplified - needs actual data fetching/joining
    lead_dict = lead_data_input.dict()
    # Simulate fetching vehicle data by ID (replace with actual DB query)
    vehicle = db.query(Vehicle).filter(Vehicle.id == lead_data_input.vehicle_id).first()
    if not vehicle:
         raise HTTPException(status_code=404, detail=f"Vehicle with ID {lead_data_input.vehicle_id} not found.")

    # Merge data into a format suitable for feature engineering
    combined_data = {**lead_dict, **vehicle.__dict__} # Merge lead and vehicle details
    combined_data.pop('_sa_instance_state', None) # Clean up SQLAlchemy keys
    df_row = pd.DataFrame([combined_data]) # Create a DataFrame with one row

    # Apply feature engineering (only the creation part, preprocessor is in the pipeline)
    df_row_features = create_features(df_row.copy())

    # Select the columns that the preprocessor/model expects
    # This list of columns needs to be consistent with training
    feature_cols = ['vehicle_price', 'vehicle_mileage', 'lead_age_hours', 'vehicle_make', 'lead_source_platform'] # Example
    # Ensure all feature_cols are present in df_row_features, handle missing if necessary
    try:
         X_predict = df_row_features[feature_cols]
    except KeyError as e:
         raise HTTPException(status_code=400, detail=f"Missing expected feature column: {e}")

    # Apply the trained pipeline (preprocessing + prediction)
    # predict_proba gives the probability [prob_class_0, prob_class_1]
    prediction_proba = model_pipeline.predict_proba(X_predict)[:, 1] # Get probability of class 1 (WON)
    likelihood_score = float(prediction_proba[0]) # Extract the single score

    # (Optional) Write back to CRM/DB
    # from src.crm_writeback.writeback_manager import writeback_score_to_crm
    # writeback_score_to_crm(lead_data_input.crm_source, lead_data_input.crm_lead_id, likelihood_score)
    # Update score in your own database
    lead_record = db.query(Lead).filter(Lead.crm_data_id == lead_data_input.crm_lead_id).first() # Needs proper mapping
    if lead_record:
         lead_record.predicted_likelihood = likelihood_score
         db.commit()


    return {"crm_lead_id": lead_data_input.crm_lead_id, "likelihood_score": likelihood_score}

# To run this API: uvicorn src.prediction_service.api:app --reload
