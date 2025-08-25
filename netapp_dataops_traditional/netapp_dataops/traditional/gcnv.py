from google.cloud import netapp_v1

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
    """
    Create a new volume in the specified project and location.

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location for the volume.
        volume_id (str):
            Required. The ID for the new volume.
        share_name (str):
            Required. Share name of the volume.
        storage_pool (str):
            Required. StoragePool name of the volume.
        capacity_gib (int):
            Required. The capacity of the volume in GiB.
        protocols (list, (MutableSequence[google.cloud.netapp_v1.types.Protocols])):
            Required. List of protocols to enable on the volume.
            Allowed values within list: NFSV3, NFSV4, SMB.
        export_policy_rules (list):
            Optional. Export policy rules for the volume to construct google.cloud.netapp_v1.types.ExportPolicy.
            Defaults to an empty list.
        smb_settings (list, MutableSequence[google.cloud.netapp_v1.types.SMBSettings]):
            Optional. SMB share settings for the volume.
            Defaults to an empty list.
        unix_permissions (str):
            Optional. Default unix style permission (e.g.777) the mount point will be created with.
            Applicable for NFS protocol types only.
            Defaults to None.
        labels (dict, MutableMapping[str, str]):
            Optional. Labels as key value pairs.
            Defaults to an empty dict.
        description (str):
            Optional. Description of the volume.
            Defaults to an empty string.
        snapshot_policy (dict, google.cloud.netapp_v1.types.SnapshotPolicy):
            Optional. Snapshot policy for the volume.
            If enabled, make snapshots automatically according to the schedules. Default is False.
            Defaults to an empty dict.
        snap_reserve (float):
            Optional. Snap_reserve specifies percentage of volume
            storage reserved for snapshot storage.
            Default is 0 percent.
        snapshot_directory (bool):
            Optional. Snapshot_directory if enabled (true) the volume
            will contain a read-only .snapshot directory which provides
            access to each of the volume's snapshots.
            Defaults to False.
        security_style (str, google.cloud.netapp_v1.types.SecurityStyle):
            Optional. Security style of the volume.
            Allowed values: NTFS, UNIX.
            Defaults to None.
        kerberos_enabled (bool):
            Optional. Flag indicating if the volume is a
            kerberos volume or not, export policy rules
            control kerberos security modes (krb5, krb5i, krb5p).
            Defaults to False.
        backup_policies (list, google.cloud.netapp_v1.types.BackupConfig):
            Optional. Backup policies for the volume.
            When specified, schedule backups will be created based on the policy configuration.
            Defaults to an empty list.
        backup_vault (str, google.cloud.netapp_v1.types.BackupConfig.backup_vault):
            Optional. Name of backup vault.
            Format: projects/{project_id}/locations/{location}/backupVaults/{backup_vault_id}
            Defaults to an empty string.
        scheduled_backup_enabled (bool):
            Optional. When set to true, scheduled backup is enabled on the volume.
            This field should be nil when there's no backup policy attached.
            Defaults to False.
        block_deletion_when_clients_connected (bool):
            Optional. Block deletion when clients are connected.
            Defaults to False.
        large_capacity (bool):
            Optional. Flag indicating if the volume will
            be a large capacity volume or a regular volume.
            If set to True, the volume will be a large capacity volume.
            Defaults to False.
        multiple_endpoints (bool):
            Optional. Flag indicating if the volume will have an IP
            address per node for volumes supporting multiple IP
            endpoints. Only the volume with large_capacity will be
            allowed to have multiple endpoints.
            Defaults to False.
        tiering_enabled (bool):
            Optional. Flag indicating if the volume has tiering policy enable/pause.
            Defaults to PAUSED.
        cooling_threshold_days (int):
            Optional. Time in days to mark the volume's data block as cold and make it eligible for tiering.
            It can be range from 2-183.
            Defaults to 31.

    Returns:
        Dict[str, Any]: Details of the created volume.

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the volume creation process.
    """
    # Validate input parameters
    if not project_id or not location or not volume_id or not share_name or not storage_pool or not capacity_gib or not protocols:
        raise ValueError("Project ID, location, volume ID, share name, storage pool, capacity GiB, and protocols are required parameters.")
    
    try:
        # Create a NetApp client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

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

    # Build ExportPolicy if provided
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

    # Build SnapshotPolicy if provided
    if snapshot_policy:
        volume.snapshot_policy = netapp_v1.SnapshotPolicy(**snapshot_policy)

    # Build TieringPolicy if provided
    if tiering_enabled:
        volume.tiering_policy = netapp_v1.TieringPolicy(
            cooling_period_days=cooling_threshold_days or 0
        )

    # Build BackupConfig if provided
    if backup_policies or backup_vault:
        volume.backup_config = netapp_v1.BackupConfig(
            backup_policies=backup_policies or [],
            backup_vault=backup_vault or "",
            scheduled_backup_enabled=scheduled_backup_enabled or False
        )

    # Build RestrictedAction if provided
    if block_deletion_when_clients_connected:
        volume.restricted_actions = [netapp_v1.RestrictedAction.BLOCK_VOLUME_DELETION]

    # Construct the request
    request = netapp_v1.CreateVolumeRequest(
        parent=parent,
        volume_id=volume_id,
        volume=volume
    )

    try:
        # Make the request
        operation = client.create_volume(request=request)

        print("Waiting for operation to complete...")

        response = operation.result()

        # Handle the response
        print(response)

        return response
    
    except Exception as e:
        print(f"An error occurred while creating the volume: {e}")
        raise e

 
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
    """
    Clone an existing volume.

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location for the volume.
        volume_id (str):
            Required. The ID for the new cloned volume.
        source_volume (str):
            Required. The ID of the source volume to clone from.
        source_snapshot (str):
            Required. The snapshot to clone from.
        share_name (str):
            Required. Share name of the volume.
        storage_pool (str):
            Required. StoragePool name of the volume.
        protocols (list, (MutableSequence[google.cloud.netapp_v1.types.Protocols])):
            Required. List of protocols to enable on the volume.
            Allowed values within list: NFSV3, NFSV4, SMB.
        export_policy_rules (list):
            Optional. Export policy rules for the volume to construct google.cloud.netapp_v1.types.ExportPolicy.
            Defaults to an empty list.
        smb_settings (list, MutableSequence[google.cloud.netapp_v1.types.SMBSettings]):
            Optional. SMB share settings for the volume.
            Defaults to an empty list.
        unix_permissions (str):
            Optional. Default unix style permission (e.g.777) the mount point will be created with.
            Applicable for NFS protocol types only.
            Defaults to None.
        labels (dict, MutableMapping[str, str]):
            Optional. Labels as key value pairs.
            Defaults to an empty dict.
        description (str):
            Optional. Description of the volume.
            Defaults to an empty string.
        snapshot_policy (dict, google.cloud.netapp_v1.types.SnapshotPolicy):
            Optional. Snapshot policy for the volume.
            If enabled, make snapshots automatically according to the schedules. Default is False.
            Defaults to an empty dict.
        snap_reserve (float):
            Optional. Snap_reserve specifies percentage of volume
            storage reserved for snapshot storage.
            Default is 0 percent.
        snapshot_directory (bool):
            Optional. Snapshot_directory if enabled (true) the volume
            will contain a read-only .snapshot directory which provides
            access to each of the volume's snapshots.
            Defaults to False.
        security_style (str, google.cloud.netapp_v1.types.SecurityStyle):
            Optional. Security style of the volume.
            Allowed values: NTFS, UNIX.
            Defaults to None.
        kerberos_enabled (bool):
            Optional. Flag indicating if the volume is a
            kerberos volume or not, export policy rules
            control kerberos security modes (krb5, krb5i, krb5p).
            Defaults to False.
        backup_policies (list, google.cloud.netapp_v1.types.BackupConfig):
            Optional. Backup policies for the volume.
            When specified, schedule backups will be created based on the policy configuration.
            Defaults to an empty list.
        backup_vault (str, google.cloud.netapp_v1.types.BackupConfig.backup_vault):
            Optional. Name of backup vault.
            Format: projects/{project_id}/locations/{location}/backupVaults/{backup_vault_id}
            Defaults to an empty string.
        scheduled_backup_enabled (bool):
            Optional. When set to true, scheduled backup is enabled on the volume.
            This field should be nil when there's no backup policy attached.
            Defaults to False.
        block_deletion_when_clients_connected (bool):
            Optional. Block deletion when clients are connected.
            Defaults to False.
        large_capacity (bool):
            Optional. Flag indicating if the volume will
            be a large capacity volume or a regular volume.
            If set to True, the volume will be a large capacity volume.
            Defaults to False.
        multiple_endpoints (bool):
            Optional. Flag indicating if the volume will have an IP
            address per node for volumes supporting multiple IP
            endpoints. Only the volume with large_capacity will be
            allowed to have multiple endpoints.
            Defaults to False.
        tiering_enabled (bool):
            Optional. Flag indicating if the volume has tiering policy enable/pause.
            Defaults to PAUSED.
        cooling_threshold_days (int):
            Optional. Time in days to mark the volume's data block as cold and make it eligible for tiering.
            It can be range from 2-183.
            Defaults to 31.

    Returns:
        None

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error while fetching the source volume.
        Exception: If there is an error during the cloning process.
    """
    # Validate input parameters
    if not project_id or not location or not volume_id or not source_volume or not source_snapshot or not share_name or not storage_pool or not protocols:
        raise ValueError("Project ID, location, volume ID, source volume, source snapshot, share name, storage pool, and protocols are required parameters.")
    
    try:
        # Create a NetApp client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

    # Create a parent string
    parent = f"projects/{project_id}/locations/{location}"
 
    # Fetch source volume to get capacity
    source_name = f"{parent}/volumes/{source_volume}"
    try:
        source_vol = client.get_volume(name=source_name)
    except Exception as e:
        print(f"An error occurred while fetching the source volume: {e}")
        raise e

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

    # Build ExportPolicy if provided
    if export_policy_rules:
        volume.export_policy = netapp_v1.ExportPolicy(
            rules=[netapp_v1.ExportPolicyRule(**rule) for rule in export_policy_rules]
        )
 
    # Build SnapshotPolicy if provided
    if snapshot_policy:
        volume.snapshot_policy = netapp_v1.SnapshotPolicy(**snapshot_policy)
 
    # Build TieringPolicy if provided
    if tiering_enabled:
        volume.tiering_policy = netapp_v1.TieringPolicy(
            cooling_period_days=cooling_threshold_days or 0
        )
 
    # Build BackupConfig if provided
    if backup_policies or backup_vault:
        volume.backup_config = netapp_v1.BackupConfig(
            backup_policies=backup_policies or [],
            backup_vault=backup_vault or "",
            scheduled_backup_enabled=scheduled_backup_enabled or False
        )
 
    # Build RestrictedAction if provided
    if block_deletion_when_clients_connected:
        volume.restricted_actions = [netapp_v1.RestrictedAction.BLOCK_VOLUME_DELETION]
 
    # Construct the request
    request = netapp_v1.CreateVolumeRequest(
        parent=parent,
        volume_id=volume_id,
        volume=volume
    )

    try:
        # Make the request
        operation = client.create_volume(request=request)

        print("Waiting for cloning operation to complete...")

        response = operation.result()

        # Handle the response
        print(response)

    except Exception as e:
        print(f"An error occurred while cloning the volume: {e}")
        raise e


