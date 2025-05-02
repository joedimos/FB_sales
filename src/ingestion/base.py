import abc

class BaseCRMConnector(abc.ABC):
    def __init__(self, config):
        self.config = config
        self.connection = None

    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def fetch_new_leads(self, last_fetch_time):
        # Returns list of standardized lead dicts
        pass

    @abc.abstractmethod
    def fetch_lead_details(self, lead_id):
         # Returns standardized lead details dict
         pass

    @abc.abstractmethod
    def fetch_vehicle_details(self, vehicle_id):
         # Returns standardized vehicle details dict
         pass

# src/ingestion/vinsolutions_connector.py
from .base import BaseCRMConnector
import requests
# Potentially Pydantic models for standardization

class VinSolutionsConnector(BaseCRMConnector):
    def connect(self):
        # Use self.config to get API keys, endpoints
        # Authenticate with VinSolutions API
        print("Connecting to VinSolutions...")
        self.connection = "VinSolutions API Session" # Placeholder

    def fetch_new_leads(self, last_fetch_time):
        # Implement VinSolutions API call to get leads since last_fetch_time
        # Example:
        api_url = self.config['api_url'] + '/leads'
        params = {'created_since': last_fetch_time.isoformat()}
        headers = {'Authorization': f'Bearer {self.config["api_key"]}'}
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        raw_leads = response.json()['leads']

        standardized_leads = []
        for raw_lead in raw_leads:
            # Map raw_lead fields to your standard format
            standardized_lead = {
                'lead_id': raw_lead.get('id'),
                'crm_source': 'VinSolutions',
                'created_at': raw_lead.get('createdAt'),
                'status': raw_lead.get('status'),
                'vehicle_id': raw_lead.get('vehicleId'), # Need to fetch details separately
                'customer_id': raw_lead.get('customerId'),
                'initial_message': raw_lead.get('initialMessage'), # From FBMP
                # ... other relevant fields
            }
            standardized_leads.append(standardized_lead)
        return standardized_leads
