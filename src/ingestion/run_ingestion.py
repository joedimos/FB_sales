import datetime
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.storage.database import SessionLocal # Use SessionLocal for script execution
from src.storage.models import CRMData, Lead, Vehicle, LeadStatus # Import models
from src.ingestion.vinsolutions_connector import VinSolutionsConnector # Explicitly import for demo
from src.ingestion.base import CRM_CONNECTORS # Import the map

# In a real orchestration system (like Airflow), this logic would be part of a DAG task.
# This script provides a manual way to trigger ingestion for the demo.

def get_connector_instance(crm_source: str):
    """Gets an instance of the specified CRM connector."""
    connector_class = CRM_CONNECTORS.get(crm_source)
    if not connector_class:
        print(f"Error: No connector found for CRM source: {crm_source}")
        return None
    # Connector config is loaded internally by the connector class from settings
    return connector_class()


def process_and_save_lead(db: Session, standardized_lead_data: dict):
    """
    Processes a single standardized lead and saves/updates it in the database.
    This is where raw ingested data is mapped to your internal Lead/Vehicle models.
    This logic needs refinement for handling updates to existing leads.
    """
    crm_lead_id = standardized_lead_data['crm_lead_id']
    crm_source = standardized_lead_data['crm_source']
    standardized_details = standardized_lead_data['standardized_data']
    raw_data = standardized_lead_data['raw_data']

    print(f"Processing lead: {crm_source}/{crm_lead_id}")

    try:
        # --- Handle CRMData record ---
        # Find existing CRMData entry or create a new one
        # This assumes crm_lead_id is unique within a source
        existing_crm_data = db.query(CRMData).filter(
            CRMData.crm_lead_id == crm_lead_id,
            CRMData.crm_source == crm_source
        ).first()

        if existing_crm_data:
            # Update existing CRMData record
            print(f"  CRMData exists for {crm_source}/{crm_lead_id}, updating...")
            existing_crm_data.raw_data = raw_data
            existing_crm_data.standardized_data = standardized_details
            # updated_at is handled by SQLAlchemy
            crm_data_record = existing_crm_data
        else:
            # Create new CRMData record
            print(f"  Creating new CRMData for {crm_source}/{crm_lead_id}...")
            crm_data_record = CRMData(
                crm_lead_id=crm_lead_id,
                crm_source=crm_source,
                raw_data=raw_data,
                standardized_data=standardized_details,
                created_at=standardized_details.get('created_at'),
                updated_at=standardized_details.get('updated_at', datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc))
            )
            db.add(crm_data_record)
            db.flush() # Ensure crm_data_record gets its ID

        # --- Handle Vehicle record ---
        # Vehicle details might come with the lead or require a separate fetch
        # For this demo, let's assume we need to fetch/create the Vehicle record
        # using the vehicle_interest_id from the standardized data.
        # In a real system, you might fetch detailed VIN/make/model/price/mileage data here
        # or get it directly from the lead data if available.
        vehicle_interest_id = standardized_details.get('vehicle_interest_id')
        vehicle_record = None
        if vehicle_interest_id:
             # Attempt to fetch detailed vehicle data from the CRM
             # This requires re-using the connector or having a shared service
             # For simplicity in this *processing* function, we'll skip refetching
             # and just create/find a dummy Vehicle record based on the ID.
             # A better design might fetch vehicle details *before* calling this function.

             # Find existing vehicle by a unique identifier (e.g., VIN or an internal CRM vehicle ID)
             # Assuming vehicle_interest_id from standardized_data *is* the unique key for Vehicle
             # In a real case, this would likely be VIN or dealership stock ID.
             vehicle_record = db.query(Vehicle).filter(Vehicle.id == vehicle_interest_id).first() # Use ID for simplicity

             if not vehicle_record:
                  print(f"  Vehicle {vehicle_interest_id} not found, simulating creation...")
                  # In a real scenario, fetch details using the connector here
                  # vehicle_details = connector_instance.fetch_vehicle_details(vehicle_interest_id)
                  # Then create Vehicle record using vehicle_details
                  # For demo, create a dummy vehicle record with minimal fields
                  dummy_vehicle_data = {
                      "id": vehicle_interest_id,
                      "vin": f"SIMULATED-{vehicle_interest_id}",
                      "make": standardized_details.get('raw_data', {}).get('vehicle_interest', {}).get('make', 'Unknown'),
                      "model": standardized_details.get('raw_data', {}).get('vehicle_interest', {}).get('model', 'Unknown'),
                      "year": 2020, # Dummy
                      "price": 25000.0, # Dummy
                      "mileage": 50000.0, # Dummy
                      "days_on_lot": 60 # Dummy
                  }
                  vehicle_record = Vehicle(**dummy_vehicle_data)
                  db.add(vehicle_record)
                  db.flush() # Ensure vehicle_record gets its ID

             # Ensure we have a vehicle record
             if not vehicle_record:
                  print(f"  Warning: Could not find or create vehicle record for ID {vehicle_interest_id}. Skipping lead.")
                  db.rollback() # Rollback changes for this lead
                  return # Skip processing this lead further

        else:
             print(f"  Warning: Standardized data missing 'vehicle_interest_id'. Skipping lead.")
             db.rollback()
             return


        # --- Handle Lead record ---
        # Find the Lead record associated with this CRMData entry or create a new one
        # We linked Lead.crm_data_fk uniquely to CRMData.id
        existing_lead = db.query(Lead).filter(Lead.crm_data_fk == crm_data_record.id).first()

        if existing_lead:
            print(f"  Lead record exists for CRMData {crm_data_record.id}, updating...")
            # Update lead status and other fields from standardized data
            existing_lead.current_status = LeadStatus(standardized_details.get('current_status_crm', 'NEW').lower()) # Map CRM status str to Enum
            existing_lead.updated_at = standardized_details.get('updated_at', datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc))
            existing_lead.initial_message = standardized_details.get('initial_message')

            # Check for status changes to WON or LOST to set closed_at and is_converted
            if existing_lead.current_status in [LeadStatus.WON, LeadStatus.LOST] and existing_lead.closed_at is None:
                 existing_lead.closed_at = existing_lead.updated_at # Or use a more accurate timestamp if available
                 existing_lead.is_converted = 1 if existing_lead.current_status == LeadStatus.WON else 0
                 print(f"  Lead {existing_lead.id} status changed to {existing_lead.current_status.value}. Marked as {'converted' if existing_lead.is_converted else 'not converted'}.")
            elif existing_lead.current_status not in [LeadStatus.WON, LeadStatus.LOST] and existing_lead.closed_at is not None:
                # Status changed back from closed? Unlikely but handle
                existing_lead.closed_at = None
                existing_lead.is_converted = None # Or some other value indicating unknown/in-progress state

            # Ensure is_converted is set for training data if not explicitly WON/LOST
            # For training, we might use age + status to determine if it's '0' (e.g., STALE)
            # For simplicity demo: only WON/LOST are 1/0, others are None target.
            if existing_lead.current_status == LeadStatus.WON:
                existing_lead.is_converted = 1
            elif existing_lead.current_status == LeadStatus.LOST:
                existing_lead.is_converted = 0
            # Leads still NEW, CONTACTED etc. might have is_converted as None for training
            # This needs careful handling in the training data loading query.


        else:
            print(f"  Creating new Lead record for CRMData {crm_data_record.id}...")
            # Create new Lead record
            lead_record = Lead(
                crm_data_fk=crm_data_record.id,
                vehicle_id=vehicle_record.id, # Link to the Vehicle record
                current_status=LeadStatus(standardized_details.get('current_status_crm', 'NEW').lower()), # Map status
                initial_message=standardized_details.get('initial_message'),
                created_at=standardized_details.get('created_at'),
                updated_at=standardized_details.get('updated_at', datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)),
                # is_converted will be set when status changes to WON/LOST
                # predicted_likelihood will be set by the prediction service
            )
            db.add(lead_record)
            # db.flush() # Not strictly necessary here as we don't need the Lead ID immediately below

        # Commit changes for this lead
        db.commit()
        print(f"  Successfully processed lead {crm_source}/{crm_lead_id}.")

    except IntegrityError as e:
        db.rollback()
        print(f"  Integrity error processing lead {crm_source}/{crm_lead_id}: {e}. Likely duplicate.")
    except Exception as e:
        db.rollback() # Rollback changes on any error
        print(f"  Error processing lead {crm_source}/{crm_lead_id}: {e}")


