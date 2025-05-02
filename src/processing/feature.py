import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import datetime

# Define feature columns expected by the preprocessor
# This list MUST be consistent between training and prediction
NUMERICAL_FEATURES = ['vehicle_price', 'vehicle_mileage', 'days_on_lot', 'lead_age_hours']
CATEGORICAL_FEATURES = ['vehicle_make', 'lead_source_platform', 'crm_source'] # Include CRM source as a feature?

def create_raw_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates new features from raw or cleaned data before transformations.
    This function should be applied to both training and prediction data.
    """
    print("Creating raw features...")

    # Ensure datetime columns are in the correct format (ideally done in cleaning)
    for col in ['created_at', 'updated_at', 'closed_at']:
        if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
             pass # Already datetime
        elif col in df.columns:
             df[col] = pd.to_datetime(df[col], errors='coerce', utc=True) # Convert to UTC datetime

    # Feature: Lead Age in Hours (calculate relative to 'now' for prediction)
    if 'created_at' in df.columns:
        # For training data loaded from DB, 'now' is implicit in the snapshot time
        # For prediction, use current time
        # Let's calculate based on 'updated_at' for a stable training feature,
        # or explicitly use a fixed point in time for training data snapshot.
        # For prediction, we need to use the time of prediction.
        # Let's make lead_age_hours a dynamic feature calculated based on current time
        # For training data, we'll need a snapshot timestamp or calculate based on a fixed reference.
        # A simpler approach: calculate based on 'updated_at' for both, or
        # require the 'time_of_prediction' in the input for real-time scoring
        # Let's calculate based on `updated_at` as a proxy for how long it's been *since* the lead was last active/updated.
        # OR, let's calculate `lead_age_hours` relative to `created_at` for leads that are not closed.
        # For closed leads, calculate duration until closure.
        # This needs careful handling for the target variable definition!

        # Let's assume for the training data, `lead_age_hours` represents the duration
        # until the lead was marked WON/LOST (for closed leads)
        # or the duration until the training data snapshot time (for open leads).
        # For *prediction*, we calculate `lead_age_hours` relative to `now()`.

        # --- Handling lead_age_hours for Prediction ---
        if 'time_of_prediction' in df.columns and 'created_at' in df.columns:
             df['time_of_prediction'] = pd.to_datetime(df['time_of_prediction'], errors='coerce', utc=True)
             # Use the time of prediction if provided (for scoring new leads)
             df['lead_age_hours'] = (df['time_of_prediction'] - df['created_at']).dt.total_seconds() / 3600
        elif 'created_at' in df.columns and 'updated_at' in df.columns:
             # Fallback/Training data calculation: age based on last update
             df['lead_age_hours'] = (df['updated_at'] - df['created_at']).dt.total_seconds() / 3600
             # For closed leads, this should ideally be duration to closed_at
             if 'closed_at' in df.columns:
                  closed_mask = df['closed_at'].notna()
                  df.loc[closed_mask, 'lead_age_hours'] = (df.loc[closed_mask, 'closed_at'] - df.loc[closed_mask, 'created_at']).dt.total_seconds() / 3600

        else:
             df['lead_age_hours'] = np.nan # Cannot calculate if created_at is missing


    # Feature: Initial message length
    if 'initial_message' in df.columns:
        df['initial_message_length'] = df['initial_message'].fillna('').apply(len)
        NUMERICAL_FEATURES.append('initial_message_length') # Add this dynamic feature


    # Add more complex features here:
    # - Number of interactions (requires Interaction data)
    # - Time since last interaction
    # - Sentiment of initial message
    # - Vehicle age (current_year - vehicle_year)
    # - Price relative to typical price for make/model/year

    print("Raw feature creation complete.")
    return df

# Define the preprocessing pipeline using ColumnTransformer
# This handles scaling numerical features and one-hot encoding categorical ones.
# `handle_unknown='ignore'` is important for categorical features during prediction
# if new categories appear that weren't in the training data.
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), NUMERICAL_FEATURES),
        ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES)
    ],
    remainder='passthrough' # Keep other columns (like IDs, timestamps)
)

# Note: The preprocessor needs to be *fitted* on the training data
# and then the *same fitted* preprocessor is used for *transforming* both
# training and prediction data. This is handled in the sklearn Pipeline.
