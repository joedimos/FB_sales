from src.config import settings
from .crm_apis.vinsolutions_api import VinSolutionsWritebackAPI

CRM_WRITEBACK_APIS = {
    "VinSolutions": VinSolutionsWritebackAPI,
}


def writeback_score_to_crm(crm_source: str, crm_lead_id: str, score: float):
    """Write a score back only when CRM writeback is explicitly enabled."""
    crm_config = settings.get("crm", {})
    if not crm_config.get("writeback_enabled", False):
        return False

    api_class = CRM_WRITEBACK_APIS.get(crm_source)
    if api_class is None:
        return False

    api_instance = api_class()
    api_instance.update_lead_score(crm_lead_id, score)
    return True
