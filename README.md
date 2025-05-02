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

## Lead Arrives
A potential car buyer generates a lead from Facebook Marketplace.  
This lead is sent to the Dealership CRMs/DMS.

---

## Lead Arrives
A potential car buyer generates a lead from Facebook Marketplace.  
This lead is sent to the Dealership CRMs/DMS.

---

### 1. Data Ingestion
- Connectors pull raw and updated lead, customer, vehicle, and interaction data from the Dealership CRMs/DMS.
- This data is standardized and stored in your Central Database & Data Store.

---

### 2. Data Preparation
- Logic is applied to clean the data from the Central Database & Data Store.
- Relevant features for prediction (e.g., lead age, vehicle details, interaction history counts) are created from the cleaned data.

**Data Split Point:**  
The prepared data is split into two paths:
- **Historical Data:** Used for training the model.
- **New Lead Data:** Used for making real-time predictions.

---

### 3a. Model Training (using Historical Data)
- The system uses the prepared Historical Data to build a predictive Trained ML Model.
- This model learns patterns associated with completed transactions.

### 3b. Likelihood Prediction Service (using New Lead Data)
- The Prediction Service API receives new lead data (which goes through Data Preparation).
- It loads the Trained ML Model.
- It uses the model to calculate a transaction **Predicted Score** (a likelihood percentage).

---

### 4. Result Integration
- The Predicted Score is sent to the **CRM Writeback** component.
- The CRM Writeback pushes the score back into the originating Dealership CRMs/DMS to update the lead record.

#### Actionable Insight & Feedback Loop
- The Predicted Score is displayed in a **User Frontend Application**.
- Dealership Sales Staff access the User Frontend to view the scores.
- Staff use the score to prioritize and tailor their engagement with leads in the Dealership CRMs/DMS.
- The outcome of the sales interactions (Sale/WON or Loss/LOST/STALE), recorded back in the Dealership CRMs/DMS, feeds back into the Central Database & Data Store as historical data — completing the feedback loop for future model retraining.






---------------------------------------------------------------




### Stages of the process
    Stage1[1. Lead Arrives]:::stage
    Stage2[2. Data Collection & Storage]:::stage
    Stage3[3. Historical Data Preparation]:::stage
    Stage4[4. Model Training]:::stage
    Stage5[5. New Lead Preparation]:::stage
    Stage6[6. Likelihood Prediction]:::stage
    Stage7[7. Actionable Insight]:::stage
    Stage8[8. Feedback Loop]:::stage

### Key Actors and Components
    FB["Facebook Marketplace"]:::source
    CRM["Dealership CRMs/DMS"]:::source
    Database["Central Database (Your System)"]:::storage
    DataPrep["Data Cleaning & Feature Engineering Logic"]:::process
    MLModel[(Trained ML Model)]:::artifact
    PredictionEngine["Prediction Service API"]:::service
    Frontend["User Frontend Application"]:::ui
    Staff[Dealership Sales Staff]:::user

### Connections representing flow
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

### Feedback Loop
    Stage6 -- Prediction Score --> Stage8
    Stage8 --> CRM -- Updates Lead Record --> CRM

### Implicit steps/relationships
    Stage3 --> DataPrep -- Applied Here --> Stage4
    Stage5 --> DataPrep -- Applied Here --> Stage6
    PredictionEngine -- Hosts --> Stage6
