from google.cloud import netapp_v1
from typing import Dict, Any
from .base import _serialize, create_client, validate_required_params

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

def create_snapshot(
    project_id: str,
    location: str,
    volume_id: str,
    snapshot_id: str,
    description: str = None,
    labels: dict = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a snapshot of a NetApp volume in Google Cloud.
    Snapshots are local space efficient image copies of your volume.
    Use snapshots to revert a volume to a prior point in time or to restore to a new volume as a copy of your original volume. 

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location to list volumes from.
        volume_id (str):
            Required. The ID of the volume to delete.
        snapshot_id (str):
            Required. The ID of the snapshot to create.
        description (str):
            Optional. The description of the snapshot. Defaults to None.
        labels (dict):
            Optional. The labels to assign to the snapshot. Defaults to None.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': API response object (if successful)
            - 'message': Error message (if failed)

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the snapshot creation process.
    """
    # Validate input parameters
    validate_required_params(
        project_id=project_id,
        location=location,
        volume_id=volume_id,
        snapshot_id=snapshot_id
    )

    if labels is not None and not isinstance(labels, dict):
        raise ValueError("labels must be a dictionary")
    
    try:
    
        client = create_client(print_output=print_output)

        # Construct a parent string
        parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

        # Define a snapshot
        snapshot = netapp_v1.Snapshot(description=description, labels=labels or {})

        # Initialize request argument(s)
        request = netapp_v1.CreateSnapshotRequest(parent=parent, snapshot_id=snapshot_id, snapshot=snapshot)

        # Make the request
        operation = client.create_snapshot(request=request)

        if print_output:
            logger.info("Creating snapshot...")

        response = operation.result()

        if print_output:
            logger.info(f"Snapshot created:\n{response}")

        return {"status": "success", "details": _serialize(response)}

    except Exception as e:
        if print_output:
            logger.error(f"An error occurred while creating the snapshot: {e}")
        return {"status": "error", "message": str(e)}


def delete_snapshot(
    project_id: str,
    location: str,
    volume_id: str,
    snapshot_id: str,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Delete a snapshot from a NetApp volume in Google Cloud.

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location of the volume.
        volume_id (str):
            Required. The ID of the volume.
        snapshot_id (str):
            Required. The ID of the snapshot to delete.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': API response object (if successful)
            - 'message': Error message (if failed)

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the snapshot deletion process.
    """
    # Validate input parameters
    validate_required_params(
        project_id=project_id,
        location=location,
        volume_id=volume_id,
        snapshot_id=snapshot_id
    )

    try:

        client = create_client(print_output=print_output)

        # Construct a name string
        name = f"projects/{project_id}/locations/{location}/volumes/{volume_id}/snapshots/{snapshot_id}"

        # Initialize request argument(s)
        request = netapp_v1.DeleteSnapshotRequest(name=name)

        # Make the request
        operation = client.delete_snapshot(request=request)

        if print_output:
            logger.info(f"Deleting snapshot: {name}...")

        response = operation.result()

        if print_output:
            logger.info(f"Snapshot deleted: {name}")

        return {"status": "success", "details": f"Snapshot deleted: {name}"}

    except Exception as e:
        if print_output:
            logger.error(f"An error occurred while deleting the snapshot: {e}")
        return {"status": "error", "message": str(e)}


def list_snapshots(
    project_id: str,
    location: str,
    volume_id: str,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    List all snapshots for a NetApp volume in the specified Google Cloud project and location.

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location to list volumes from.
        volume_id (str):
            Required. The ID of the volume to list snapshots for.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': List of snapshots (if successful)
            - 'message': Error message (if failed)

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the snapshot listing process.
    """
    # Validate input parameters
    validate_required_params(
        project_id=project_id,
        location=location,
        volume_id=volume_id
    )

    try:

        client = create_client(print_output=print_output)

        # Construct a parent string
        parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

        # Initialize request argument(s)
        request = netapp_v1.ListSnapshotsRequest(
            parent=parent,
        )

        # Make the request
        page_result = client.list_snapshots(request=request)

        if print_output:
            logger.info("Fetching list of snapshots...")

        snapshots = [s for s in page_result]

        if print_output:
            logger.info(f"Snapshots fetched:\n{snapshots}")

        return {"status": "success", "details": _serialize(snapshots)}

    except Exception as e:
        if print_output:
            logger.error(f"An error occurred while listing snapshots: {e}")
        return {"status": "error", "message": str(e)}
