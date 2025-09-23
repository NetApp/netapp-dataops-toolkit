from google.cloud import netapp_v1
from google.protobuf.json_format import MessageToDict
from typing import Dict, List, Any, Union
import logging

logger = logging.getLogger(__name__)


def _serialize(details) -> Union[Dict[str, Any], List[Any], str, int, float, bool, None]:
    """Internal helper to convert protobuf objects (and lists) to JSON-serializable structures."""
    if hasattr(details, '_pb'):
        return MessageToDict(details._pb)
    if isinstance(details, list):
        return [_serialize(item) for item in details]
    if isinstance(details, (dict, str, int, float, bool)) or details is None:
        return details
    # Fallback to string representation
    return str(details)


def create_client() -> netapp_v1.NetAppClient:
    """Create and return a NetApp client.
    
    Returns:
        netapp_v1.NetAppClient: The NetApp client instance.
        
    Raises:
        Exception: If there is an error while creating the NetApp client.
    """
    try:
        return netapp_v1.NetAppClient()
    except Exception as e:
        logger.error(f"An error occurred while creating the NetApp client: {e}")
        raise e


def validate_required_params(**params) -> None:
    """Validate that all required parameters are provided.
    
    Args:
        **params: Dictionary of parameter names and values to validate.
        
    Raises:
        ValueError: If any required parameter is missing or empty.
    """
    missing_params = [name for name, value in params.items() if value is None or (isinstance(value, str) and value == "")]
    if missing_params:
        param_list = ", ".join(missing_params)
        raise ValueError(f"The following required parameters are missing: {param_list}")
