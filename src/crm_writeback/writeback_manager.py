from .crm_apis.vinsolutions_api import VinSolutionsWritebackAPI
from .crm_apis.cdk_api import CdkWritebackAPI # Import placeholders
from .crm_apis.reynolds_api import ReynoldsWritebackAPI

# Map CRM source strings to their respective writeback API classes
CRM_WRITEBACK_APIS = {
    'VinSolutions': VinSolutionsWritebackAPI,
    'CDK': CdkWritebackAPI,
    'Reynolds': ReynoldsWritebackAPI,
    # Add other CRMs here
}

def writeback_score_to_crm(crm_source: str, crm_lead_id: str, score: float):
    """
    Routes the writeback call to the correct CRM API based on source.
    """
    api_class = CRM_WRITEBACK_APIS.get(crm_source)

    if api_class:
        try:
            api_instance = api_class()
            api_instance.update_lead_score(crm_lead_id, score)
        except Exception as e:
            print(f"Error initializing or calling writeback API for {crm_source}: {e}")
            # Log the error but don't necessarily re-raise
    else:
        print(f"Warning: No writeback API configured for CRM source: {crm_source}")
