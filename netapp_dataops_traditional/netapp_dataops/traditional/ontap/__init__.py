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
    list_flexcaches,
    get_flexcache_origin,
    update_flexcache,
    create_flexcache
)

from ..protocols.cifs_share_operations import (
    create_cifs_share,
    list_cifs_shares,
    get_cifs_share
)

from .qtree_operations import (
    create_qtree,
    list_qtrees,
    get_qtree,
    get_qtree_metrics
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
    'list_flexcaches',
    'get_flexcache_origin',
    'update_flexcache',
    'create_flexcache',
    # CIFS Share operations
    'create_cifs_share',
    'list_cifs_shares',
    'get_cifs_share',
    # Qtree operations
    'create_qtree',
    'list_qtrees',
    'get_qtree',
    'get_qtree_metrics',
]
