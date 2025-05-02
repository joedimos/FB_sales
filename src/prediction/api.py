from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import datetime

from src.storage.database import get_db
from src.storage.models import Lead # Assuming you might want to update the lead in DB
from src.prediction_service.schemas import LeadPredictInput, PredictionOutput
from src.prediction_service.model_loader import load_model_pipeline, model_pipeline as loaded_model_pipeline # Import the global variable and loader
from src.processing.feature_engineering import create_raw_features, NUMERICAL_FEATURES, CATEGORICAL_FEATURES # Import feature creation and column lists
from src.crm_writeback.writeback_manager import writeback_score_to_crm # Import writeback function


# --- FastAPI App Setup ---
app = FastAPI(
    title="FB Marketplace Lead Predictor API",
    description="API for predicting the likelihood of a lead completing a transaction.",
    version="0.1.0",
)

# --- Model Loading on Startup ---
@app.on_event("startup")
async def startup_event():
    """Load the model when the FastAPI app starts."""
    global loaded_model_pipeline # Use the global variable
    loaded_model_pipeline = load_model_pipeline()
    if loaded_model_pipeline is None:
        print("Startup failed: Could not load the model.")
        # Depending on severity, you might want to raise an exception here
        # to prevent the app from starting if prediction is critical.
        # raise RuntimeError("Failed to load ML model")


# --- Prediction Endpoint ---
@app.post("/predict", response_model=PredictionOutput)
async def predict_lead_likelihood(
    lead_data_input: LeadPredictInput,
    db: Session = Depends(get_db) # Get a DB session
):
    """
    Receives lead data and returns a transaction likelihood score.
    """
    # Check if model is loaded
    if loaded_model_pipeline is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded. Cannot make predictions.")

    # --- Data Preparation ---
    # Convert Pydantic input to a Pandas DataFrame row
    # This structure MUST match the data used for create_raw_features and training
    input_data_dict = lead_data_input.dict()

    # Ensure expected datetime format
    input_data_dict['created_at'] = input_data_dict['created_at'].replace(tzinfo=datetime.timezone.utc)
    # input_data_dict['updated_at'] = input_data_dict['updated_at'].replace(tzinfo=datetime.timezone.utc) if input_data_dict.get('updated_at') else None
    input_data_dict['time_of_prediction'] = input_data_dict['time_of_prediction'].replace(tzinfo=datetime.timezone.utc)


    df_row = pd.DataFrame([input_data_dict])

    # Apply the raw feature creation function
    # This function needs to correctly handle the 'time_of_prediction' column
    # to calculate lead_age_hours correctly for scoring *new* data.
    try:
        df_row_features = create_raw_features(df_row.copy())
    except Exception as e:
        print(f"Error during raw feature creation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error during feature engineering: {e}")


    # Select the columns that the *preprocessor* inside the pipeline expects
    # This list and order MUST match the columns fed into the preprocessor during training
    # Ensure all expected columns are present, even if with dummy values (e.g., 0 or 'Unknown')
    # if they weren't provided in the input. This is crucial for the preprocessor's ColumnTransformer.
    # A more robust way is to define ALL possible input columns expected by raw_feature_creation
    # and the preprocessor beforehand and ensure the input or fetching covers them.

    # For this example, let's manually ensure the columns expected by the preprocessor exist
    expected_input_cols_for_pipeline = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

    # Check for missing columns and add them if necessary (with default values, requires careful design)
    # A better approach: the input schema/data fetching guarantees necessary fields.
    # For demonstration, let's assume the input contains all required raw features.
    # If not, you'd need more complex logic here to fetch missing data (e.g., from DB)
    # or impute defaults before selecting columns for X_predict.

    try:
        # Select the columns needed for the preprocessor, ensuring order matches training
        X_predict = df_row_features[expected_input_cols_for_pipeline]
    except KeyError as e:
        print(f"Missing column(s) required for prediction: {e}")
        raise HTTPException(status_code=400, detail=f"Missing required input data for feature engineering: {e}")
    except Exception as e:
         print(f"Error preparing prediction data: {e}")
         raise HTTPException(status_code=500, detail=f"Internal error preparing data: {e}")


    # --- Prediction ---
    try:
        # The pipeline handles both preprocessing and prediction
        # predict_proba returns probabilities [P(class_0), P(class_1)]
        prediction_proba = loaded_model_pipeline.predict_proba(X_predict)[:, 1] # Get probability of the positive class (1=WON)
        likelihood_score = float(prediction_proba[0]) # Extract the single score
    except Exception as e:
        print(f"Error during model prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error during prediction: {e}")


    # --- Post-Prediction Actions (Optional) ---
    # 1. Write score back to your internal DB (Lead table)
    # Assuming you can match the lead_data_input to a Lead record in your DB
    try:
        # Find the Lead record based on crm_lead_id and crm_source
        # This assumes crm_lead_id is unique within a crm_source and mapped to your Lead table
        lead_record = db.query(Lead).join(Lead.crm_data).filter(
             CRMData.crm_lead_id == lead_data_input.crm_lead_id,
             CRMData.crm_source == lead_data_input.crm_source
        ).first()

        if lead_record:
            lead_record.predicted_likelihood = likelihood_score
            db.commit()
            db.refresh(lead_record) # Refresh to see updated value
            print(f"Updated lead {lead_record.id} with score {likelihood_score}")
        else:
            print(f"Warning: Lead with crm_lead_id={lead_data_input.crm_lead_id}, crm_source={lead_data_input.crm_source} not found in internal DB for update.")
            # In a real system, you might want to handle this - perhaps the lead hasn't been ingested yet?
            # Or the mapping logic needs refinement.
    except Exception as e:
        db.rollback() # Rollback DB session on error
        print(f"Error updating internal database with score: {e}")
        # Decide if this error should prevent the API response or just log


    # 2. Write score back to the originating CRM
    try:
        writeback_score_to_crm(
            crm_source=lead_data_input.crm_source,
            crm_lead_id=lead_data_input.crm_lead_id,
            score=likelihood_score
        )
    except Exception as e:
        print(f"Error writing score back to CRM {lead_data_input.crm_source}: {e}")
        # Decide if this error should prevent the API response or just log


    # --- Return Response ---
    return PredictionOutput(
        crm_lead_id=lead_data_input.crm_lead_id,
        likelihood_score=likelihood_score
    )

# --- Health Check Endpoint (Optional but Recommended) ---
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    status = "ok"
    model_status = "loaded" if loaded_model_pipeline is not None else "not loaded"
    db_status = "ok"
    try:
        db = next(get_db())
        db.execute("SELECT 1") # Simple query to check DB connection
    except Exception:
        db_status = "error"
        status = "degraded" # Or "error" if DB is critical

    if loaded_model_pipeline is None:
         status = "degraded" if status == "ok" else status # Stay 'error' if DB also failed

    return {"status": status, "model": model_status, "database": db_status}
