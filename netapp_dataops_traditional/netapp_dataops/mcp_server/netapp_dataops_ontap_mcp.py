#!/usr/bin/env python3

import asyncio
import logging
import sys
from typing import Optional

from fastmcp import FastMCP

from netapp_dataops.mcp_server.config import load_credentials
from netapp_dataops.logging_utils import setup_logger
from netapp_dataops.traditional.ontap import (
    clone_volume,
    create_flexcache,
    create_qtree,
    create_snap_mirror_relationship,
    create_snapshot,
    create_volume,
    get_flexcache_origin,
    get_qtree,
    get_qtree_metrics,
    list_flexcaches,
    list_qtrees,
    list_snap_mirror_relationships,
    list_snapshots,
    list_volumes,
    mount_volume,
    update_flexcache,
)


logger = setup_logger(__name__)

# Creates the FastMCP server instance
mcp = FastMCP("NetApp DataOps Traditional Toolkit MCP")


@mcp.tool(name="CreateVolume")
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
    snaplock_type: Optional[str] = None,
) -> None:
    """Provision a new data volume."""
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
            snaplock_type=snaplock_type,
        )
    except Exception as e:
        logger.error(f"Error creating volume: {e}")
        raise


@mcp.tool(name="CloneVolume")
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
    print_output: bool = False,
) -> None:
    """Create a FlexClone of an existing volume."""
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
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error cloning volume: {e}")
        raise


@mcp.tool(name="ListVolumes")
async def list_volumes_tool(
    check_local_mounts: bool = False,
    include_space_usage_details: bool = False,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    print_output: bool = False,
) -> list:
    """List existing data volumes."""
    try:
        volumes = list_volumes(
            check_local_mounts=check_local_mounts,
            include_space_usage_details=include_space_usage_details,
            cluster_name=cluster_name,
            svm_name=svm_name,
            print_output=print_output,
        )
        if volumes is None:
            return []
        return volumes
    except Exception as e:
        logger.error(f"Error listing volumes: {e}")
        raise


