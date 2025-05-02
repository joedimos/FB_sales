# src/training/trainer.py
import pandas as pd
from sqlalchemy.orm import Session
from src.storage.database import get_db, SessionLocal # Need SessionLocal for script usage
from src.storage.models import Lead, Vehicle, CRMData, LeadStatus
from src.processing.data_cleaning import clean_data # Import cleaning
from src.processing.feature_engineering import create_raw_features, NUMERICAL_FEATURES, CATEGORICAL_FEATURES # Import feature creation
from src.training.pipeline import build_model_pipeline
from src.training.evaluator import evaluate_model
from src.config import settings
from sklearn.model_selection import train_test_split
import joblib
import os
import datetime
import numpy as np # For synthetic data

MODEL_PATH = settings.get("model", {}).get("path")
if MODEL_PATH is None:
     raise ValueError("Model path not specified in settings.yaml")
MODEL_DIR = os.path.dirname(MODEL_PATH)
os.makedirs(MODEL_DIR, exist_ok=True)


def load_historical_data(db: Session) -> pd.DataFrame:
    """
    Loads historical data (converted and unconverted leads) for training.
    This query needs to fetch all necessary fields from joined tables.
    """
    print("Loading historical data from database...")
    # Fetch Leads, joining with CRMData and Vehicle
    # Filter for leads that have reached a conclusive status (WON or LOST)
    # In a real scenario, you might include STALE leads as '0' target
    # and potentially leads that have been open for a very long time.
    # The definition of 'is_converted' (the target variable) is crucial.
    # Let's define 'is_converted' as 1 for WON, 0 for LOST or STALE (older than X days)

    # For demo, let's fetch all leads that have been updated at least once,
    # and synthesize 'is_converted' based on a rule or random assignment
    # since our dummy ingestion doesn't set WON/LOST status realistically yet.

    # --- Real-world approach ---
    # query = db.query(Lead, Vehicle, CRMData)\
    #           .join(Vehicle)\
    #           .join(CRMData)\
    #           .filter(Lead.current_status.in_([LeadStatus.WON, LeadStatus.LOST]))
    # results = query.all()
    # data = []
    # for lead, vehicle, crm_data in results:
    #      row = lead.__dict__.copy()
    #      row.update(vehicle.__dict__)
    #      row.update(crm_data.__dict__) # Include CRM data fields if needed
    #      row.pop('_sa_instance_state', None) # Clean up SQLAlchemy internals
    #      # Determine target variable
    #      row['is_converted'] = 1 if lead.current_status == LeadStatus.WON else 0
    #      # Calculate lead_age_hours based on closure time for closed leads
    #      if lead.closed_at and lead.created_at:
    #           row['lead_age_hours'] = (lead.closed_at - lead.created_at).total_seconds() / 3600
    #      # For open leads in training data (if included), calculate age until data snapshot time
    #      # This gets complicated. A simpler approach might be to only train on completed leads.
    #      # Or, include leads open longer than a threshold, labeling them 0.
    #      data.append(row)

    # --- Synthetic Data Generation for Demo ---
    print("Generating synthetic training data...")
    num_samples = 1000
    data = []
    for i in range(num_samples):
        is_converted = np.random.choice([0, 1], p=[0.7, 0.3]) # Simulate 30% conversion rate
        created_at = datetime.datetime.utcnow() - datetime.timedelta(days=np.random.randint(1, 365), hours=np.random.randint(1, 24))
        closed_at = None
        status = LeadStatus.STALE.value if is_converted == 0 else LeadStatus.WON.value
        if is_converted == 1:
             closed_at = created_at + datetime.timedelta(days=np.random.randint(1, 30), hours=np.random.randint(1, 24))
             status = LeadStatus.WON.value
        elif (datetime.datetime.utcnow() - created_at).total_seconds() / (3600 * 24) > 90: # Older than 90 days, mark LOST/STALE
            closed_at = datetime.datetime.utcnow() - datetime.timedelta(days=np.random.randint(1, 30))
            status = LeadStatus.LOST.value # Or STALE


        vehicle_id = np.random.randint(1, 100) # Dummy vehicle ID
        vehicle_price = np.random.randint(5000, 80000)
        vehicle_mileage = np.random.randint(1000, 200000)
        vehicle_make = np.random.choice(['Toyota', 'Honda', 'Ford', 'Chevrolet', 'BMW', 'Mercedes', 'Other'])
        days_on_lot = np.random.randint(5, 180)

        # Simulate interaction count
        num_interactions = np.random.randint(1, 15 if is_converted == 1 else 10)
        # Simulate initial message length
        initial_message_length = np.random.randint(20, 500)

        data.append({
            'id': i + 1, # Dummy ID
            'crm_data_fk': i + 1, # Dummy FK
            'vehicle_id': vehicle_id,
            'current_status': status,
            'initial_message': 'This is a simulated message ' * (initial_message_length // 30), # Make message length somewhat realistic
            'created_at': created_at,
            'updated_at': closed_at if closed_at else datetime.datetime.utcnow(), # Use closed_at for conversion, otherwise current time
            'closed_at': closed_at,
            'is_converted': is_converted,
            'predicted_likelihood': None, # Not predicted yet

            # Vehicle fields (simulate joining)
            'vehicle_price': float(vehicle_price),
            'vehicle_mileage': float(vehicle_mileage),
            'vehicle_make': vehicle_make,
            'days_on_lot': days_on_lot,

            # Other potential features to simulate
            'crm_source': np.random.choice(['VinSolutions', 'CDK', 'Reynolds']),
            'lead_source_platform': 'Facebook Marketplace', # Or sometimes Direct, Website etc.
            'num_interactions': num_interactions # Requires Interaction data in real DB
        })

    df = pd.DataFrame(data)
    print(f"Generated {len(df)} synthetic samples.")

    # Calculate lead_age_hours for synthetic data
    # For closed leads, use closed_at - created_at
    # For unclosed leads (status != WON/LOST), use latest_update/now - created_at
    # We will use the create_raw_features function which handles datetime conversion
    return df

def train_model(db: Session):
    """Orchestrates the model training process."""
    print("Starting model training process...")

    # 1. Load Data
    df = load_historical_data(db)

    if df.empty:
        print("No historical data found for training.")
        return

    # 2. Clean Data (Optional, could be part of pipeline)
    df = clean_data(df.copy())

    # 3. Create Raw Features (Fields like lead_age_hours, message_length etc.)
    # Note: For `lead_age_hours` in training, we use `closed_at` if available,
    # otherwise the `updated_at` or a snapshot time. The create_raw_features
    # function needs to handle this training-specific calculation vs. prediction time.
    # For the synthetic data, lead_age_hours is calculated in load_historical_data directly,
    # or we can rely on create_raw_features if it handles the logic based on available dates.
    # Let's make create_raw_features handle both training and prediction logic based on input.
    # For training, we might need to pass a `snapshot_time` or rely on `updated_at`.
    # Let's add 'snapshot_time' to the training data simulation or as a parameter.
    # Simpler: rely on the calculation in create_raw_features using available dates.
    # Let's add a dummy 'time_of_prediction' column set to current time for calculation in `create_raw_features`
    # to simulate the calculation logic used during prediction.
    df['time_of_prediction'] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


    df = create_raw_features(df.copy())


    # Ensure all expected feature columns exist after raw feature creation
    all_expected_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    for col in all_expected_cols:
         if col not in df.columns:
              print(f"Warning: Feature column '{col}' not found in DataFrame. Will use dummy values.")
              if col in NUMERICAL_FEATURES:
                   df[col] = df[col].fillna(0.0) # Or median/mean from historical data
              elif col in CATEGORICAL_FEATURES:
                   df[col] = df[col].fillna('Missing')


    # Select features (X) and target (y)
    # Use the list of columns that the preprocessor expects BEFORE transformation
    # Ensure the order of columns in X matches what the preprocessor was built with
    # This requires careful coordination between feature_engineering.py and trainer.py
    # A robust way is to explicitly list the input columns for the preprocessor
    # and pass them here. Let's refine feature_engineering.py to expose these lists.
    X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES].copy() # Select the columns to be fed into the preprocessor
    y = df['is_converted']


    # 4. Split Data
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
    print(f"Train conversion rate: {y_train.mean():.4f}, Test conversion rate: {y_test.mean():.4f}")


    # 5. Build & Train Model Pipeline
    print("Building and training model pipeline...")
    model_pipeline = build_model_pipeline()
    model_pipeline.fit(X_train, y_train)
    print("Training complete.")


    # 6. Evaluate Model
    metrics = evaluate_model(model_pipeline, X_test, y_test)


    # 7. Save Model Pipeline
    print(f"Saving model pipeline to {MODEL_PATH}...")
    try:
        joblib.dump(model_pipeline, MODEL_PATH)
        print("Model pipeline saved successfully.")
    except Exception as e:
        print(f"Error saving model: {e}")

    print("Model training process finished.")
    return metrics # Optional: return metrics


# Helper function to run training directly from script
def train_model_script():
    """Helper to run train_model using a database session."""
    db = SessionLocal()
    try:
        train_model(db)
    finally:
        db.close()


if __name__ == '__main__':
    train_model_script()
