from google.cloud import netapp_v1
from typing import Dict, Any
from .base import _serialize, create_client, validate_required_params

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

def create_replication(
    source_project_id: str,
    source_location: str,
    source_volume_id: str,
    replication_id: str,
    replication_schedule: str,
    destination_storage_pool: str,
    destination_volume_id: str = None,
    destination_share_name: str = None,
    destination_volume_description: str = None,
    tiering_enabled: bool = None,
    cooling_threshold_days: int = None,
    description: str = None,
    labels: dict = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a replication for a volume.
    Volume replication enables asynchronous replication of a volume to a different location.
    A new volume in the destination location will be created in a storage pool with available capacity within a supported region pair.
    
    Supported region pairs for volume replication:

    For STANDARD, PREMIUM, and EXTREME service levels:
    - asia-southeast1 ↔ australia-southeast1
    - europe-west2 ↔ europe-west3
    - europe-west2 ↔ europe-west4
    - europe-west3 ↔ europe-west4
    - europe-west3 ↔ europe-west6
    - europe-southwest1 ↔ europe-west3
    - northamerica-northeast1 ↔ northamerica-northeast2
    - northamerica-northeast1 ↔ us-central1
    - australia-southeast1 ↔ asia-southeast1
    - us-central1 ↔ us-east4
    - us-central1 ↔ us-west2
    - us-central1 ↔ us-west3
    - us-central1 ↔ us-west4
    - us-east4 ↔ us-west2
    - us-east4 ↔ us-west4
    - us-west2 ↔ us-west4
    - us-west3 ↔ us-west4
    
    For FLEX service level, replication is supported between regions within the same region group:
    
    Americas: southamerica-east1, southamerica-west1, northamerica-northeast1,
              northamerica-northeast2, us-central1, us-east1, us-east4, us-east5,
              us-south1, us-west1, us-west2, us-west3, us-west4
              
    Asia-Pacific: asia-east1, asia-east2, asia-northeast1, asia-northeast2,
                  asia-northeast3, asia-south1, asia-south2, asia-southeast1,
                  asia-southeast2, australia-southeast1, australia-southeast2
                  
    Europe/Middle East/Africa: africa-south1, europe-central2, europe-north1,
                               europe-southwest1, europe-west1, europe-west2,
                               europe-west3, europe-west4, europe-west6, europe-west8,
                               europe-west9, europe-west10, europe-west12, me-central1,
                               me-central2, me-west1
    
    For the most up-to-date list: https://cloud.google.com/netapp/volumes/docs/protect-data/about-volume-replication

    Args:
        source_project_id (str):
            Required. The ID of the source project.
        source_location (str):
            Required. The location of the source volume.
        source_volume_id (str):
            Required. The ID of the source volume to replicate.
            Full name of source volume resource. Example :
            "projects/{source_project_id}/locations/{source_location}/volumes/{source_volume_id}"
        replication_id (str):
            Required. The ID for the new replication.
        replication_schedule (str, google.cloud.netapp_v1.types.Replication.ReplicationSchedule):
            Required. Indicates the schedule for replication.
        destination_storage_pool (str):
            Required. The storage pool for the destination volume.
            Full name of destination storage pool resource should be provided. Example:
            "projects/{destination_project_id}/locations/{destination_location}/storagePools/{destination_storage_pool_id}"
        destination_volume_id (str):
            Optional. Desired destination volume resource id.
            If not specified, source volume's resource id will be used. 
            This value must start with a lowercase letter followed by up to 62 lowercase letters, numbers, or hyphens, and cannot end with a hyphen.
        destination_share_name (str):
            Optional. Destination volume's share name.
            If not specified, source volume's share name will be used.
        destination_volume_description (str):
            Optional. Description for the destination volume.
        tiering_enabled (bool):
            Optional. Whether tiering is enabled on the destination volume.
        cooling_threshold_days (int):
            Optional. Time in days to mark the volume's data block as cold and make it eligible for tiering.
            It can be range from 2-183. Default is 31.
        description (str):
            Optional. A description about this replication relationship.
        labels (dict, MutableMapping[str, str]):
            Optional. Resource labels to represent user provided metadata.
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
        Exception: If there is an error during the replication creation process.
    """
    # Validate input parameters
    validate_required_params(
        source_project_id=source_project_id,
        source_location=source_location,
        source_volume_id=source_volume_id,
        replication_id=replication_id,
        replication_schedule=replication_schedule,
        destination_storage_pool=destination_storage_pool
    )

    if labels is not None and not isinstance(labels, dict):
        raise ValueError("labels must be a dictionary")
    
    try:
        client = create_client(print_output=print_output)

        # Construct a parent string
        parent = f"projects/{source_project_id}/locations/{source_location}/volumes/{source_volume_id}"
    
        # Initialize request argument(s)
        destination_params = netapp_v1.DestinationVolumeParameters(
            storage_pool=destination_storage_pool,
            volume_id=destination_volume_id,
            share_name=destination_share_name,
            description=destination_volume_description
        )
    
        # Build TieringPolicy if provided
        if tiering_enabled:
            destination_params.tiering_policy = netapp_v1.TieringPolicy(
                cooling_threshold_days=cooling_threshold_days or 0
            )
    
        # Construct the replication object
        replication = netapp_v1.Replication(
            replication_schedule=replication_schedule,
            destination_volume_parameters=destination_params,
            description=description,
            labels=labels or {}
        )
    
        # Construct the request
        request = netapp_v1.CreateReplicationRequest(
            parent=parent,
            replication=replication,
            replication_id=replication_id
        )
 
        # Make the request
        operation = client.create_replication(request=request)

        if print_output:
            logger.info("Creating replication...")

        response = operation.result()

        if print_output:
            logger.info(f"Replication created:\n{response}")

        return {"status": "success", "details": _serialize(response)}

    except Exception as e:
        if print_output:
            logger.error(f"An error occurred while creating the replication: {e}")
        return {"status": "error", "message": str(e)}
