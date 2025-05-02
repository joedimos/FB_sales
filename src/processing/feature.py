import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def create_features(df):
    # Example feature creation
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['now'] = pd.to_datetime('now', utc=True) # Assuming UTC timestamps
    df['lead_age_hours'] = (df['now'] - df['created_at']).dt.total_seconds() / 3600

    # Simple example of interaction feature (needs actual interaction data)
    # df['response_time_hours'] = (df['first_contact_time'] - df['created_at']).dt.total_seconds() / 3600

    # Example one-hot encoding
    categorical_features = ['vehicle_make', 'lead_source_platform'] # Add more
    numerical_features = ['vehicle_price', 'vehicle_mileage', 'lead_age_hours'] # Add more

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Apply transformations - usually done within the training pipeline
    # For prediction, you'd apply this preprocessor to new data
    # processed_df = preprocessor.fit_transform(df) # fit_transform for training data
    # processed_df = preprocessor.transform(df) # transform for new data

    return df # Return dataframe with raw features for clarity here, actual code applies preprocessor
