import abc
from typing import List, Dict, Any
import datetime

class BaseCRMConnector(abc.ABC):
    """Abstract base class for all CRM connectors."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None # Placeholder for connection object if needed

    @abc.abstractmethod
    def connect(self):
        """Establishes connection to the CRM API/DB."""
        pass

    @abc.abstractmethod
    def disconnect(self):
        """Closes connection."""
        pass

    @abc.abstractmethod
    def fetch_new_leads(self, last_fetch_time: datetime.datetime) -> List[Dict[str, Any]]:
        """
        Fetches leads created or updated since last_fetch_time.
        Returns a list of dictionaries in a standardized format.
        """
        pass

    @abc.abstractmethod
    def fetch_lead_details(self, lead_id: str) -> Dict[str, Any]:
         """Fetches detailed information for a specific lead ID."""
         pass

    @abc.abstractmethod
    def fetch_vehicle_details(self, vehicle_id: str) -> Dict[str, Any]:
         """Fetches detailed information for a specific vehicle ID."""
         pass

    # Add methods for fetching interaction history, customer data, etc.
    # @abc.abstractmethod
    # def fetch_lead_interactions(self, lead_id: str) -> List[Dict[str, Any]]:
    #      pass
