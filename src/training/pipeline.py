from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

from src.processing.feature import preprocessor


def build_model_pipeline():
    """Build the preprocessing + classification pipeline."""
    classifier = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        max_depth=10,
        n_jobs=-1,
    )
    return Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])
