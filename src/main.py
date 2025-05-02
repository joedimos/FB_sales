import argparse
import subprocess # To run uvicorn
import sys
import os

def run_train():
    """Runs the model training script."""
    from src.training.trainer import train_model_script
    print("Starting model training...")
    train_model_script()
    print("Model training finished.")

def run_ingestion():
     """Runs the ingestion process (for the demo connector)."""
     from src.ingestion.run_ingestion import run_ingestion_script
     print("Starting data ingestion...")
     run_ingestion_script()
     print("Data ingestion finished.")


def run_api():
    """Starts the FastAPI prediction service."""
    print("Starting Prediction Service API...")
    # Use subprocess to run uvicorn command
    # Assumes uvicorn is installed in the environment
    # Adjust host/port/reload as needed
    command = [
        sys.executable, "-m", "uvicorn",
        "src.prediction_service.api:app",
        "--host", "0.0.0.0", # Listen on all interfaces
        "--port", "8000",
        "--reload" # Auto-reload code changes (useful for development)
    ]
    print(f"Executing command: {' '.join(command)}")
    subprocess.run(command)

def init_db():
    """Initializes the database."""
    from src.storage.database import init_db
    init_db()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FB Marketplace Predictor Main Entry Point")
    parser.add_argument("command", choices=["train", "ingest", "api", "init_db"], help="Command to run")

    args = parser.parse_args()

    if args.command == "init_db":
        init_db()
    elif args.command == "ingest":
         # Note: This currently only runs the VinSolutions dummy connector
         # Modify run_ingestion.py or add arguments to handle specific CRMs
         run_ingestion()
    elif args.command == "train":
        # Note: Requires data to be in the DB (run ingest first, potentially multiple times)
        # and requires synthetic data generation in load_historical_data to be enabled if no real data.
        run_train()
    elif args.command == "api":
        # Note: Requires a trained model file to exist in ./models/
        run_api()
    # python src/main.py init_db
    # python src/main.py ingest # Run multiple times
    # python src/main.py train
    # python src/main.py api