def delete_volume(
        project_id: str,
        location: str,
        volume_id: str,
        force: bool = False):
    """
    Delete a volume in the specified project and location.
    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location of the volume.
        volume_id (str):
            Required. The ID of the volume to delete.
        force (bool):
            Optional. If set to True, the volume will be deleted even if it is not empty.
            Defaults to False.

    Returns:
        None

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the volume deletion process.
    """
    # Validate input parameters
    if not project_id or not location or not volume_id:
        raise ValueError("Project ID, location, and volume ID are required parameters.")

    try:
        # Create a client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

    # Construct a name string
    name = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Initialize request argument(s)
    request = netapp_v1.DeleteVolumeRequest(name=name, force=force)

    try:
        # Make the request
        operation = client.delete_volume(request=request)

        print("Waiting for deletion of a volume to complete...")

        response = operation.result()

        # Handle the response
        print(response)

    except Exception as e:
        print(f"An error occurred while deleting the volume: {e}")
        raise e

 
def list_volumes(
        project_id: str,
        location: str):
    """
    List all volumes in a project and location.

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location to list volumes from.

    Returns:
        None

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the volume listing process.
    """
    # Validate input parameters
    if not project_id or not location:
        raise ValueError("Project ID and location are required parameters.")

    try:
        # Create a client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}"

    # Initialize request argument(s)
    request = netapp_v1.ListVolumesRequest(parent=parent)

    try:
        # Make the request
        page_result = client.list_volumes(request=request)

        # Handle the response
        for response in page_result:
            print(response)

    except Exception as e:
        print(f"An error occurred while listing volumes: {e}")
        raise e


