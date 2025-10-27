"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Snapshot Management

This module provides snapshot management operations for Azure NetApp Files.
"""

from typing import Dict, Optional, Any
from azure.mgmt.netapp.models import Snapshot
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from .client import get_anf_client
from .base import _serialize, validate_required_params

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

def create_snapshot(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    snapshot_name: str,
    location: str,
    tags: dict = None,
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a new snapshot for an Azure NetApp Files volume.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account
        pool_name (str):
            Required. The name of the capacity pool.
        volume_name (str):
            Required. The name of the volume.
        snapshot_name (str):
            Required. The name of the snapshot.
        location (str):
            Required. Azure region
        tags (Dict[str, str]):
            Optional. Resource tags.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and snapshot details

    Raises:
        ResourceExistsError: If the snapshot already exists
        ResourceNotFoundError: If the volume does not exist
        Exception: For other errors during snapshot creation
    """

    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name,
        volume_name=volume_name,
        snapshot_name=snapshot_name,
        location=location
    )

    try:
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # Build snapshot properties
        snapshot_properties = {
            'location': location
        }
        
        # Add optional parameters if provided
        if tags:
            snapshot_properties['tags'] = tags
        
        # Create the snapshot object
        snapshot = Snapshot(**snapshot_properties)
        
        # Create the snapshot
        poller = client.snapshots.begin_create(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            snapshot_name=snapshot_name,
            body=snapshot
        )

        if print_output:
            logger.info("Creating snapshot...")
        
        # Wait for completion and get result
        result = poller.result()

        if print_output:
            logger.info(f"Snapshot '{snapshot_name}' created successfully")

        return {"status": "success", "details": _serialize(result)}
        
    except ResourceExistsError as e:
        if print_output:
            logger.error(f"Snapshot '{snapshot_name}' already exists: {str(e)}")
        return {"status": "error", "details": str(e)}
    except ResourceNotFoundError as e:
        if print_output:
            logger.error(f"Source volume '{volume_name}' not found: {str(e)}")
        return {"status": "error", "details": str(e)}
    except Exception as e:
        if print_output:
            logger.error(f"Failed to create snapshot: {str(e)}")
        return {"status": "error", "details": str(e)}


def delete_snapshot(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    snapshot_name: str,
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Delete an existing snapshot for an Azure NetApp Files volume.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool.
        volume_name (str):
            Required. The name of the volume.
        snapshot_name (str):
            Required. The name of the snapshot.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and operation details

    Raises:
        ResourceNotFoundError: If the snapshot does not exist
        Exception: For other errors during snapshot deletion
    """

    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name,
        volume_name=volume_name,
        snapshot_name=snapshot_name
    )

    try:
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # Delete the snapshot
        poller = client.snapshots.begin_delete(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            snapshot_name=snapshot_name
        )

        if print_output:
            logger.info("Deleting snapshot...")
        
        # Wait for completion
        poller.result()

        if print_output:
            logger.info(f"Snapshot '{snapshot_name}' deleted successfully")

        return {"status": "success", "details": f"Snapshot '{snapshot_name}' deleted successfully"}

    except ResourceNotFoundError:
        if print_output:
            logger.error(f"Snapshot '{snapshot_name}' not found")
        return {"status": "error", "details": str(e)}
    except Exception as e:
        if print_output:
            logger.error(f"Failed to delete snapshot: {str(e)}")
        return {"status": "error", "details": str(e)}


def list_snapshots(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    List all snapshots for an Azure NetApp Files volume.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool.
        volume_name (str):
            Required. The name of the volume.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and list of snapshots.

    Raises:
        ResourceNotFoundError: If the volume does not exist.
        Exception: For other errors during snapshot listing.
    """

    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name,
        volume_name=volume_name
    )

    try:
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # List all snapshots for the volume
        snapshots = client.snapshots.list(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name
        )

        if print_output:
            logger.info("Listing snapshots...")
        
        # Convert to list and serialize (since it returns an iterator)
        snapshot_list = list(snapshots)
        
        # Serialize the Azure SDK Snapshot objects to dictionaries
        serialized_snapshots = [_serialize(snapshot) for snapshot in snapshot_list]

        if print_output:
            logger.info(f"Number of snapshots fetched: {len(serialized_snapshots)}")
            logger.info(f"Snapshots fetched:\n{serialized_snapshots}")

        return {"status": "success", "details": serialized_snapshots}

    except ResourceNotFoundError as e:
        if print_output:
            logger.error(f"Volume '{volume_name}' not found")
        return {"status": "error", "details": str(e)}
    except Exception as e:
        if print_output:
            logger.error(f"Failed to list snapshots: {str(e)}")
        return {"status": "error", "details": str(e)}
        