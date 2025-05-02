import datetime
import time
import random
from typing import List, Dict, Any
import uuid # To generate dummy lead IDs
from .base import BaseCRMConnector
from src.config import settings

class VinSolutionsConnector(BaseCRMConnector):
    """Simulated connector for VinSolutions CRM."""
    def __init__(self, config: Dict[str, Any] = settings.get("vinsolutions")):
        super().__init__(config)
        self.crm_source_name = "VinSolutions"
        print(f"Initialized {self.crm_source_name} Connector")

    def connect(self):
        """Simulate connecting to VinSolutions API."""
        if not self.config or not self.config.get("api_url") or not self.config.get("api_key"):
             print(f"Warning: {self.crm_source_name} config missing or incomplete. Connection simulated.")
             self.connection = "simulated_connected"
             return

        print(f"Connecting to {self.crm_source_name} API...")
        # In a real connector, you'd authenticate here
        # try:
        #    self.session = requests.Session()
        #    self.session.headers.update({'Authorization': f'Bearer {self.config["api_key"]}'})
        #    # Optional: Make a small test call to verify connection
        #    response = self.session.get(f'{self.config["api_url"]}/test_endpoint', timeout=5)
        #    response.raise_for_status()
        #    self.connection = self.session
        #    print(f"Successfully connected to {self.crm_source_name}.")
        # except Exception as e:
        #    print(f"Failed to connect to {self.crm_source_name}: {e}")
        #    self.connection = None

        # --- Simulation ---
        self.connection = "simulated_connected"
        print(f"Simulated connection to {self.crm_source_name}.")
        time.sleep(0.5) # Simulate network latency


    def disconnect(self):
        """Simulate disconnecting."""
        if self.connection:
            print(f"Simulating disconnection from {self.crm_source_name}.")
            # if isinstance(self.connection, requests.Session): self.connection.close()
            self.connection = None
            time.sleep(0.1)


    def fetch_new_leads(self, last_fetch_time: datetime.datetime) -> List[Dict[str, Any]]:
        """Simulate fetching leads created/updated since last_fetch_time."""
        if not self.connection:
            print(f"Not connected to {self.crm_source_name}. Skipping fetch.")
            return []

        print(f"Simulating fetching new leads from {self.crm_source_name} since {last_fetch_time}...")
        time.sleep(1) # Simulate API call time

        # --- Simulate fetching data ---
        # Generate a few dummy leads each time
        num_new_leads = random.randint(0, 5)
        leads_data = []
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

        for i in range(num_new_leads):
            lead_id = str(uuid.uuid4()) # Unique ID for this dummy lead
            created_at = now - datetime.timedelta(minutes=random.randint(1, 60*24*2)) # Within last 2 days
            updated_at = created_at + datetime.timedelta(minutes=random.randint(1, 120)) # Updated shortly after creation

            # Simulate fetching basic data often included in lead lists
            raw_lead_data = {
                "id": lead_id,
                "source": "Facebook", # CRM field indicating FBMP
                "status": random.choice(["New", "Contacted", "Open"]),
                "createdAt": created_at.isoformat(),
                "updatedAt": updated_at.isoformat(),
                "customer": {"name": f"Customer {lead_id[:4]}"},
                "vehicle_interest": {"id": random.randint(100, 999), "make": random.choice(["Toyota", "Honda", "Ford"]), "model": random.choice(["Camry", "Civic", "F-150"])},
                "initial_message": random.choice([
                    "Is this still available?",
                    "Tell me about pricing options.",
                    "What's the lowest you'll go?",
                    "Interested, can I see it today?",
                    "Do you offer financing?",
                    "Looking to trade my car."
                ])
            }

            # --- Standardize Data Format ---
            standardized_lead = {
                'crm_lead_id': str(raw_lead_data['id']), # Ensure string type
                'crm_source': self.crm_source_name,
                'raw_data': raw_lead_data, # Store raw data just in case
                'standardized_data': { # Standardize key fields
                    'created_at': datetime.datetime.fromisoformat(raw_lead_data['createdAt']).replace(tzinfo=datetime.timezone.utc),
                    'updated_at': datetime.datetime.fromisoformat(raw_lead_data['updatedAt']).replace(tzinfo=datetime.timezone.utc),
                    'current_status_crm': raw_lead_data['status'], # Store raw status string
                    'initial_message': raw_lead_data.get('initial_message'),
                    'vehicle_interest_id': raw_lead_data['vehicle_interest']['id'],
                    # Add other common fields
                }
            }
            leads_data.append(standardized_lead)

        print(f"Simulated fetched {len(leads_data)} new leads from {self.crm_source_name}.")
        return leads_data

    def fetch_lead_details(self, lead_id: str) -> Dict[str, Any]:
        """Simulate fetching detailed lead information."""
        if not self.connection:
            print(f"Not connected to {self.crm_source_name}. Skipping lead detail fetch.")
            return {}

        print(f"Simulating fetching details for lead {lead_id} from {self.crm_source_name}...")
        time.sleep(0.5) # Simulate API call time

        # --- Simulate fetching data ---
        # In a real scenario, this would call a specific CRM API endpoint for a single lead ID
        # Return more detailed data than fetch_new_leads provides
        details = {
            "id": lead_id,
            "full_customer_info": {"address": "123 Main St", "phone": "555-1234"},
            "assigned_salesperson_id": random.randint(10, 50),
            # ... add other detailed fields
        }
        return details

    def fetch_vehicle_details(self, vehicle_id: str) -> Dict[str, Any]:
        """Simulate fetching detailed vehicle information."""
        if not self.connection:
            print(f"Not connected to {self.crm_source_name}. Skipping vehicle detail fetch.")
            return {}

        print(f"Simulating fetching details for vehicle {vehicle_id} from {self.crm_source_name}...")
        time.sleep(0.3) # Simulate API call time

        # --- Simulate fetching data ---
        # This would call a specific CRM API endpoint for a single vehicle ID or VIN
        # For simplicity, return dummy vehicle data based on the dummy ID
        price = random.randint(5000, 80000)
        mileage = random.randint(1000, 200000)
        make = random.choice(['Toyota', 'Honda', 'Ford', 'Chevrolet', 'BMW', 'Mercedes', 'Other'])
        year = random.randint(2010, 2023)
        days_on_lot = random.randint(5, 180) # Simulate days on lot

        details = {
             "id": vehicle_id,
             "vin": f"VIN{vehicle_id}{random.randint(1000,9999)}", # Dummy VIN
             "make": make,
             "model": random.choice(["Sedan", "SUV", "Truck", "Coupe"]), # Simplified model
             "year": year,
             "price": float(price),
             "mileage": float(mileage),
             "condition": random.choice(["New", "Used", "Certified"]),
             "days_on_lot": days_on_lot,
             # ... add other detailed fields like transmission, fuel type etc.
        }
        return details

    # Add fetch_lead_interactions etc. similarly


