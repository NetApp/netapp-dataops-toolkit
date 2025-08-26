"""
Storage operations for NetApp DataOps traditional environments.

This package contains all traditional storage-related operations including
volume management (with listing), snapshots (with listing), SnapMirror, and FlexCache.
"""

from .volume_operations import (
    create_volume,
    clone_volume, 
    delete_volume,
    mount_volume,
    unmount_volume,
    list_volumes,
    createVolume,
    cloneVolume,
    deleteVolume,
    mountVolume,
    unmountVolume,
    listVolumes
)

from .snapshot_operations import (
    create_snapshot,
    delete_snapshot,
    restore_snapshot,
    list_snapshots,
    createSnapshot,
    deleteSnapshot,
    restoreSnapshot,
    listSnapshots
)

from .snapmirror_operations import (
    list_snap_mirror_relationships,
    create_snap_mirror_relationship,
    sync_snap_mirror_relationship,
    listSnapMirrorRelationships,
    syncSnapMirrorRelationship
)

from .flexcache_operations import (
    prepopulate_flex_cache,
    prepopulateFlexCache
)
