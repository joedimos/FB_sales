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


%% Stages of the process
    Stage1[1. Lead Arrives]:::stage
    Stage2[2. Data Collection & Storage]:::stage
    Stage3[3. Historical Data Preparation]:::stage
    Stage4[4. Model Training]:::stage
    Stage5[5. New Lead Preparation]:::stage
    Stage6[6. Likelihood Prediction]:::stage
    Stage7[7. Actionable Insight]:::stage
    Stage8[8. Feedback Loop]:::stage

    %% Key Actors and Components
    FB["Facebook Marketplace"]:::source
    CRM["Dealership CRMs/DMS"]:::source
    Database["Central Database (Your System)"]:::storage
    DataPrep["Data Cleaning & Feature Engineering Logic"]:::process
    MLModel[(Trained ML Model)]:::artifact
    PredictionEngine["Prediction Service API"]:::service
    Frontend["User Frontend Application"]:::ui
    Staff[Dealership Sales Staff]:::user

    %% Connections representing flow
    FB --> Stage1
    Stage1 --> CRM
    CRM -- Ingestion --> Stage2
    Stage2 -- Stores --> Database
    Database -- Historical Data --> Stage3
    Stage3 -- Prepared Data --> Stage4
    Stage4 -- Creates --> MLModel
    MLModel -- Used by --> Stage6
    Database -- New Lead Data --> Stage5
    Stage5 -- Prepared Data --> Stage6
    Stage6 -- Predicted Score --> Stage7
    Stage7 --> Frontend
    Frontend -- Used by --> Staff
    Staff -- Uses Score to Prioritize/Engage --> CRM

    %% Feedback Loop
    Stage6 -- Prediction Score --> Stage8
    Stage8 --> CRM -- Updates Lead Record --> CRM

    %% Implicit steps/relationships
    Stage3 --> DataPrep -- Applied Here --> Stage4
    Stage5 --> DataPrep -- Applied Here --> Stage6
    PredictionEngine -- Hosts --> Stage6

