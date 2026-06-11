"""EE Usage limits - trial detection."""

from onyx.utils.logger import setup_logger
from shared_configs.configs import MULTI_TENANT

logger = setup_logger()


def is_tenant_on_trial(tenant_id: str) -> bool:
    """
    Determine if a tenant is currently on a trial subscription.
    """
    return False