def create_snapshot(
    project_id: str,
    location: str,
    volume_id: str,
    snapshot_id: str,
    description: str = None,
    labels: dict = None
):
    """
    Create a near-instantaneous, space-efficient, read-only copy of an existing data volume, called a snapshot. 
    Snapshots are particularly useful for versioning datasets and implementing dataset-to-model traceability.

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
        None

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the snapshot creation process.
    """
    # Validate input parameters
    if not project_id or not location or not volume_id or not snapshot_id:
        raise ValueError("Project ID, location, volume ID, and snapshot ID are required parameters.")
    
    try:
        # Create a client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Define a snapshot
    snapshot = netapp_v1.Snapshot(snapshot_id=snapshot_id, description=description, labels=labels or {})

    # Initialize request argument(s)
    request = netapp_v1.CreateSnapshotRequest(parent=parent, snapshot_id=snapshot_id, snapshot=snapshot)

    try:
        # Make the request
        operation = client.create_snapshot(request=request)

        print("Waiting for creation of a snapshot to complete...")

        response = operation.result()

        # Handle the response
        print(response)

    except Exception as e:
        print(f"An error occurred while creating the snapshot: {e}")
        raise e


def delete_snapshot(
    project_id: str,
    location: str,
    volume_id: str,
    snapshot_id: str
):
    """
    Delete a snapshot.

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
        None

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the snapshot deletion process.
    """
    # Validate input parameters
    if not project_id or not location or not volume_id or not snapshot_id:
        raise ValueError("Project ID, location, volume ID, and snapshot ID are required parameters.")

    try:
        # Create a client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

    # Construct a name string
    name = f"projects/{project_id}/locations/{location}/volumes/{volume_id}/snapshots/{snapshot_id}"

    # Initialize request argument(s)
    request = netapp_v1.DeleteSnapshotRequest(name=name)

    try:
        # Make the request
        operation = client.delete_snapshot(request=request)

        print("Waiting for deletion of snapshot to complete...")

        response = operation.result()

        # Handle the response
        print(response)

    except Exception as e:
        print(f"An error occurred while deleting the snapshot: {e}")
        raise e


