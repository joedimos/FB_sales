import argparse
import subprocess
import sys


def run_train():
    from src.training.trainer import train_model_script
    train_model_script()


def run_ingestion():
    from src.ingestion.run_ingestion import run_ingestion_script
    run_ingestion_script()


def run_api():
    subprocess.run([
        sys.executable, "-m", "uvicorn", "src.prediction.api:app",
        "--host", "0.0.0.0", "--port", "8000"
    ], check=True)


def run_dashboard():
    subprocess.run([sys.executable, "app.py"], check=True)


def init_db():
    from src.storage.database import init_db as initialize
    initialize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FB Marketplace sales predictor")
    parser.add_argument("command", choices=["init_db", "ingest", "train", "api", "dashboard"])
    args = parser.parse_args()
    {
        "init_db": init_db,
        "ingest": run_ingestion,
        "train": run_train,
        "api": run_api,
        "dashboard": run_dashboard,
    }[args.command]()
