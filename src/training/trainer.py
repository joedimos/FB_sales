import pandas as pd
from sqlalchemy.orm import Session
from src.storage.models import Lead, Vehicle # Assuming joined data is complex, might need custom query
from src.processing.feature_engineering import create_features, preprocessor # Assume preprocessor is saved/loaded
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier # Or xgb/lightgbm
from sklearn.pipeline import Pipeline
import joblib # To save/load model and preprocessor
import os

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def load_training_data(db: Session) -> pd.DataFrame:
    # Complex query to join Leads, Vehicles, Interactions, etc.
    # Fetch leads marked as WON or LOST that have sufficient history
    # For simplicity, let's just fetch Lead and Vehicle data
    data = db.query(Lead, Vehicle).join(Vehicle).filter(
        Lead.current_status.in_(['WON', 'LOST'])
        # Add filters for minimum age, number of interactions if needed
    ).all()

    # Convert results to a list of dictionaries and then to DataFrame
    rows = []
    for lead, vehicle in data:
        row = lead.__dict__.copy()
        row.update(vehicle.__dict__) # Add vehicle data
        # Clean up SQLAlchemy internal keys
        row.pop('_sa_instance_state', None)
        rows.append(row)

    df = pd.DataFrame(rows)
    df['is_converted'] = df['current_status'] == 'WON' # Target variable
    return df

def train_model(db: Session):
    df = load_training_data(db)

    # Apply raw feature creation
    df = create_features(df.copy())

    # Define features (X) and target (y)
    # Select columns *before* applying the preprocessor
    # Need to ensure the columns match what the preprocessor expects
    # This part needs careful alignment with create_features and preprocessor definition
    feature_cols = ['vehicle_price', 'vehicle_mileage', 'lead_age_hours', 'vehicle_make', 'lead_source_platform'] # Example
    X = df[feature_cols]
    y = df['is_converted']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Build the full pipeline (preprocessing + model)
    # Assuming preprocessor is defined globally or loaded
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')) # class_weight='balanced' for imbalance
    ])

    # Train the model
    model_pipeline.fit(X_train, y_train)

    # Evaluate (implement evaluation logic in evaluator.py)
    # from .evaluator import evaluate_model
    # metrics = evaluate_model(model_pipeline, X_test, y_test)
    # print(metrics)

    # Save the trained pipeline
    model_path = os.path.join(MODEL_DIR, 'latest_model_pipeline.joblib')
    joblib.dump(model_pipeline, model_path)
    print(f"Model pipeline saved to {model_path}")

    # In a real system, you'd version models and save metadata (training date, metrics)
    # Potentially update a 'latest' pointer in a database or model registry

if __name__ == "__main__":
    from src.storage.database import get_db # Helper to get a session
    db = next(get_db()) # Get a database session
    train_model(db)