def list_snapshots(
    project_id: str,
    location: str,
    volume_id: str
):
    """
    List all snapshots for a given volume.

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location to list volumes from.
        volume_id (str):
            Required. The ID of the volume to list snapshots for.

    Returns:
        None

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the snapshot listing process.
    """
    # Validate input parameters
    if not project_id or not location or not volume_id:
        raise ValueError("Project ID, location, and volume ID are required parameters.")

    try:
        # Create a client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

    # Construct a parent string
    parent = f"projects/{project_id}/locations/{location}/volumes/{volume_id}"

    # Initialize request argument(s)
    request = netapp_v1.ListSnapshotsRequest(
        parent=parent,
    )

    try:
        # Make the request
        page_result = client.list_snapshots(request=request)

        # Handle the response
        for response in page_result:
            print(response)

    except Exception as e:
        print(f"An error occurred while listing snapshots: {e}")
        raise e

 
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
    """
    Create a replication for a volume.

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
            Optional. Resource labels to represent user provided
            metadata.

    Returns:
        None

    Raises:
        ValueError: If required parameters are missing.
        Exception: If there is an error while creating the NetApp client.
        Exception: If there is an error during the replication creation process.
    """
    # Validate input parameters
    if not source_project_id or not source_location or not source_volume_id or not replication_id or not replication_schedule or not destination_storage_pool:
        raise ValueError("Source project ID, location, source volume ID, replication ID, replication schedule, and destination storage pool are required parameters.")
    
    try:
        # Create a client
        client = netapp_v1.NetAppClient()
    except Exception as e:
        print(f"An error occurred while creating the NetApp client: {e}")
        raise e

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
            cooling_period_days=cooling_threshold_days or 0
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
 
    try:
        # Make the request
        operation = client.create_replication(request=request)

        print("Waiting for operation to complete...")

        response = operation.result()

        # Handle the response
        print(response)

    except Exception as e:
        print(f"An error occurred while creating the replication: {e}")
        raise e