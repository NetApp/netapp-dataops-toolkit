from google.cloud import netapp_v1

# from google.cloud.netapp_v1.types import (
#     Volume, ExportPolicy, SnapshotPolicy, BackupConfig,
#     TieringPolicy, RestoreParameters, Replication, DestinationVolumeParameters,
#     RestrictedAction, Snapshot, CreateSnapshotRequest, DeleteSnapshotRequest
# )

# from google.api_core.exceptions import GoogleAPICallError, InvalidArgument
 
def create_volume(
    project_id: str,
    location: str,
    volume_id: str,
    share_name: str,
    storage_pool: str,
    capacity_gib: int,
    protocols: list,
    export_policy_rules: list = None,
    smb_settings: list = None,
    unix_permissions: str = None,
    labels: dict = None,
    description: str = None,
    snapshot_policy: dict = None,
    snap_reserve: float = None,
    snapshot_directory: bool = None,
    security_style: str = None,
    kerberos_enabled: bool = None,
    backup_policies: list = None,
    backup_vault: str = None,
    scheduled_backup_enabled: bool = None,
    block_deletion_when_clients_connected: bool = None,
    large_capacity: bool = None,
    multiple_endpoints: bool = None,
    tiering_enabled: bool = None,
    cooling_threshold_days: int = None
):
    
    # Create a client
    client = netapp_v1.NetAppClient()

    # Create a parent string
    parent = f"projects/{project_id}/locations/{location}"

    # Initialize request argument(s)
    volume = netapp_v1.Volume(
        share_name=share_name,
        storage_pool=storage_pool,
        capacity_gib=capacity_gib,
        protocols=protocols,
        description=description,
        labels=labels or {},
        unix_permissions=unix_permissions,
        snapshot_directory=snapshot_directory,
        security_style=security_style,
        kerberos_enabled=kerberos_enabled,
        large_capacity=large_capacity,
        multiple_endpoints=multiple_endpoints,
    )

    if smb_settings:
        volume.smb_settings = smb_settings

    if export_policy_rules:
        volume.export_policy = netapp_v1.ExportPolicy(
            rules=[
                netapp_v1.ExportPolicyRule(
                    allowed_clients=rule.get("allowed_clients", ""),
                    access_type=rule.get("access_type", "READ_WRITE"),
                    has_root_access=rule.get("has_root_access", False),
                    nfsv3=rule.get("nfsv3", False),
                    nfsv4=rule.get("nfsv4", False),
                ) for rule in export_policy_rules
            ]
        )

    if snapshot_policy:
        volume.snapshot_policy = netapp_v1.SnapshotPolicy(**snapshot_policy)

    if tiering_enabled:
        volume.tiering_policy = netapp_v1.TieringPolicy(
            cooling_period_days=cooling_threshold_days or 0
        )

    if backup_policies or backup_vault:
        volume.backup_config = netapp_v1.BackupConfig(
            backup_policies=backup_policies or [],
            backup_vault=backup_vault or "",
            scheduled_backup_enabled=scheduled_backup_enabled or False
        )

    if block_deletion_when_clients_connected:
        volume.restricted_actions = [netapp_v1.RestrictedAction.BLOCK_VOLUME_DELETION]

    request = netapp_v1.CreateVolumeRequest(
        parent=parent,
        volume_id=volume_id,
        volume=volume
    )

    # Make the request
    operation = client.create_volume(request=request)

    print("Waiting for operation to complete...")

    response = operation.result()

    # Handle the response
    print(response)

    return response
 
def clone_volume(
    project_id: str,
    location: str,
    volume_id: str,
    source_volume: str,
    source_snapshot: str,
    share_name: str,
    storage_pool: str,
    protocols: list,
    export_policy_rules: list = None,
    smb_settings: list = None,
    unix_permissions: str = None,
    labels: dict = None,
    description: str = None,
    snapshot_policy: dict = None,
    snap_reserve: float = None,
    snapshot_directory: bool = None,
    security_style: str = None,
    kerberos_enabled: bool = None,
    backup_policies: list = None,
    backup_vault: str = None,
    scheduled_backup_enabled: bool = None,
    block_deletion_when_clients_connected: bool = None,
    large_capacity: bool = None,
    multiple_endpoints: bool = None,
    tiering_enabled: bool = None,
    cooling_threshold_days: int = None
):
    # Create a client
    client = netapp_v1.NetAppClient()

    # Create a parent string
    parent = f"projects/{project_id}/locations/{location}"
 
    # Fetch source volume to get capacity
    source_name = f"{parent}/volumes/{source_volume}"
    source_vol = client.get_volume(name=source_name)
    
    # Initialize request argument(s)
    volume = netapp_v1.Volume(
        share_name=share_name,
        storage_pool=storage_pool,
        capacity_gib=source_vol.capacity_gib,
        protocols=protocols,
        restore_parameters=netapp_v1.RestoreParameters(
            source_volume=source_name,
            source_snapshot=source_snapshot
        ),
        description=description,
        labels=labels or {},
        unix_permissions=unix_permissions,
        snapshot_directory=snapshot_directory,
        security_style=security_style,
        kerberos_enabled=kerberos_enabled,
        large_volume=large_capacity,
        multi_protocol_access=multiple_endpoints,
    )
 
    if smb_settings:
        volume.smb_settings = smb_settings
 
    if export_policy_rules:
        volume.export_policy = netapp_v1.ExportPolicy(
            rules=[netapp_v1.ExportPolicyRule(**rule) for rule in export_policy_rules]
        )
 
    if snapshot_policy:
        volume.snapshot_policy = netapp_v1.SnapshotPolicy(**snapshot_policy)
 
    if tiering_enabled:
        volume.tiering_policy = netapp_v1.TieringPolicy(
            cooling_period_days=cooling_threshold_days or 0
        )
 
    if backup_policies or backup_vault:
        volume.backup_config = netapp_v1.BackupConfig(
            backup_policies=backup_policies or [],
            backup_vault=backup_vault or "",
            scheduled_backup_enabled=scheduled_backup_enabled or False
        )
 
    if block_deletion_when_clients_connected:
        volume.restricted_actions = [netapp_v1.RestrictedAction.BLOCK_VOLUME_DELETION]
 
    request = netapp_v1.CreateVolumeRequest(
        parent=parent,
        volume_id=volume_id,
        volume=volume
    )

    # Make the request
    operation = client.create_volume(request=request)

    print("Waiting for cloning operation to complete...")

    response = operation.result()

    # Handle the response
    print(response)

 
