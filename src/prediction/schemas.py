from pydantic import BaseModel
from typing import Optional
import datetime

# Schema for the input data to the prediction API
# These fields must be sufficient to generate the features needed by the model
class LeadPredictInput(BaseModel):
    crm_lead_id: str
    crm_source: str
    created_at: datetime.datetime # Use datetime object
    # updated_at: Optional[datetime.datetime] = None # Include if available/needed for features
    # initial_message: Optional[str] = None # Include if message length/sentiment is a feature

    vehicle_id: int # Need vehicle details
    # Alternatively, pass vehicle details directly if fetching from DB is slow or not desired
    vehicle_price: float
    vehicle_mileage: float
    vehicle_make: str
    days_on_lot: int # Assumes this is available or calculated externally

    # Add other fields required for feature engineering (e.g., num_interactions if used)

    # Optional: Include a timestamp for when the prediction request is made
    # This is useful for calculating dynamic features like lead age correctly
    time_of_prediction: datetime.datetime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


# Schema for the prediction output
class PredictionOutput(BaseModel):
    crm_lead_id: str
    likelihood_score: float # Probability between 0 and 1
    # Optionally add confidence intervals, feature contributions, etc.
