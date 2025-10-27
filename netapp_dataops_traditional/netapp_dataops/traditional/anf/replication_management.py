"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Replication Management

This module provides replication management operations for Azure NetApp Files.
"""

from typing import Dict, Optional, Any
from azure.mgmt.netapp.models import AuthorizeRequest
from azure.core.exceptions import ResourceNotFoundError
from .client import get_anf_client
from .base import _serialize, validate_required_params

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

def create_replication(
    # Source volume parameters
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    # Destination volume parameters (optional - if not provided, will use remote_volume_resource_id)
    destination_resource_group_name: str = None,
    destination_account_name: str = None,
    destination_pool_name: str = None,
    destination_volume_name: str = None,
    destination_location: str = None,
    destination_creation_token: str = None,
    destination_usage_threshold: int = None,
    destination_protocol_types: list = None,
    destination_virtual_network_name: str = None,
    destination_subnet_name: str = "default",
    destination_zones: list = None,
    destination_service_level: str = None,
    # For existing destination volume
    remote_volume_resource_id: str = None,
    # Common parameters
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a complete cross-region replication setup for Azure NetApp Files.
    
    This function can either:
    1. Create a new data protection volume and authorize replication (provide destination_* parameters)
    2. Authorize replication to an existing data protection volume (provide remote_volume_resource_id)
    
    Args:
        # Source volume parameters (required)
        resource_group_name (str):
            Required. Source volume resource group name.
        account_name (str):
            Required. Source volume NetApp account name.
        pool_name (str):
            Required. Source volume capacity pool name.
        volume_name (str):
            Required. Source volume name.

        # For creating new destination volume:
        destination_resource_group_name (str):
            Required. Destination resource group name.
        destination_account_name (str):
            Optional. Destination NetApp account name. 
        destination_pool_name (str):
            Optional. Destination capacity pool name.
        destination_volume_name (str):
            Optional. Destination volume name.
        destination_location (str):
            Optional. Destination Azure region (must differ from source).
        destination_creation_token (str):
            Optional. Destination volume file path. Must be unique within the account.
        destination_virtual_network_name (str):
            Optional. Destination virtual network name.
        destination_subnet_name (str):
            Optional. Destination subnet name.
            Defaults to "default".
        destination_zones (list):
            Optional. Availability zones for destination volume.
        destination_usage_threshold (int):
            Optional. Destination volume quota in bytes (default: 100 GiB).
        destination_service_level (str):
            Optional. Destination service level (Standard/Premium/Ultra).
            Defaults to "Premium".

        # For existing destination volume:
        remote_volume_resource_id (str):
            Required. Resource ID of existing data protection volume

        subscription_id (str):
            Optional. Azure subscription ID
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and replication setup details

    Raises:
        ValueError: If required parameters are missing or invalid
        ResourceNotFoundError: If source volume does not exist
        Exception: If there is an error during the replication setup process   
    
    Note:
        - Must provide either destination_* parameters OR remote_volume_resource_id
        - Source and destination volumes must be in different Azure regions
        - Destination volume will be created as a data protection volume if creating new
    """
    try:
        # Validate that either destination parameters or remote_volume_resource_id is provided
        has_destination_params = all([
            destination_resource_group_name,
            destination_account_name, 
            destination_pool_name,
            destination_volume_name,
            destination_location,
            destination_creation_token,
            destination_virtual_network_name,
            destination_subnet_name
        ])
        
        has_remote_resource_id = bool(remote_volume_resource_id)
        
        if not has_destination_params and not has_remote_resource_id:
            if print_output:
                logger.error("Must provide either all destination volume parameters (destination_resource_group_name, destination_account_name, destination_pool_name, destination_volume_name, destination_location, destination_creation_token, destination_subnet_id) OR remote_volume_resource_id for existing volume")
            return {
                "status": "error", 
                "details": "Must provide either all destination volume parameters (destination_resource_group_name, destination_account_name, destination_pool_name, destination_volume_name, destination_location, destination_creation_token, destination_subnet_id) OR remote_volume_resource_id for existing volume"
            }
        
        if has_destination_params and has_remote_resource_id:
            if print_output:
                logger.error("Cannot provide both destination volume parameters and remote_volume_resource_id. Choose one: create new destination volume OR use existing volume")
            return {
                "status": "error",
                "details": "Cannot provide both destination volume parameters and remote_volume_resource_id. Choose one: create new destination volume OR use existing volume"
            }
        
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # Construct source volume resource ID
        source_volume_resource_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.NetApp/netAppAccounts/{account_name}/capacityPools/{pool_name}/volumes/{volume_name}"
        
        destination_volume_resource_id = remote_volume_resource_id
        
        # Create destination volume if parameters are provided
        if destination_resource_group_name and destination_account_name and destination_pool_name and destination_volume_name:
            if not all([destination_location, destination_creation_token, destination_virtual_network_name, destination_subnet_name]):
                if print_output:
                    logger.error("For new destination volume, destination_location, destination_creation_token, and destination_subnet_id are required")
                return {"status": "error", "details": "For new destination volume, destination_location, destination_creation_token, and destination_subnet_id are required"}
            
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
                subscription_id=subscription_id
            )
            
            if volume_result.get('status') != 'success':
                if print_output:
                    logger.error(f"Failed to create destination volume: {volume_result.get('details', 'Unknown error')}")
                return {"status": "error", "details": f"Failed to create destination volume: {volume_result.get('details', 'Unknown error')}"}
            
            # Construct destination volume resource ID
            destination_volume_resource_id = f"/subscriptions/{subscription_id}/resourceGroups/{destination_resource_group_name}/providers/Microsoft.NetApp/netAppAccounts/{destination_account_name}/capacityPools/{destination_pool_name}/volumes/{destination_volume_name}"
        
        elif not remote_volume_resource_id:
            if print_output:
                logger.error("Must provide either destination volume parameters to create new volume, or remote_volume_resource_id for existing volume")
            return {"status": "error", "details": "Must provide either destination volume parameters to create new volume, or remote_volume_resource_id for existing volume"}
        
        # Validate that source and destination are not the same
        if destination_volume_resource_id and destination_volume_resource_id.lower() == source_volume_resource_id.lower():
            if print_output:
                logger.error("A volume cannot be authorized for replication against itself")
            return {"status": "error", "details": "A volume cannot be authorized for replication against itself"}
        
        # Create the authorize request object
        authorize_request = AuthorizeRequest(
            remote_volume_resource_id=destination_volume_resource_id
        )
        
        # Authorize replication on source volume
        poller = client.volumes.begin_authorize_replication(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
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

    except ResourceNotFoundError as e:
        if print_output:
            logger.error(f"Volume '{volume_name}' not found: {str(e)}")
        return {"status": "error", "details": f"Volume '{volume_name}' not found: {str(e)}"}
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

        if print_output:
            logger.error(error_details)
        return {"status": "error", "details": error_details}


def create_data_protection_volume(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    location: str,
    creation_token: str,
    usage_threshold: int,
    protocol_types: list,
    virtual_network_name: str,
    subnet_name: str,
    source_volume_resource_id: str,
    zones: list = None,
    service_level: str = None,
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a data protection volume for use as a replication destination.
    
    This is a convenience function to create a destination volume specifically
    for cross-region replication. The volume will be created with volume_type="DataProtection".
    
    Args:
        resource_group_name (str):
            Required. The name of the destination resource group.
        account_name (str):
            Required. The name of the destination NetApp account.
        pool_name (str):
            Required. The name of the destination capacity pool.
        volume_name (str):
            Required. The name of the destination volume.
        location (str):
            Required. Azure region for the destination (must be different from source).
        creation_token (str):
            Required. Unique file path for the destination volume.
        virtual_network_name (str):
            Required. The name of the virtual network to which the volume will be connected.
        subnet_name (str):
            Optional. The name of a delegated Azure subnet to construct the Azure Resource ID for a delegated subnet.
            If not provided, the default subnet will be used.
        source_volume_resource_id (str):
            Required. The resource ID of the source volume to replicate from.
        zones (list):
            Required. List of availability zones for cross-zone replication (e.g., ["1"] or ["1", "2", "3"]).
        usage_threshold (int):
            Required. Volume quota in bytes (default: 100 GiB).
        service_level (str):
            Required. Service level (Standard, Premium, Ultra).
        subscription_id (str):
            Required. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and volume creation details

    Raises:
        ValueError: If required parameters are missing or invalid
        ResourceNotFoundError: If the source volume does not exist
        Exception: If there is an error during volume creation
        
    Note:
        - For cross-zone replication, zones parameter is required
        - After creating this volume, use its resource ID as the remote_volume_resource_id
          parameter in the create_replication function on the source volume
        - Common zone values: ["1"], ["2"], ["3"], or ["1", "2", "3"] for zone redundancy
    """

    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name,
        volume_name=volume_name,
        location=location,
        creation_token=creation_token,
        virtual_network_name=virtual_network_name,
        source_volume_resource_id=source_volume_resource_id
    )

    try:
        # Import volume management functions
        from .volume_management import create_volume
        from azure.mgmt.netapp.models import VolumePropertiesDataProtection, ReplicationObject

        # Set default zones if not provided (required for cross-zone replication)
        if zones is None:
            zones = ["1"]  # Default to zone 1
            print("INFO: No zones specified, defaulting to zone 1 for data protection volume")
        
        # Create replication object pointing to the source volume
        replication_object = ReplicationObject(
            replication_id=f"repl-{volume_name}",
            remote_volume_resource_id=source_volume_resource_id
        )
        
        # Create data protection object
        data_protection = VolumePropertiesDataProtection(
            replication=replication_object
        )
        
        # Create the data protection volume using the volume management function
        result = create_volume(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            location=location,
            creation_token=creation_token,
            virtual_network_name=virtual_network_name,
            subnet_name=subnet_name,
            usage_threshold=usage_threshold,
            protocol_types=protocol_types,
            service_level=service_level,
            volume_type="DataProtection",
            zones=zones,  # Include zones for cross-zone replication
            data_protection=data_protection,
            subscription_id=subscription_id,
            print_output=print_output
        )
        
        if result.get('status') == 'success':
            # Add replication-specific information to the response
            result['details']['replication_info'] = {
                "volume_type": "DataProtection",
                "source_volume_resource_id": source_volume_resource_id,
                "replication_id": f"repl-{volume_name}",
                "next_steps": [
                    "Wait for the data protection volume to be created",
                    f"Use this volume's resource ID in create_replication() on the source volume"
                ]
            }
        
        return result
        
    except Exception as e:
        if print_output:
            logger.error(f"Failed to create data protection volume: {str(e)}")
        return {"status": "error", "details": f"Failed to create data protection volume: {str(e)}"}
    