def delete_volume(project_id: str, location: str, volume_id: str, force: bool = False):
    # Create a client
    client = netapp_v1.NetAppClient()

    # Construct a name string
    name = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Initialize request argument(s)
    request = netapp_v1.DeleteVolumeRequest(name=name, force=force)

    # Make the request
    operation = client.delete_volume(request=request)

    print("Waiting for deletion of a volume to complete...")

    response = operation.result()

    # Handle the response
    print(response)

 
def list_volumes(project_id: str, location: str):
    # Create a client
    client = netapp_v1.NetAppClient()

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}"

    # Initialize request argument(s)
    request = netapp_v1.ListVolumesRequest(parent=parent)

    # Make the request
    page_result = client.list_volumes(request=request)

    # Handle the response
    for response in page_result:
        print(response)
 
def create_snapshot(project_id: str, location: str, volume_id: str, snapshot_id: str, description: str = None, labels: dict = None):
    # Create a client
    client = netapp_v1.NetAppClient()

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Define a snapshot
    snapshot = netapp_v1.Snapshot(snapshot_id=snapshot_id, description=description, labels=labels or {})

    # Initialize request argument(s)
    request = netapp_v1.CreateSnapshotRequest(parent=parent, snapshot_id=snapshot_id, snapshot=snapshot)

    # Make the request
    operation = client.create_snapshot(request=request)

    print("Waiting for creation of a snapshot to complete...")

    response = operation.result()

    # Handle the response
    print(response)

 
def delete_snapshot(project_id: str, location: str, volume_id: str, snapshot_id: str):
    # Create a client
    client = netapp_v1.NetAppClient()

    # Construct a name string
    name = f"projects/{project_id}/locations/{location}/volumes/{volume_id}/snapshots/{snapshot_id}"

    # Initialize request argument(s)
    request = netapp_v1.DeleteSnapshotRequest(name=name)

    # Make the request
    operation = client.delete_snapshot(request=request)

    print("Waiting for deletion of snapshot to complete...")

    response = operation.result()

    # Handle the response
    print(response)


def list_snapshots(project_id: str, location: str, volume_id: str):
    # Create a client
    client = netapp_v1.NetAppClient()

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Initialize request argument(s)
    request = netapp_v1.ListSnapshotsRequest(
        parent=parent,
    )

    # Make the request
    page_result = client.list_snapshots(request=request)

    # Handle the response
    for response in page_result:
        print(response)

 
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
    labels: dict = None
):
    # Create a client
    client = netapp_v1.NetAppClient()

    # Construct a parent string
    parent = f"projects/{source_project_id}/locations/{source_location}/volumes/{source_volume_id}"
 
    # Initialize request argument(s)
    destination_params = netapp_v1.DestinationVolumeParameters(
        storage_pool=destination_storage_pool,
        volume_id=destination_volume_id,
        share_name=destination_share_name,
        description=destination_volume_description
    )
 
    if tiering_enabled:
        destination_params.tiering_policy = netapp_v1.TieringPolicy(
            cooling_period_days=cooling_threshold_days or 0
        )
 
    replication = netapp_v1.Replication(
        replication_schedule=replication_schedule,
        destination_volume_parameters=destination_params,
        description=description,
        labels=labels or {}
    )
 
    request = netapp_v1.CreateReplicationRequest(
        parent=parent,
        replication=replication,
        replication_id=replication_id
    )
 
    # Make the request
    operation = client.create_replication(request=request)

    print("Waiting for operation to complete...")

    response = operation.result()

    # Handle the response
    print(response) 