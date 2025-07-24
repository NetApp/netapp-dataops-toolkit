#!/usr/bin/env python3

import logging
import sys
import asyncio
from typing import Optional
from fastmcp import FastMCP
from netapp_dataops.mcp_server.config import load_credentials
from netapp_dataops.traditional import (
    create_volume, 
    clone_volume, 
    list_volumes, 
    mount_volume, 
    create_snapshot, 
    list_snapshots, 
    create_snap_mirror_relationship, 
    list_snap_mirror_relationships
)

mcp = FastMCP("NetApp DataOps Traditional Toolkit MCP")

@mcp.tool(name="Create Volume")
async def create_volume_tool(
    volume_name: str,
    volume_size: str,
    guarantee_space: bool = False,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    volume_type: str = "flexvol",
    unix_permissions: str = "0777",
    unix_uid: str = "0",
    unix_gid: str = "0",
    export_policy: str = "default",
    snapshot_policy: str = "none",
    aggregate: Optional[str] = None,
    mountpoint: Optional[str] = None,
    junction: Optional[str] = None,
    readonly: bool = False,
    print_output: bool = False,
    tiering_policy: Optional[str] = None,
    vol_dp: bool = False,
    snaplock_type: Optional[str] = None
) -> None:
    """
    Use this tool to rapidly provision a new data volume.

    Args:
        volume_name (str): Name of the new volume (required).
        volume_size (str): Size of the new volume (required). Format: '1024MB', '100GB', '10TB', etc.
        guarantee_space (bool): Guarantee sufficient storage space for the full capacity of the volume (i.e., do not use thin provisioning). Defaults to False.
        cluster_name (str): Non-default cluster name, same credentials as the default credentials should be used. Defaults to None.
        svm_name (str): Non-default SVM name, same credentials as the default credentials should be used. Defaults to None.
        volume_type (str): Volume type can be flexvol (default) or flexgroup. Defaults to "flexvol".
        unix_permissions (str): Unix filesystem permissions to apply when creating the new volume (e.g., '0777' for full read/write permissions for all users and groups). Defaults to "0777".
        unix_uid (str): Unix filesystem user ID (uid) to apply when creating the new volume (e.g., '0' for root user). Defaults to "0".
        unix_gid (str): Unix filesystem group ID (gid) to apply when creating the new volume (e.g., '0' for root group). Defaults to "0".
        export_policy (str): NFS export policy to use when exporting the new volume. Defaults to "default".
        snapshot_policy (str): Snapshot policy to apply for the new volume. Defaults to "none".
        aggregate (str): Aggregate name or comma-separated aggregates for flexgroup. Defaults to None.
        mountpoint (str): Local mountpoint to mount the new volume at. If not specified, the volume will not be mounted locally. On Linux hosts - if specified, the calling program must be run as root. Defaults to None.
        junction (str): Custom junction path for the volume to be exported at. If not specified, the junction path will be: ("/"+Volume Name). Defaults to None.
        readonly (bool): Mount the volume locally as "read-only." If not specified, the volume will be mounted as "read-write". On Linux hosts - if specified, the calling program must be run as root. Defaults to False.
        print_output (bool): Denotes whether or not to print messages to the console during execution. Defaults to False.
        tiering_policy (str): For fabric pool-enabled systems, the tiering policy can be: none, auto, snapshot-only, all. Defaults to None.
        vol_dp (bool): Create the volume as type DP, which can be used as a SnapMirror destination. Defaults to False.
        snaplock_type (str): SnapLock type to apply for the new volume (e.g., 'compliance' or 'enterprise'). Defaults to None.

    Returns:
        None.
    """
    try:
        create_volume(
            volume_name=volume_name,
            volume_size=volume_size,
            guarantee_space=guarantee_space,
            cluster_name=cluster_name,
            svm_name=svm_name,
            volume_type=volume_type,
            unix_permissions=unix_permissions,
            unix_uid=unix_uid,
            unix_gid=unix_gid,
            export_policy=export_policy,
            snapshot_policy=snapshot_policy,
            aggregate=aggregate,
            mountpoint=mountpoint,
            junction=junction,
            readonly=readonly,
            print_output=print_output,
            tiering_policy=tiering_policy,
            vol_dp=vol_dp,
            snaplock_type=snaplock_type
        )
    except Exception as e:
        print(f"Error creating volume: {e}")
        raise


