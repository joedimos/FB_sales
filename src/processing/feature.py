import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERICAL_FEATURES = ["vehicle_price", "vehicle_mileage", "days_on_lot", "lead_age_hours"]
CATEGORICAL_FEATURES = ["vehicle_make", "lead_source_platform", "crm_source"]


def create_raw_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create deterministic features shared by training and online prediction."""
    result = df.copy()
    for col in ["created_at", "updated_at", "closed_at", "time_of_prediction"]:
        if col in result.columns:
            result[col] = pd.to_datetime(result[col], errors="coerce", utc=True)

    if "created_at" in result.columns:
        if "time_of_prediction" in result.columns:
            end = result["time_of_prediction"]
        elif "updated_at" in result.columns:
            end = result["updated_at"].copy()
            if "closed_at" in result.columns:
                end = result["closed_at"].where(result["closed_at"].notna(), end)
        else:
            end = pd.Series(pd.Timestamp.now(tz="UTC"), index=result.index)
        result["lead_age_hours"] = (end - result["created_at"]).dt.total_seconds().div(3600).clip(lower=0)
    else:
        result["lead_age_hours"] = np.nan
    return result


preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), NUMERICAL_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ],
    remainder="drop",
)
