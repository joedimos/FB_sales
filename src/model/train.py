"""
Model training: fit a RandomForestClassifier on historical (closed) leads,
evaluate with cross-validation, and persist the model to disk.
"""
import logging
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.data_preparation.feature_engineering import build_feature_dataframe, FEATURE_COLS
from src.utils.config import get_config

logger = logging.getLogger(__name__)

MODEL_VERSION = "1.0"


def train_model():
    """Train the transaction likelihood model and save to disk."""
    cfg = get_config()
    model_path = cfg["model"]["path"]
    min_samples = cfg["model"].get("min_training_samples", 50)

    # 1. Build features
    df = build_feature_dataframe(include_open_leads=False)
    if df.empty:
        logger.error("No training data available. Run ingestion first.")
        return None

    df_labeled = df.dropna(subset=["label"])
    if len(df_labeled) < min_samples:
        logger.error(
            "Only %d labeled samples — need at least %d. Run more ingestion.",
            len(df_labeled), min_samples
        )
        return None

    X = df_labeled[FEATURE_COLS].values
    y = df_labeled["label"].astype(int).values

    logger.info("Training on %d samples (%.1f%% positive).", len(y), 100 * y.mean())

    # 2. Define pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])

    # 3. Cross-validate
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auc_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    logger.info("CV ROC-AUC: %.3f ± %.3f", auc_scores.mean(), auc_scores.std())

    # 4. Fit on full dataset
    pipeline.fit(X, y)

    y_pred = pipeline.predict(X)
    logger.info("Training set classification report:\n%s",
                classification_report(y, y_pred, target_names=["lost/stale", "won"]))

    # 5. Save model
    os.makedirs(os.path.dirname(model_path) if os.path.dirname(model_path) else ".", exist_ok=True)
    meta = {
        "pipeline": pipeline,
        "version": MODEL_VERSION,
        "feature_cols": FEATURE_COLS,
        "cv_auc_mean": float(auc_scores.mean()),
        "cv_auc_std": float(auc_scores.std()),
    }
    joblib.dump(meta, model_path)
    logger.info("Model saved to %s (v%s, AUC=%.3f)", model_path, MODEL_VERSION, auc_scores.mean())
    return meta


if __name__ == "__main__":
    train_model()