@mcp.tool(name="Clone Volume")
async def clone_volume_tool(
    new_volume_name: str,
    source_volume_name: str,
    cluster_name: Optional[str] = None,
    source_snapshot_name: Optional[str] = None,
    source_svm: Optional[str] = None,
    target_svm: Optional[str] = None,
    export_hosts: Optional[str] = None,
    export_policy: Optional[str] = None,
    snapshot_policy: Optional[str] = None,
    split: bool = False,
    unix_uid: Optional[str] = None,
    unix_gid: Optional[str] = None,
    mountpoint: Optional[str] = None,
    junction: Optional[str] = None,
    readonly: bool = False,
    refresh: bool = False,
    svm_dr_unprotect: bool = False,
    print_output: bool = False
) -> None:
    """
    Use this tool to near-instantaneously create a new data volume that is an exact copy of an existing volume. 
    This functionality utilizes NetApp FlexClone technology, ensuring that any clones created will be extremely storage-space-efficient. 
    Aside from metadata, a clone will not consume additional storage space until its contents start to deviate from the source volume.

    Args:
        new_volume_name (str): Name of the new cloned volume (required).
        source_volume_name (str): Name of the volume to be cloned (required).
        cluster_name (str): Non-default cluster name, same credentials as the default credentials should be used. Defaults to None.
        source_snapshot_name (str): Name of the snapshot to be cloned. If suffixed by '*', the latest snapshot starting with the prefix will be used (e.g., 'daily*'). Defaults to None.
        source_svm (str): Name of the SVM hosting the volume to be cloned. Defaults to the default SVM if not provided.
        target_svm (str): Name of the SVM hosting the clone. Defaults to the source SVM if not provided.
        export_hosts (str): Colon-separated hosts/CIDRs for export. Hosts will be exported for read-write and root access. Defaults to None.
        export_policy (str): Export policy name to attach to the volume. Default policy will be used if export-hosts/export-policy is not provided. Defaults to None.
        snapshot_policy (str): Name of an existing snapshot policy to configure on the volume. Defaults to None.
        split (bool): Start clone split after creation. Defaults to False.
        unix_uid (str): Unix filesystem user ID (uid) to apply when creating the new volume. Defaults to the source volume's uid. Cannot apply uid of '0' when creating a clone. Defaults to None.
        unix_gid (str): Unix filesystem group ID (gid) to apply when creating the new volume. Defaults to the source volume's gid. Cannot apply gid of '0' when creating a clone. Defaults to None.
        mountpoint (str): Local mountpoint to mount the new volume. If not specified, the volume will not be mounted locally. On Linux hosts, if specified, the calling program must be run as root. Defaults to None.
        junction (str): Custom junction path for the volume to be exported at. Defaults to "/<Volume Name>" if not specified. Defaults to None.
        readonly (bool): Option to mount the volume locally as "read-only." Defaults to "read-write" if not specified. On Linux hosts, if specified, the calling program must be run as root. Defaults to False.
        refresh (bool): If true, a previous clone using this name will be deleted prior to the new clone creation. Defaults to False.
        svm_dr_unprotect (bool): Marks the clone to be excluded from SVM-DR replication when configured on the clone SVM. Defaults to False.
        print_output (bool): Prints logs to the console. Defaults to False.

    Returns:
        None
    """
    try:
        clone_volume(
            new_volume_name=new_volume_name,
            source_volume_name=source_volume_name,
            cluster_name=cluster_name,
            source_snapshot_name=source_snapshot_name,
            source_svm=source_svm,
            target_svm=target_svm,
            export_hosts=export_hosts,
            export_policy=export_policy,
            snapshot_policy=snapshot_policy,
            split=split,
            unix_uid=unix_uid,
            unix_gid=unix_gid,
            mountpoint=mountpoint,
            junction=junction,
            readonly=readonly,
            refresh=refresh,
            svm_dr_unprotect=svm_dr_unprotect,
            print_output=print_output
        )
    except Exception as e:
        print(f"Error cloning volume: {e}")
        raise


@mcp.tool(name="List Volumes")
async def list_volumes_tool(
    check_local_mounts: bool = False,
    include_space_usage_details: bool = False,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    print_output: bool = False
) -> list:
    """
    Use this tool to retrieve a list of all existing data volumes.

    Args:
        check_local_mounts (bool): If set to true, the local mountpoints of any mounted volumes will be included in the returned list and printed output. Defaults to False.
        cluster_name (str): Non-default cluster name, same credentials as the default credentials should be used. Defaults to None.
        svm_name (str): Non-default SVM name, same credentials as the default credentials should be used. Defaults to None.
        print_output (bool): Denotes whether or not to print messages to the console during execution. Defaults to False.

        include_space_usage_details (bool): Include storage space usage details in the output. Defaults to False. 
        If set to True, then four additional fields will be included in the output: 'Snap Reserve', 'Capacity', 'Usage', and 'Footprint'. 
        These fields and their relation to the 'Size' field are explained below:
        - Size: The logical size of the volume.
        - Snap Reserve: The percentage of the volume's logical size that is reserved for snapshot copies.
        - Capacity: The logical capacity that is available for users of the volume to store data in.
        - Usage: The combined logical size of all of the files that are stored on the volume.
        - Footprint: The actual on-disk storage space that is being consumed by the volume after all ONTAP storage efficiencies are taken into account.

    Returns:
        A list of all existing volumes. Each item in the list will be a dictionary containing details regarding a specific volume.
    """
    try:
        volumes = list_volumes(
            check_local_mounts=check_local_mounts,
            include_space_usage_details=include_space_usage_details,
            cluster_name=cluster_name,
            svm_name=svm_name,
            print_output=print_output
        )
        if volumes is None:
            return []
        return volumes
    except Exception as e:
        print(f"Error listing volumes: {e}")
        raise


