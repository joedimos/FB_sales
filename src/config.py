import os
import yaml

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml"))


def load_config():
    """Load application configuration and expose a few backwards-compatible keys."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    database = config.get("database", {})
    model = config.get("model", {})
    # Older modules expect flat names; keep those modules working while using the
    # clearer nested YAML structure.
    config.setdefault("database_url", os.getenv("DATABASE_URL", database.get("url", "sqlite:///fb_sales.db")))
    config.setdefault("model_path", os.getenv("MODEL_PATH", model.get("path", "models/transaction_predictor.joblib")))
    return config


settings = load_config()
