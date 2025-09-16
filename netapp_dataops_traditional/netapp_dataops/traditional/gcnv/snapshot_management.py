from google.cloud import netapp_v1
from typing import Dict, Any
from .base import _serialize, create_client, validate_required_params


def create_snapshot(
    project_id: str,
    location: str,
    volume_id: str,
    snapshot_id: str,
    description: str = None,
    labels: dict = None
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
        labels (dict, optional):
            Optional. The labels to assign to the snapshot. Defaults to None.

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
    
    client = create_client()

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Define a snapshot
    snapshot = netapp_v1.Snapshot(description=description, labels=labels or {})

    # Initialize request argument(s)
    request = netapp_v1.CreateSnapshotRequest(parent=parent, snapshot_id=snapshot_id, snapshot=snapshot)

    try:
        # Make the request
        operation = client.create_snapshot(request=request)

        print("Waiting for creation of a snapshot to complete...")

        response = operation.result()

        return {"status": "success", "details": _serialize(response)}

    except Exception as e:
        print(f"An error occurred while creating the snapshot: {e}")
        return {"status": "error", "message": str(e)}


def delete_snapshot(
    project_id: str,
    location: str,
    volume_id: str,
    snapshot_id: str
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

    client = create_client()

    # Construct a name string
    name = f"projects/{project_id}/locations/{location}/volumes/{volume_id}/snapshots/{snapshot_id}"

    # Initialize request argument(s)
    request = netapp_v1.DeleteSnapshotRequest(name=name)

    try:
        # Make the request
        operation = client.delete_snapshot(request=request)

        print("Waiting for deletion of snapshot to complete...")

        response = operation.result()

        return {"status": "success", "details": _serialize(response)}

    except Exception as e:
        print(f"An error occurred while deleting the snapshot: {e}")
        return {"status": "error", "message": str(e)}


def list_snapshots(
    project_id: str,
    location: str,
    volume_id: str
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

    client = create_client()

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Initialize request argument(s)
    request = netapp_v1.ListSnapshotsRequest(
        parent=parent,
    )

    try:
        # Make the request
        page_result = client.list_snapshots(request=request)

        snapshots = [s for s in page_result]

        return {"status": "success", "details": _serialize(snapshots)}

    except Exception as e:
        print(f"An error occurred while listing snapshots: {e}")
        return {"status": "error", "message": str(e)}