@mcp.tool(name="Mount Volume")
async def mount_volume_tool(
    volume_name: str,          
    mountpoint: str,            
    cluster_name: Optional[str] = None,   
    svm_name: Optional[str] = None,      
    mount_options: Optional[str] = None,  
    lif_name: Optional[str] = None,
    readonly: bool = False,     
    print_output: bool = False  
) -> None:

    """
    Use this tool to mount an existing data volume as "read-only" or "read-write" on your local host as part of any Python program or workflow. 
    On Linux hosts, mounting requires root privileges, so any Python program that invokes this function must be run as root. 
    It is usually not necessary to invoke this function as root on macOS hosts.

    Args:
        volume_name (str): Name of the volume (required).
        mountpoint (str): Local mountpoint to mount the volume at (required).
        cluster_name (str): Non-default cluster name, same credentials as the default credentials should be used. Defaults to None.
        svm_name (str): Non-default SVM name, same credentials as the default credentials should be used. Defaults to None.
        mount_options (str): Specify custom NFS mount options. Defaults to None.
        lif_name(str): Non-default lif (nfs server ip/name). Defaults to None.
        readonly (bool): Option to mount the volume locally as "read-only." If not specified volume will be mounted as "read-write". On Linux hosts, if specified, the calling program must be run as root. Defaults to False.
        print_output (bool): Denotes whether or not to print messages to the console during execution. Defaults to False.

    Returns:
        None
    """
    try:
        mount_volume(
            volume_name=volume_name,
            cluster_name=cluster_name,
            svm_name=svm_name,
            mountpoint=mountpoint,
            mount_options=mount_options,
            lif_name=lif_name,
            readonly=readonly,
            print_output=print_output
        )
    except Exception as e:
        print(f"Error mounting volume: {e}")
        raise


@mcp.tool(name="Create Snapshot")
async def create_snapshot_tool(
    volume_name: str,                    
    snapshot_name: Optional[str] = None,           
    cluster_name: Optional[str] = None,            
    svm_name: Optional[str] = None,                
    retention_count: int = 0,            
    retention_days: bool = False,        
    snapmirror_label: Optional[str] = None,        
    print_output: bool = False
) -> None:
    
    """
    Use this tool to create a near-instantaneous, space-efficient, read-only copy of an existing data volume, called a snapshot. 
    Snapshots are particularly useful for versioning datasets and implementing dataset-to-model traceability.

    Args:
        volume_name (str): Name of the volume (required).
        snapshot_name (str): Name of the new snapshot. If not specified, will be set to 'netapp_dataops_<timestamp>'. If retention is specified, snapshot name will be the prefix for the snapshot. Defaults to None.
        cluster_name (str): Non-default cluster name, same credentials as the default credentials should be used. Defaults to None.
        svm_name (str): Non-default SVM name, same credentials as the default credentials should be used. Defaults to None.
        retention_count (int): The number of snapshots to keep. Excessive snapshots will be deleted. Defaults to 0.
        retention_days (bool): When true, the retention count will represent the number of days to retain snapshots. Defaults to False.
        snapmirror_label (str): When provided, the snapmirror label will be set on the snapshot created. This is useful when the volume is a source for vault snapmirror. Defaults to None.
        print_output (bool): Denotes whether or not to print messages to the console during execution. Defaults to False.

    Returns:
        None
    """
    try:
        create_snapshot(
            volume_name=volume_name,
            snapshot_name=snapshot_name,
            cluster_name=cluster_name,
            svm_name=svm_name,
            retention_count=retention_count,
            retention_days=retention_days,
            snapmirror_label=snapmirror_label,
            print_output=print_output
        )
    except Exception as e:
        print(f"Error creating snapshot: {e}")
        raise


