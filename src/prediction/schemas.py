import datetime
from pydantic import BaseModel, Field


class LeadPredictInput(BaseModel):
    crm_lead_id: str
    crm_source: str = "VinSolutions"
    created_at: datetime.datetime
    vehicle_id: int
    vehicle_price: float
    vehicle_mileage: float
    vehicle_make: str
    days_on_lot: int
    lead_source_platform: str = "Facebook Marketplace"
    time_of_prediction: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class PredictionOutput(BaseModel):
    crm_lead_id: str
    likelihood_score: float