def run_connector_ingestion(crm_source: str = 'VinSolutions'):
    """
    Runs the ingestion process for a specific CRM connector.
    In a real system, this would track the last fetch time.
    For demo, we'll use a hardcoded time or fetch all (simulated).
    """
    connector = get_connector_instance(crm_source)
    if not connector:
        return

    db = SessionLocal()
    try:
        connector.connect()
        if not connector.connection:
             print(f"Failed to connect to {crm_source}. Aborting ingestion.")
             return

        # --- Determine last fetch time ---
        # In a real system, store and retrieve the last successful fetch time per connector.
        # For this demo, let's fetch leads created/updated in the last 7 days (simulated).
        last_fetch_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - datetime.timedelta(days=7)
        print(f"Starting ingestion for {crm_source} since {last_fetch_time}...")


        # --- Fetch New Leads ---
        new_leads_data = connector.fetch_new_leads(last_fetch_time)
        print(f"Fetched {len(new_leads_data)} potential new/updated leads from {crm_source}.")

        # --- Process and Save Leads ---
        for lead_data in new_leads_data:
            # Fetch additional details if needed and not available in the initial fetch
            # For this demo, the initial fetch is enough to process
            process_and_save_lead(db, lead_data)

    except Exception as e:
        print(f"An error occurred during {crm_source} ingestion: {e}")
        db.rollback() # Rollback any outstanding transactions
    finally:
        if connector:
            connector.disconnect()
        db.close()
        print(f"Ingestion process for {crm_source} finished.")

# Helper function to run ingestion directly from script
def run_ingestion_script():
    """Helper to run ingestion for the demo connector."""
    # In a real system, you'd iterate through configured connectors
    run_connector_ingestion(crm_source='VinSolutions')

if __name__ == '__main__':
    # Example: Run ingestion for VinSolutions when script is executed
    run_ingestion_script()
