import datetime

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.crm_writeback.writeback_manager import writeback_score_to_crm
from src.prediction.model_loader import load_model_pipeline
from src.prediction.schemas import LeadPredictInput, PredictionOutput
from src.processing.feature import CATEGORICAL_FEATURES, NUMERICAL_FEATURES, create_raw_features
from src.storage.database import get_db
from src.storage.models import CRMData, Lead

app = FastAPI(
    title="FB Marketplace Lead Predictor API",
    description="Predict the likelihood of a dealership lead completing a transaction.",
    version="1.0.0",
)
model_pipeline = None


@app.on_event("startup")
def startup_event():
    global model_pipeline
    model_pipeline = load_model_pipeline()


@app.post("/predict", response_model=PredictionOutput)
def predict_lead_likelihood(lead_data_input: LeadPredictInput, db: Session = Depends(get_db)):
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="Model is not trained. Run `python src/main.py train` first.")

    payload = lead_data_input.model_dump() if hasattr(lead_data_input, "model_dump") else lead_data_input.dict()
    payload.setdefault("lead_source_platform", "Facebook Marketplace")
    created = payload["created_at"]
    prediction_time = payload["time_of_prediction"]
    if created.tzinfo is None:
        payload["created_at"] = created.replace(tzinfo=datetime.timezone.utc)
    if prediction_time.tzinfo is None:
        payload["time_of_prediction"] = prediction_time.replace(tzinfo=datetime.timezone.utc)

    try:
        features = create_raw_features(pd.DataFrame([payload]))
        for col in NUMERICAL_FEATURES:
            if col not in features.columns:
                features[col] = 0.0
            features[col] = pd.to_numeric(features[col], errors="coerce").fillna(0.0)
        for col in CATEGORICAL_FEATURES:
            if col not in features.columns:
                features[col] = "Unknown"
            features[col] = features[col].fillna("Unknown").astype(str)
        score = float(model_pipeline.predict_proba(features[NUMERICAL_FEATURES + CATEGORICAL_FEATURES])[:, 1][0])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to score lead: {exc}") from exc

    try:
        lead = (
            db.query(Lead)
            .join(CRMData, Lead.crm_data_fk == CRMData.id)
            .filter(CRMData.crm_lead_id == lead_data_input.crm_lead_id, CRMData.crm_source == lead_data_input.crm_source)
            .first()
        )
        if lead:
            lead.predicted_likelihood = score
            db.commit()
    except Exception:
        db.rollback()

    try:
        writeback_score_to_crm(lead_data_input.crm_source, lead_data_input.crm_lead_id, score)
    except Exception:
        pass

    return PredictionOutput(crm_lead_id=lead_data_input.crm_lead_id, likelihood_score=score)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    model = "loaded" if model_pipeline is not None else "not_loaded"
    status = "ok" if database == "ok" and model == "loaded" else "degraded"
    return {"status": status, "model": model, "database": database}
