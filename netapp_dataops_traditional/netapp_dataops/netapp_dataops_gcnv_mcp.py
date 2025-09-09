#!/usr/bin/env python3
import sys
import asyncio
from typing import Any, Dict
from fastmcp import FastMCP

# Importing the necessary functions from the traditional GCNV module
from netapp_dataops.traditional.gcnv import (
    create_volume,
    clone_volume,
    list_volumes,
    create_snapshot,
    list_snapshots,
    create_replication
)

# Creating an instance of FastMCP for the NetApp DataOps Traditional GCNV Toolkit
mcp = FastMCP("NetApp DataOps Traditional GCNV Toolkit MCP")

@mcp.tool(name = "Create Volume")
async def create_volume_tool(
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
) -> Dict[str, Any]:
    """
    Use this tool to create a new volume in the specified project and location.

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
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': API response object (if successful)
            - 'message': Error message (if failed)

    Error Handling:
        If an error occurs while creating the volume, the tool logs the error using `mcp.log_error()` and returns a response
        with "status": "error" and the error message.
    """
    response = create_volume(
        project_id=project_id,
        location=location,
        volume_id=volume_id,
        share_name=share_name,
        storage_pool=storage_pool,
        capacity_gib=capacity_gib,
        protocols=protocols,
        export_policy_rules=export_policy_rules,
        smb_settings=smb_settings,
        unix_permissions=unix_permissions,
        labels=labels,
        description=description,
        snapshot_policy=snapshot_policy,
        snap_reserve=snap_reserve,
        snapshot_directory=snapshot_directory,
        security_style=security_style,
        kerberos_enabled=kerberos_enabled,
        backup_policies=backup_policies,
        backup_vault=backup_vault,
        scheduled_backup_enabled=scheduled_backup_enabled,
        block_deletion_when_clients_connected=block_deletion_when_clients_connected,
        large_capacity=large_capacity,
        multiple_endpoints=multiple_endpoints,
        tiering_enabled=tiering_enabled,
        cooling_threshold_days=cooling_threshold_days
    )
    if response['status'] == 'error':
        mcp.log_error(f"Error creating volume: {response['message']}")
    return response
    
    
@mcp.tool(name = "Clone Volume")
async def clone_volume_tool(
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
) -> Dict[str, Any]:
    """
    Use this tool to clone an existing volume.

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
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': API response object (if successful)
            - 'message': Error message (if failed)

    Error Handling:
        If an error occurs while cloning the volume, the tool logs the error using `mcp.log_error()` and returns a response
        with "status": "error" and the error message.
    """
    response = clone_volume(
        project_id=project_id,
        location=location,
        volume_id=volume_id,
        source_volume=source_volume,
        source_snapshot=source_snapshot,
        share_name=share_name,
        storage_pool=storage_pool,
        protocols=protocols,
        export_policy_rules=export_policy_rules,
        smb_settings=smb_settings,
        unix_permissions=unix_permissions,
        labels=labels,
        description=description,
        snapshot_policy=snapshot_policy,
        snap_reserve=snap_reserve,
        snapshot_directory=snapshot_directory,
        security_style=security_style,
        kerberos_enabled=kerberos_enabled,
        backup_policies=backup_policies,
        backup_vault=backup_vault,
        scheduled_backup_enabled=scheduled_backup_enabled,
        block_deletion_when_clients_connected=block_deletion_when_clients_connected,
        large_capacity=large_capacity,
        multiple_endpoints=multiple_endpoints,
        tiering_enabled=tiering_enabled,
        cooling_threshold_days=cooling_threshold_days
    )
    if response['status'] == 'error':
        mcp.log_error(f"Error cloning volume: {response.get('message', 'Unknown error')}")
    return response
    
@mcp.tool(name = "List Volumes")
async def list_volumes_tool(
    project_id: str,
    location: str
) -> Dict[str, Any]:
    """
    Use this tool to list all volumes in a project and location.

    Args:
        project_id (str):
            Required. The ID of the project.
        location (str):
            Required. The location to list volumes from.

    Returns:
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': List of volumes (if successful)
            - 'message': Error message (if failed)

    Error Handling:
        If an error occurs while listing the volumes, the tool logs the error using `mcp.log_error()` and returns a response
        with "status": "error" and the error message.
    """    
    response = list_volumes(
        project_id=project_id,
        location=location
    )
    if response['status'] == 'error':
        mcp.log_error(f"Error listing volumes: {response['message']}")
    return response

@mcp.tool(name = "Create Snapshot")
async def create_snapshot_tool(
    project_id: str,
    location: str,
    volume_id: str,
    snapshot_id: str,
    description: str = None,
    labels: dict = None
) -> Dict[str, Any]:
    """
    Use this tool to create a near-instantaneous, space-efficient, read-only copy of an existing data volume, called a snapshot. 
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
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': API response object (if successful)
            - 'message': Error message (if failed)

    Error Handling:
        If an error occurs while creating the snapshot, the tool logs the error using `mcp.log_error()` and returns a response
        with "status": "error" and the error message.
    """
    response = create_snapshot(
        project_id=project_id,
        location=location,
        volume_id=volume_id,
        snapshot_id=snapshot_id,
        description=description,
        labels=labels
    )
    if response['status'] == 'error':
        mcp.log_error(f"Error creating snapshot: {response['message']}")
    return response
    
@mcp.tool(name = "List Snapshots")
async def list_snapshots_tool(
    project_id: str,
    location: str,
    volume_id: str
) -> Dict[str, Any]:
    """
    Use this tool to list all snapshots for a given volume.

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

    Error Handling:
        If an error occurs while listing the snapshots, the tool logs the error using `mcp.log_error()` and returns a response
        with "status": "error" and the error message.
    """
    response = list_snapshots(
            project_id=project_id,
            location=location,
            volume_id=volume_id
    )
    if response['status'] == 'error':
        mcp.log_error(f"Error listing snapshots: {response['message']}")
    return response

@mcp.tool(name = "Create Replication")
async def create_replication_tool(
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
) -> Dict[str, Any]:
    """
    Use this tool to create a replication for a volume.

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
        dict: Dictionary with keys
            - 'status': 'success' or 'error'
            - 'details': API response object (if successful)
            - 'message': Error message (if failed)
    
    Error Handling:
        If an error occurs while creating the replication, the tool logs the error using `mcp.log_error()` and returns a response
        with "status": "error" and the error message.
    """
    response = create_replication(
        source_project_id=source_project_id,
        source_location=source_location,
        source_volume_id=source_volume_id,
        replication_id=replication_id,
        replication_schedule=replication_schedule,
        destination_storage_pool=destination_storage_pool,
        destination_volume_id=destination_volume_id,
        destination_share_name=destination_share_name,
        destination_volume_description=destination_volume_description,
        tiering_enabled=tiering_enabled,
        cooling_threshold_days=cooling_threshold_days,
        description=description,
        labels=labels
    )
    if response['status'] == 'error':
        mcp.log_error(f"Error creating replication: {response['message']}")
    return response

# Register the MCP instance to run the tools
def main():
    """Main entry point for the GCNV MCP server."""
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()
# The module can be imported for testing and development purposes without executing the main logic