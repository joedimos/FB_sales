# src/crm_writeback/writeback_manager.py
from .crm_apis.cdk_api import CdkWritebackAPI
from .crm_apis.vinsolutions_api import VinSolutionsWritebackAPI
# ... import others

def writeback_score_to_crm(crm_source: str, crm_lead_id: str, score: float):
    """Routes the writeback call to the correct CRM API."""
    if crm_source == 'CDK':
        api = CdkWritebackAPI() # Needs config
        api.update_lead_score(crm_lead_id, score)
    elif crm_source == 'VinSolutions':
        api = VinSolutionsWritebackAPI() # Needs config
        api.update_lead_score(crm_lead_id, score)
    # Add elif for other CRMs
    else:
        print(f"Warning: No writeback API configured for CRM source: {crm_source}")

# Example src/crm_writeback/crm_apis/vinsolutions_api.py
# import requests
# class VinSolutionsWritebackAPI:
#    def update_lead_score(self, lead_id, score):
#        # Call VinSolutions API to update lead field
#        print(f"Writing back score {score} to VinSolutions lead {lead_id}")
#        pass # Implementation using requests