@mcp.tool(name="List Snapshots")
async def list_snapshots_tool(
    volume_name: str,            
    cluster_name: Optional[str] = None,    
    svm_name: Optional[str] = None,            
    print_output: bool = False  
) -> list :
    
    """
    Use this tool to retrieve a list of all existing snapshots for a specific data volume. 
    Snapshots are space-efficient, read-only copies of a volume at a specific point in time. 

    Args:
        volume_name (str): Name of the volume (required).
        cluster_name (str): Non-default cluster name, same credentials as the default credentials should be used. Defaults to None.
        svm_name (str): Non-default SVM name, same credentials as the default credentials should be used. Defaults to None.
        print_output (bool): Denotes whether or not to print messages to the console during execution. Defaults to False.

    Returns:
        A list of all existing snapshots for the specific data volume.
        Each item in the list will be a dictionary containing details regarding a specific snapshot. 
        The keys for the values in this dictionary are "Snapshot Name", "Create Time".
    """
    try:
        snapshots = list_snapshots(volume_name=volume_name, cluster_name=cluster_name, svm_name=svm_name, print_output=print_output)
        if snapshots is None:
            return []
        return snapshots
    except Exception as e:
        print(f"Error listing snapshots: {e}")
        raise


@mcp.tool(name="Create SnapMirror Relationship")
async def create_snap_mirror_relationship_tool(
    source_svm: str,                    
    source_vol: str,                    
    target_vol: str,                    
    target_svm: Optional[str] = None,             
    cluster_name: Optional[str] = None,           
    schedule: str = '',                 
    policy: str = 'MirrorAllSnapshots', 
    action: Optional[str] = None,                 
    print_output: bool = False          
) -> None:
    
    """
    Use this tool to create a SnapMirror relationship between a source volume and a target volume. 
    SnapMirror is a NetApp technology used for efficient data replication between storage systems. 
    This tool is particularly useful for replicating data for various purposes, including but not limited to AI/ML model training or retraining, disaster recovery, or data migration. 
    It can also be used to initialize new replication relationships or resynchronize existing ones.

    Args:
        source_svm (str): Name of the SVM hosting the source volume (required).
        source_vol (str): Name of the source volume to replicate (required).
        target_vol (str): Name of the target volume to replicate to (required). If not provided, the default SVM will be used.
        target_svm (str): Name of the SVM hosting the target volume. Defaults to None.
        cluster_name (str): Non-default cluster name. Same credentials as the default credentials should be used. Defaults to None.
        schedule (str): Name of the schedule to use. If not provided, no schedule will be provided. Defaults to an empty string.
        policy (str): SnapMirror policy to use. Defaults to 'MirrorAllSnapshots'.
        action (str): Action to perform after creating the SnapMirror relationship. Can be 'initialize' (to start new replication, requires destination volume to be of DP type) or 'resync' (to resynchronize volumes with a common snapshot). Defaults to None.
        print_output (bool): Denotes whether or not to print messages to the console during execution. Defaults to False.

    Returns:
        None
    """
    try:
        create_snap_mirror_relationship(
            source_svm=source_svm,
            source_vol=source_vol,
            target_vol=target_vol,
            target_svm=target_svm,
            cluster_name=cluster_name,
            schedule=schedule,
            policy=policy,
            action=action,
            print_output=print_output
        )
    except Exception as e:
        print(f"Error creating snapmirror relationship: {e}")
        raise


@mcp.tool(name="List SnapMirror Relationships")
async def list_snap_mirror_relationships_tool(
    cluster_name: Optional[str] = None,          
    print_output: bool = False  
) -> list:
    
    """
    Use this tool to retrieve a list of all existing SnapMirror relationships for which the destination volume resides on the user's storage system. 

    Args:
        cluster_name (str): Non-default cluster name, same credentials as the default credentials should be used. Defaults to None.
        print_output (bool): Denotes whether or not to print messages to the console during execution. Defaults to False.

    Returns:
        A list of all existing SnapMirror relationships for which the destination volume resides on the user's storage system. 
        Each item in the list will be a dictionary containing details regarding a specific SnapMirror relationship. 
        The keys for the values in this dictionary are "UUID", "Type", "Healthy", "Current Transfer Status", "Source Cluster", "Source SVM", "Source Volume", "Dest Cluster", "Dest SVM", "Dest Volume".
    """
    try:
        snap_mirror_relationships = list_snap_mirror_relationships(
            cluster_name=cluster_name,
            print_output=print_output
        )
        if snap_mirror_relationships is None:
            return []
        return snap_mirror_relationships
    except Exception as e:
        print(f"Error listing snapmirror relationships: {e}")
        raise



if __name__ == "__main__":

    try:
        # Validates the configuration
        load_credentials()

        # Sets up basic logging to capture server events and errors
        logging.basicConfig(level=logging.INFO)

        if hasattr(mcp, '_tool_manager'):
            logging.info("Registered tools:") 
            logging.info(asyncio.run(mcp._tool_manager.get_tools()))

        # Starts the MCP server using stdio transport for local operation
        mcp.run(transport="stdio")

    except Exception as e:
        # Logs and prints any startup errors, then exits with an error code
        logging.error(f"Server startup failed: {e}")
        sys.exit(1)

