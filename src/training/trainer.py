import datetime
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from src.config import settings
from src.processing.data_cleaning import clean_data
from src.processing.feature import create_raw_features, NUMERICAL_FEATURES, CATEGORICAL_FEATURES
from src.storage.database import SessionLocal
from src.storage.models import LeadStatus
from src.training.evaluator import evaluate_model
from src.training.pipeline import build_model_pipeline

MODEL_PATH = settings.get("model", {}).get("path")
if not MODEL_PATH:
    raise ValueError("Model path not specified in settings.yaml")
os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)


def load_historical_data(db: Session) -> pd.DataFrame:
    """Generate deterministic demo history until a production CRM history source is configured."""
    rng = np.random.default_rng(42)
    data = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for i in range(1000):
        converted = int(rng.choice([0, 1], p=[0.7, 0.3]))
        created_at = now - datetime.timedelta(days=int(rng.integers(1, 365)), hours=int(rng.integers(1, 24)))
        closed_at = None
        status = LeadStatus.STALE.value
        if converted:
            closed_at = created_at + datetime.timedelta(days=int(rng.integers(1, 30)), hours=int(rng.integers(1, 24)))
            status = LeadStatus.WON.value
        elif (now - created_at).days > 90:
            closed_at = min(now, created_at + datetime.timedelta(days=int(rng.integers(1, 90))))
            status = LeadStatus.LOST.value

        message_length = int(rng.integers(20, 500))
        data.append({
            "id": i + 1,
            "current_status": status,
            "initial_message": "Interested in this vehicle. " * max(1, message_length // 28),
            "created_at": created_at,
            "updated_at": closed_at or now,
            "closed_at": closed_at,
            "is_converted": converted,
            "vehicle_price": float(rng.integers(5000, 80000)),
            "vehicle_mileage": float(rng.integers(1000, 200000)),
            "vehicle_make": str(rng.choice(["Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes", "Other"])),
            "days_on_lot": int(rng.integers(5, 180)),
            "crm_source": str(rng.choice(["VinSolutions", "CDK", "Reynolds"])),
            "lead_source_platform": "Facebook Marketplace",
        })
    return pd.DataFrame(data)


def train_model(db: Session):
    df = load_historical_data(db)
    if df.empty:
        raise RuntimeError("No historical data available for training")

    df = clean_data(df.copy())
    df = create_raw_features(df.copy())

    for col in NUMERICAL_FEATURES:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = "Unknown"
        df[col] = df[col].fillna("Unknown").astype(str)

    X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df["is_converted"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model_pipeline = build_model_pipeline()
    model_pipeline.fit(X_train, y_train)
    metrics = evaluate_model(model_pipeline, X_test, y_test)
    joblib.dump(model_pipeline, MODEL_PATH)
    return metrics


def train_model_script():
    db = SessionLocal()
    try:
        return train_model(db)
    finally:
        db.close()


if __name__ == "__main__":
    train_model_script()
