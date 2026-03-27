"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Snapshot Management

This module provides snapshot management operations for Azure NetApp Files.
"""

from typing import Dict, Any
from azure.mgmt.netapp.models import Snapshot
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from .client import get_anf_client
from .base import _serialize, _validate_required_params, _get_clean_error_message
from .config import _retrieve_anf_config, _get_config_value, InvalidConfigError

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)


def create_snapshot(
    snapshot_name: str,
    volume_name: str,
    resource_group_name: str = None,
    account_name: str = None,
    pool_name: str = None,
    location: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a new snapshot for an Azure NetApp Files volume.
    
    Args:
        snapshot_name (str):
            Required. The name of the snapshot.
        volume_name (str):
            Required. The name of the volume to snapshot.
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        location (str):
            Optional. Azure region. Will use config default if not provided.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:    Returns:
        Dictionary with status and snapshot details

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        ResourceExistsError: If the snapshot already exists
        ResourceNotFoundError: If the volume does not exist
        Exception: For other errors during snapshot creation
    """

    # Retrieve config details from config file
    try:
        config = _retrieve_anf_config(print_output=print_output)
    except InvalidConfigError:
        raise

    # Resolve parameters from function arguments or config
    try:
        resolved_resource_group_name = _get_config_value('resource_group_name', resource_group_name, config, print_output)
        resolved_account_name = _get_config_value('account_name', account_name, config, print_output)
        resolved_pool_name = _get_config_value('pool_name', pool_name, config, print_output)
        resolved_location = _get_config_value('location', location, config, print_output)
    except InvalidConfigError:
        raise

    # Validate input parameters (now using resolved values)
    _validate_required_params(
        resource_group_name=resolved_resource_group_name,
        account_name=resolved_account_name,
        pool_name=resolved_pool_name,
        volume_name=volume_name,
        snapshot_name=snapshot_name,
        location=resolved_location
    )

    try:
        # Get ANF client
        client, _ = get_anf_client(print_output=print_output)

        # Build snapshot properties (using resolved values)
        snapshot_properties = {
            'location': resolved_location
        }
        
        # Note: Azure NetApp Files snapshots do not support tags
        # Tags are inherited from the parent volume
        
        # Create the snapshot object
        snapshot = Snapshot(**snapshot_properties)
        
        # Create the snapshot (using resolved values)
        poller = client.snapshots.begin_create(
            resource_group_name=resolved_resource_group_name,
            account_name=resolved_account_name,
            pool_name=resolved_pool_name,
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
        clean_msg = _get_clean_error_message(e)
        logger.error(f"Snapshot '{snapshot_name}' already exists: {clean_msg}")
        return {"status": "error", "details": clean_msg}
    except ResourceNotFoundError as e:
        clean_msg = _get_clean_error_message(e)
        logger.error(f"Source volume '{volume_name}' not found: {clean_msg}")
        return {"status": "error", "details": clean_msg}
    except Exception as e:
        clean_msg = _get_clean_error_message(e)
        logger.error(f"Failed to create snapshot: {clean_msg}")
        return {"status": "error", "details": clean_msg}


def delete_snapshot(
    snapshot_name: str,
    volume_name: str,
    resource_group_name: str = None,
    account_name: str = None,
    pool_name: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Delete an existing snapshot for an Azure NetApp Files volume.
    
    Args:
        snapshot_name (str):
            Required. The name of the snapshot to delete.
        volume_name (str):
            Required. The name of the volume.
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and operation details

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        ResourceNotFoundError: If the snapshot does not exist
        Exception: For other errors during snapshot deletion
    """

    # Retrieve config details from config file
    try:
        config = _retrieve_anf_config(print_output=print_output)
    except InvalidConfigError:
        raise

    # Resolve parameters from function arguments or config
    try:
        resolved_resource_group_name = _get_config_value('resource_group_name', resource_group_name, config, print_output)
        resolved_account_name = _get_config_value('account_name', account_name, config, print_output)
        resolved_pool_name = _get_config_value('pool_name', pool_name, config, print_output)
    except InvalidConfigError:
        raise

    # Validate input parameters (now using resolved values)
    _validate_required_params(
        resource_group_name=resolved_resource_group_name,
        account_name=resolved_account_name,
        pool_name=resolved_pool_name,
        volume_name=volume_name,
        snapshot_name=snapshot_name
    )

    try:
        # Get ANF client
        client, _ = get_anf_client(print_output=print_output)

        # Check if snapshot exists before attempting deletion
        try:
            _ = client.snapshots.get(
                resource_group_name=resolved_resource_group_name,
                account_name=resolved_account_name,
                pool_name=resolved_pool_name,
                volume_name=volume_name,
                snapshot_name=snapshot_name
            )
           
        except ResourceNotFoundError:
            error_message = f"Snapshot '{snapshot_name}' not found"
            logger.error(error_message)
            return {"status": "error", "details": f"Snapshot '{snapshot_name}' does not exist"}

        # Delete the snapshot (using resolved values)
        poller = client.snapshots.begin_delete(
            resource_group_name=resolved_resource_group_name,
            account_name=resolved_account_name,
            pool_name=resolved_pool_name,
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

    except ResourceNotFoundError as e:
        clean_msg = _get_clean_error_message(e)
        logger.error(f"Snapshot '{snapshot_name}' not found: {clean_msg}")
        return {"status": "error", "details": clean_msg}
    except Exception as e:
        clean_msg = _get_clean_error_message(e)
        logger.error(f"Failed to delete snapshot: {clean_msg}")
        return {"status": "error", "details": clean_msg}


def list_snapshots(
    volume_name: str,
    resource_group_name: str = None,
    account_name: str = None,
    pool_name: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    List all snapshots for an Azure NetApp Files volume.
    
    Args:
        volume_name (str):
            Required. The name of the volume.
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and list of snapshots.

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        ResourceNotFoundError: If the volume does not exist.
        Exception: For other errors during snapshot listing.
    """

    # Retrieve config details from config file
    try:
        config = _retrieve_anf_config(print_output=print_output)
    except InvalidConfigError:
        raise

    # Resolve parameters from function arguments or config
    try:
        resolved_resource_group_name = _get_config_value('resource_group_name', resource_group_name, config, print_output)
        resolved_account_name = _get_config_value('account_name', account_name, config, print_output)
        resolved_pool_name = _get_config_value('pool_name', pool_name, config, print_output)
    except InvalidConfigError:
        raise

    # Validate input parameters (now using resolved values)
    _validate_required_params(
        resource_group_name=resolved_resource_group_name,
        account_name=resolved_account_name,
        pool_name=resolved_pool_name,
        volume_name=volume_name
    )

    try:
        # Get ANF client
        client, _ = get_anf_client(print_output=print_output)

        # List all snapshots for the volume (using resolved values)
        snapshots = client.snapshots.list(
            resource_group_name=resolved_resource_group_name,
            account_name=resolved_account_name,
            pool_name=resolved_pool_name,
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
        clean_msg = _get_clean_error_message(e)
        logger.error(f"Volume '{volume_name}' not found: {clean_msg}")
        return {"status": "error", "details": clean_msg}
    except Exception as e:
        clean_msg = _get_clean_error_message(e)
        logger.error(f"Failed to list snapshots: {clean_msg}")
        return {"status": "error", "details": clean_msg}
        