@mcp.tool(name="MountVolume")
async def mount_volume_tool(
    volume_name: str,
    mountpoint: str,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    mount_options: Optional[str] = None,
    lif_name: Optional[str] = None,
    readonly: bool = False,
    print_output: bool = False,
) -> None:
    """Mount an existing data volume locally."""
    try:
        mount_volume(
            volume_name=volume_name,
            cluster_name=cluster_name,
            svm_name=svm_name,
            mountpoint=mountpoint,
            mount_options=mount_options,
            lif_name=lif_name,
            readonly=readonly,
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error mounting volume: {e}")
        raise


@mcp.tool(name="CreateSnapshot")
async def create_snapshot_tool(
    volume_name: str,
    snapshot_name: Optional[str] = None,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    retention_count: int = 0,
    retention_days: bool = False,
    snapmirror_label: Optional[str] = None,
    print_output: bool = False,
) -> None:
    """Create a snapshot for a volume."""
    try:
        create_snapshot(
            volume_name=volume_name,
            snapshot_name=snapshot_name,
            cluster_name=cluster_name,
            svm_name=svm_name,
            retention_count=retention_count,
            retention_days=retention_days,
            snapmirror_label=snapmirror_label,
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        raise


@mcp.tool(name="ListSnapshots")
async def list_snapshots_tool(
    volume_name: str,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    print_output: bool = False,
) -> list:
    """List snapshots for a volume."""
    try:
        snapshots = list_snapshots(
            volume_name=volume_name,
            cluster_name=cluster_name,
            svm_name=svm_name,
            print_output=print_output,
        )
        if snapshots is None:
            return []
        return snapshots
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}")
        raise


@mcp.tool(name="CreateSnapMirrorRelationship")
async def create_snap_mirror_relationship_tool(
    source_svm: str,
    source_vol: str,
    target_vol: str,
    target_svm: Optional[str] = None,
    cluster_name: Optional[str] = None,
    schedule: str = "",
    policy: str = "MirrorAllSnapshots",
    action: Optional[str] = None,
    print_output: bool = False,
) -> None:
    """Create a SnapMirror relationship between volumes."""
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
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error creating snapmirror relationship: {e}")
        raise


@mcp.tool(name="ListSnapMirrorRelationships")
async def list_snap_mirror_relationships_tool(
    cluster_name: Optional[str] = None,
    print_output: bool = False,
) -> list:
    """List SnapMirror relationships where the destination resides on this system."""
    try:
        snap_mirror_relationships = list_snap_mirror_relationships(
            cluster_name=cluster_name,
            print_output=print_output,
        )
        if snap_mirror_relationships is None:
            return []
        return snap_mirror_relationships
    except Exception as e:
        logger.error(f"Error listing snapmirror relationships: {e}")
        raise


@mcp.tool(name="CreateFlexCache")
async def create_flexcache_tool(
    source_vol: str,
    source_svm: str,
    flexcache_vol: str,
    flexcache_svm: Optional[str] = None,
    cluster_name: Optional[str] = None,
    flexcache_size: Optional[str] = None,
    junction: Optional[str] = None,
    export_policy: str = "default",
    mountpoint: Optional[str] = None,
    readonly: bool = False,
    print_output: bool = False,
) -> None:
    """Create a FlexCache volume from a source volume."""
    try:
        create_flexcache(
            source_vol=source_vol,
            source_svm=source_svm,
            flexcache_vol=flexcache_vol,
            flexcache_svm=flexcache_svm,
            cluster_name=cluster_name,
            flexcache_size=flexcache_size,
            junction=junction,
            export_policy=export_policy,
            mountpoint=mountpoint,
            readonly=readonly,
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error creating FlexCache: {e}")
        raise


@mcp.tool(name="ListFlexCache")
async def list_flexcaches_tool(
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    print_output: bool = False,
) -> list:
    """List FlexCache volumes with origin details."""
    try:
        return list_flexcaches(
            cluster_name=cluster_name,
            svm_name=svm_name,
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error listing FlexCache origins: {e}")
        raise


@mcp.tool(name="GetFlexCacheOrigin")
async def get_flexcache_origin_tool(
    volume_name: str,
    svm_name: Optional[str] = None,
    cluster_name: Optional[str] = None,
    print_output: bool = False,
) -> list:
    """Retrieve origin details for a FlexCache volume."""
    try:
        return get_flexcache_origin(
            volume_name=volume_name,
            svm_name=svm_name,
            cluster_name=cluster_name,
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error getting FlexCache origin: {e}")
        raise


@mcp.tool(name="UpdateFlexCache")
async def update_flexcache_tool(
    uuid: Optional[str] = None,
    volume_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    cluster_name: Optional[str] = None,
    prepopulate_paths: Optional[list] = None,
    prepopulate_exclude_paths: Optional[list] = None,
    writeback_enabled: Optional[bool] = None,
    relative_size_enabled: Optional[bool] = None,
    relative_size_percentage: Optional[int] = None,
    atime_scrub_enabled: Optional[bool] = None,
    atime_scrub_period: Optional[int] = None,
    cifs_change_notify_enabled: Optional[bool] = None,
    print_output: bool = False,
) -> None:
    """Update an existing FlexCache volume."""
    try:
        update_flexcache(
            uuid=uuid,
            volume_name=volume_name,
            svm_name=svm_name,
            cluster_name=cluster_name,
            prepopulate_paths=prepopulate_paths,
            prepopulate_exclude_paths=prepopulate_exclude_paths,
            writeback_enabled=writeback_enabled,
            relative_size_enabled=relative_size_enabled,
            relative_size_percentage=relative_size_percentage,
            atime_scrub_enabled=atime_scrub_enabled,
            atime_scrub_period=atime_scrub_period,
            cifs_change_notify_enabled=cifs_change_notify_enabled,
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error updating FlexCache: {e}")
        raise


@mcp.tool(name="CreateQtree")
async def create_qtree_tool(
    qtree_name: str,
    volume_name: str,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    security_style: Optional[str] = None,
    unix_permissions: Optional[str] = None,
    export_policy: Optional[str] = None,
    print_output: bool = False,
) -> None:
    """Create a qtree within a volume."""
    try:
        create_qtree(
            qtree_name=qtree_name,
            volume_name=volume_name,
            cluster_name=cluster_name,
            svm_name=svm_name,
            security_style=security_style,
            unix_permissions=unix_permissions,
            export_policy=export_policy,
            print_output=print_output,
        )
    except Exception as e:
        logger.error(f"Error creating qtree: {e}")
        raise


@mcp.tool(name="ListQtrees")
async def list_qtrees_tool(
    volume_name: Optional[str] = None,
    cluster_name: Optional[str] = None,
    svm_name: Optional[str] = None,
    print_output: bool = False,
) -> list:
    """List qtrees in a volume or across an SVM."""
    try:
        qtrees = list_qtrees(
            volume_name=volume_name,
            cluster_name=cluster_name,
            svm_name=svm_name,
            print_output=print_output,
        )
        if qtrees is None:
            return []
        return qtrees
    except Exception as e:
        logger.error(f"Error listing qtrees: {e}")
        raise


@mcp.tool(name="GetQtree")
async def get_qtree_tool(
    volume_uuid: str,
    qtree_id: int,
    cluster_name: Optional[str] = None,
    print_output: bool = False,
) -> dict:
    """Retrieve properties for a specific qtree."""
    try:
        qtree_info = get_qtree(
            volume_uuid=volume_uuid,
            qtree_id=qtree_id,
            cluster_name=cluster_name,
            print_output=print_output,
        )
        return qtree_info
    except Exception as e:
        logger.error(f"Error getting qtree: {e}")
        raise


@mcp.tool(name="GetQtreeMetrics")
async def get_qtree_metrics_tool(
    volume_uuid: str,
    qtree_id: int,
    cluster_name: Optional[str] = None,
    print_output: bool = False,
) -> dict:
    """Retrieve historical performance metrics for a qtree."""
    try:
        metrics = get_qtree_metrics(
            volume_uuid=volume_uuid,
            qtree_id=qtree_id,
            cluster_name=cluster_name,
            print_output=print_output,
        )
        return metrics
    except Exception as e:
        logger.error(f"Error getting qtree metrics: {e}")
        raise


if __name__ == "__main__":
    try:
        load_credentials()

        if hasattr(mcp, "_tool_manager"):
            logger.info("Registered tools:")
            logger.info(asyncio.run(mcp._tool_manager.get_tools()))

        mcp.run(transport="stdio")
    except Exception as e:
        logging.error(f"Server startup failed: {e}")
        sys.exit(1)

