# FB Marketplace Car Transaction Likelihood Predictor

This project aims to build a recommendation system to predict the likelihood of a Facebook Marketplace car lead completing a sales transaction for a car dealership.

## Project Structure

(Based on the provided structure)

## Setup

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure settings:
    Copy `config/settings.yaml.example` to `config/settings.yaml` and update with your actual database connection details and CRM API keys. (Note: I will create `settings.yaml` directly for this example, no `.example`).
4.  Initialize the database:
    ```bash
    python -c "from src.storage.database import init_db; init_db()"
    ```

## Running Components

### 1. Database Initialization

Run the command in Setup step 4.

### 2. Data Ingestion (Manual Trigger for Demo)

In a real system, this would be scheduled (e.g., via Airflow). For this demo, you can simulate ingestion:

```bash
python -c "from src.ingestion.run_ingestion import run_connector_ingestion; run_connector_ingestion()"
