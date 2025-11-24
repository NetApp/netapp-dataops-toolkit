"""Storage operations for NetApp DataOps traditional environments."""

from .volume_operations import (
    create_volume,
    clone_volume, 
    delete_volume,
    mount_volume,
    unmount_volume,
    list_volumes
)

from .snapshot_operations import (
    create_snapshot,
    delete_snapshot,
    restore_snapshot,
    list_snapshots
)

from .snapmirror_operations import (
    list_snap_mirror_relationships,
    create_snap_mirror_relationship,
    sync_snap_mirror_relationship
)

from .flexcache_operations import (
    prepopulate_flex_cache,
    list_flexcache_origins,
    get_flexcache_origin,
    create_flexcache
)

__all__ = [
    # Volume operations
    'create_volume',
    'clone_volume',
    'delete_volume',
    'mount_volume',
    'unmount_volume',
    'list_volumes',
    # Snapshot operations
    'create_snapshot',
    'delete_snapshot',
    'restore_snapshot',
    'list_snapshots',
    # SnapMirror operations
    'list_snap_mirror_relationships',
    'create_snap_mirror_relationship',
    'sync_snap_mirror_relationship',
    # FlexCache operations
    'prepopulate_flex_cache',
    'list_flexcache_origins',
    'get_flexcache_origin',
    'create_flexcache',
]