# Placeholder for other CRM connectors
class CdkConnector(BaseCRMConnector):
    def __init__(self, config: Dict[str, Any] = settings.get("cdk")):
        super().__init__(config)
        self.crm_source_name = "CDK"
        print(f"Initialized {self.crm_source_name} Connector (Simulated)")

    def connect(self):
        print(f"Simulating connection to {self.crm_source_name}...")
        self.connection = "simulated_connected"
        time.sleep(0.5)

    def disconnect(self):
         print(f"Simulating disconnection from {self.crm_source_name}.")
         self.connection = None
         time.sleep(0.1)

    def fetch_new_leads(self, last_fetch_time: datetime.datetime) -> List[Dict[str, Any]]:
         print(f"Simulating fetching new leads from {self.crm_source_name} since {last_fetch_time}...")
         time.sleep(1.2)
         # Simulate fetching a few leads in CDK format and standardizing
         return [] # No leads for demo

    def fetch_lead_details(self, lead_id: str) -> Dict[str, Any]:
         print(f"Simulating fetching details for lead {lead_id} from {self.crm_source_name}...")
         time.sleep(0.6)
         return {} # No details for demo

    def fetch_vehicle_details(self, vehicle_id: str) -> Dict[str, Any]:
         print(f"Simulating fetching details for vehicle {vehicle_id} from {self.crm_source_name}...")
         time.sleep(0.4)
         return {} # No details for demo


class ReynoldsConnector(BaseCRMConnector):
    def __init__(self, config: Dict[str, Any] = settings.get("reynolds")):
        super().__init__(config)
        self.crm_source_name = "Reynolds"
        print(f"Initialized {self.crm_source_name} Connector (Simulated)")

    def connect(self):
        print(f"Simulating connection to {self.crm_source_name}...")
        self.connection = "simulated_connected"
        time.sleep(0.7)

    def disconnect(self):
         print(f"Simulating disconnection from {self.crm_source_name}.")
         self.connection = None
         time.sleep(0.2)

    def fetch_new_leads(self, last_fetch_time: datetime.datetime) -> List[Dict[str, Any]]:
         print(f"Simulating fetching new leads from {self.crm_source_name} since {last_fetch_time}...")
         time.sleep(1.5)
         return [] # No leads for demo

    def fetch_lead_details(self, lead_id: str) -> Dict[str, Any]:
         print(f"Simulating fetching details for lead {lead_id} from {self.crm_source_name}...")
         time.sleep(0.7)
         return {} # No details for demo

    def fetch_vehicle_details(self, vehicle_id: str) -> Dict[str, Any]:
         print(f"Simulating fetching details for vehicle {vehicle_id} from {self.crm_source_name}...")
         time.sleep(0.5)
         return {} # No details for demo


# Map CRM source strings to their connector classes
CRM_CONNECTORS = {
    'VinSolutions': VinSolutionsConnector,
    'CDK': CdkConnector,
    'Reynolds': ReynoldsConnector,
    # Add other CRM connectors here
}
