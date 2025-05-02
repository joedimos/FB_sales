from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier # Popular choice for performance
from src.processing.feature_engineering import preprocessor

def build_model_pipeline():
    """Builds the full scikit-learn pipeline including preprocessing and model."""
    # Choose your classifier
    # classifier = LogisticRegression(random_state=42, solver='liblinear')
    # classifier = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced', max_depth=10) # class_weight='balanced' helps with imbalance
    classifier = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42, n_estimators=200, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8)

    # Create the pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])

    return pipeline
