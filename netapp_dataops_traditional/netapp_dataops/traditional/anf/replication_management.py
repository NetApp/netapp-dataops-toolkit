"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Replication Management

This module provides replication management operations for Azure NetApp Files.
"""

from typing import Dict, List, Any
from azure.mgmt.netapp.models import AuthorizeRequest
from azure.core.exceptions import ResourceNotFoundError
from .client import get_anf_client
from .base import _serialize, validate_required_params
from .config import _retrieve_anf_config, get_config_value, InvalidConfigError

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

# Constants for validation
VALID_PROTOCOL_TYPES = ["NFSv3", "NFSv4.1", "CIFS"]
VALID_SERVICE_LEVELS = ["Standard", "Premium", "Ultra", "StandardZRS", "Flexible"]
DEFAULT_SERVICE_LEVEL = "Premium"

def create_replication(
    # Source volume parameters
    volume_name: str,
    # Destination volume parameters
    destination_resource_group_name: str,
    destination_account_name: str,
    destination_pool_name: str,
    destination_volume_name: str,
    destination_location: str,
    destination_creation_token: str,
    destination_usage_threshold: int,
    destination_protocol_types: List[str],
    destination_virtual_network_name: str,
    destination_subnet_name: str = "default",
    destination_service_level: str = None,
    destination_zones: List[str] = None,
    # Source volume parameters (optional - will use config defaults)
    resource_group_name: str = None,
    account_name: str = None,
    pool_name: str = None,
    # Common parameters
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a complete cross-region replication setup for Azure NetApp Files.
    
    This function creates a new data protection volume in the destination location
    and sets up replication from the source volume.
    
    Args:
        # Source volume parameters
        volume_name (str):
            Required. Source volume name.
        
        # Destination volume parameters (required - typically in different region/subscription)
        destination_resource_group_name (str):
            Required. Destination resource group name.
        destination_account_name (str):
            Required. Destination NetApp account name. 
        destination_pool_name (str):
            Required. Destination capacity pool name.
        destination_volume_name (str):
            Required. Destination volume name.
        destination_location (str):
            Required. Destination Azure region (must differ from source).
        destination_creation_token (str):
            Required. Destination volume file path. Must be unique within the account.
        destination_usage_threshold (int):
            Required. Destination volume quota in bytes.
            This must be at least as large as the source volume's usage threshold.
        destination_protocol_types (List[str]):
            Required. List of protocol types for destination volume (e.g., ["NFSv4.1"]).
        destination_virtual_network_name (str):
            Required. Destination virtual network name.
        destination_subnet_name (str):
            Optional. Destination subnet name. Defaults to "default".
        destination_service_level (str):
            Optional. Destination service level (Standard/Premium/Ultra).
            Defaults to "Premium".
        destination_zones (List[str]):
            Optional. Availability zones for destination volume. If None, defaults to ["1"].
        
        # Source volume parameters (optional - will use config defaults)
        resource_group_name (str):
            Optional. Source volume resource group name. Will use config default if not provided.
        account_name (str):
            Optional. Source volume NetApp account name. Will use config default if not provided.
        pool_name (str):
            Optional. Source volume capacity pool name. Will use config default if not provided.

        subscription_id (str):
            Optional. Azure subscription ID. Will use config default if not provided.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and replication setup details. The response details 
        are serialized using _serialize() and include status information, source 
        volume details, destination volume details, and replication status.

    Raises:
        InvalidConfigError: If required source volume parameters are missing from both function call and config
        ValueError: If required destination parameters are missing or invalid
        ResourceNotFoundError: If source volume does not exist
        Exception: If there is an error during the replication setup process   
    
    Note:
        - Source and destination volumes must be in different Azure zones or regions
        - Destination volume will be created as a data protection volume
    """
    # Retrieve config details from config file
    try:
        config = _retrieve_anf_config(print_output=print_output)
    except InvalidConfigError:
        raise

    # Resolve source volume parameters from function arguments or config
    try:
        resolved_subscription_id = get_config_value('subscription_id', subscription_id, config, print_output)
        resolved_resource_group_name = get_config_value('resource_group_name', resource_group_name, config, print_output)
        resolved_account_name = get_config_value('account_name', account_name, config, print_output)
        resolved_pool_name = get_config_value('pool_name', pool_name, config, print_output)
    except InvalidConfigError:
        raise

    try:
        # Validate input parameters (using resolved values for source volume)
        validate_required_params(
            resource_group_name=resolved_resource_group_name,
            account_name=resolved_account_name,
            pool_name=resolved_pool_name,
            volume_name=volume_name,
            destination_resource_group_name=destination_resource_group_name,
            destination_account_name=destination_account_name,
            destination_pool_name=destination_pool_name,
            destination_volume_name=destination_volume_name,
            destination_location=destination_location,
            destination_creation_token=destination_creation_token,
            destination_usage_threshold=destination_usage_threshold,
            destination_protocol_types=destination_protocol_types,
            destination_virtual_network_name=destination_virtual_network_name
        )
        
        # Set default service level if not provided
        if destination_service_level is None:
            destination_service_level = DEFAULT_SERVICE_LEVEL
        
        # Validate protocol types
        invalid_protocols = [pt for pt in destination_protocol_types if pt not in VALID_PROTOCOL_TYPES]
        if invalid_protocols:
            error_message = f"Invalid protocol types: {invalid_protocols}. Valid options are: {VALID_PROTOCOL_TYPES}"
            logger.error(error_message)
            if print_output:
                print(error_message)
            return {"status": "error", "details": error_message}
        
        # Validate service level
        if destination_service_level not in VALID_SERVICE_LEVELS:
            error_message = f"Invalid service level: '{destination_service_level}'. Valid options are: {VALID_SERVICE_LEVELS}"
            logger.error(error_message)
            if print_output:
                print(error_message)
            return {"status": "error", "details": error_message}
        
        # Get ANF client and subscription ID (using resolved value)
        client, final_subscription_id = get_anf_client(resolved_subscription_id, print_output=print_output)

        # Construct source volume resource ID (using resolved values)
        source_volume_resource_id = f"/subscriptions/{final_subscription_id}/resourceGroups/{resolved_resource_group_name}/providers/Microsoft.NetApp/netAppAccounts/{resolved_account_name}/capacityPools/{resolved_pool_name}/volumes/{volume_name}"
        
        # Initialize destination volume resource ID
        destination_volume_resource_id = None
        
        # Create destination volume if parameters are provided
        if destination_resource_group_name and destination_account_name and destination_pool_name and destination_volume_name:
            if not all([destination_location, destination_creation_token, destination_virtual_network_name, destination_subnet_name]):
                error_message = "For new destination volume, destination_location, destination_creation_token, destination_virtual_network_name, and destination_subnet_name are required"
                logger.error(error_message)
                if print_output:
                    print(error_message)
                return {"status": "error", "details": error_message}
            
            # Create the data protection volume
            from .volume_management import create_volume
            from azure.mgmt.netapp.models import VolumePropertiesDataProtection, ReplicationObject
            
            # Set default zones if not provided
            if destination_zones is None:
                destination_zones = ["1"]
            
            # Create replication object pointing to the source volume
            replication_object = ReplicationObject(
                replication_id=f"repl-{destination_volume_name}",
                remote_volume_resource_id=source_volume_resource_id
            )
            
            # Create data protection object
            data_protection = VolumePropertiesDataProtection(
                replication=replication_object
            )
            
            # Create the data protection volume
            volume_result = create_volume(
                resource_group_name=destination_resource_group_name,
                account_name=destination_account_name,
                pool_name=destination_pool_name,
                volume_name=destination_volume_name,
                location=destination_location,
                creation_token=destination_creation_token,
                virtual_network_name=destination_virtual_network_name,
                subnet_name=destination_subnet_name,
                usage_threshold=destination_usage_threshold,
                protocol_types=destination_protocol_types,
                service_level=destination_service_level,
                volume_type="DataProtection",
                zones=destination_zones,
                data_protection=data_protection,
                subscription_id=final_subscription_id
            )
            
            if volume_result.get('status') != 'success':
                error_message = f"Failed to create destination volume: {volume_result.get('details', 'Unknown error')}"
                logger.error(error_message)
                if print_output:
                    print(error_message)
                return {"status": "error", "details": error_message}
            
            # Construct destination volume resource ID
            destination_volume_resource_id = f"/subscriptions/{final_subscription_id}/resourceGroups/{destination_resource_group_name}/providers/Microsoft.NetApp/netAppAccounts/{destination_account_name}/capacityPools/{destination_pool_name}/volumes/{destination_volume_name}"
        
        # Ensure destination volume resource ID is set
        if not destination_volume_resource_id:
            error_message = "Destination volume resource ID could not be determined"
            logger.error(error_message)
            if print_output:
                print(error_message)
            return {"status": "error", "details": error_message}
        
        
        # Validate that source and destination are not the same
        if destination_volume_resource_id and destination_volume_resource_id.lower() == source_volume_resource_id.lower():
            error_message = "A volume cannot be authorized for replication against itself"
            logger.error(error_message)
            if print_output:
                print(error_message)
            return {"status": "error", "details": error_message}
        
        # Create the authorize request object
        authorize_request = AuthorizeRequest(
            remote_volume_resource_id=destination_volume_resource_id
        )
        
        # Authorize replication on source volume (using resolved values)
        poller = client.volumes.begin_authorize_replication(
            resource_group_name=resolved_resource_group_name,
            account_name=resolved_account_name,
            pool_name=resolved_pool_name,
            volume_name=volume_name,
            body=authorize_request
        )
        
        # Wait for completion
        poller.result()
        
        # # Prepare success response
        replication_details = {
            "source_volume": {
                "resource_id": source_volume_resource_id,
                "name": volume_name
            },
            "destination_volume": {
                "resource_id": destination_volume_resource_id
            },
            "replication_status": "authorized",
            "message": f"Replication setup completed successfully for volume '{volume_name}'"
        }
        
        # Add destination volume creation info if we created it
        if destination_resource_group_name:
            replication_details["destination_volume"]["created"] = True
            replication_details["destination_volume"]["name"] = destination_volume_name
            replication_details["destination_volume"]["location"] = destination_location
        else:
            replication_details["destination_volume"]["created"] = False
        
        return {"status": "success", "details": _serialize(replication_details)}

    except InvalidConfigError:
        raise
    except ResourceNotFoundError as e:
        error_message = f"Volume '{volume_name}' not found: {str(e)}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": error_message}
    except Exception as e:
        error_message = str(e)
        
        # Provide specific guidance for common replication errors
        if "cannot be authorized for replication against itself" in error_message.lower():
            error_details = f"Replication authorization failed: A volume cannot replicate to itself. Please create a data protection volume in a different Azure region. Original error: {error_message}"
        elif "data protection volume" in error_message.lower():
            error_details = f"Replication authorization failed: The destination volume must be a data protection volume. Create the destination volume with volume_type='DataProtection' in a different region. Original error: {error_message}"
        elif "different region" in error_message.lower():
            error_details = f"Replication authorization failed: Source and destination volumes must be in different Azure regions. Original error: {error_message}"
        else:
            error_details = f"Failed to setup replication: {error_message}"

        logger.error(error_details)
        if print_output:
            print(error_details)
        return {"status": "error", "details": error_details}
