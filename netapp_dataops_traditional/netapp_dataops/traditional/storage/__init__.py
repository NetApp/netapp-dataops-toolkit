"""
Storage operations for NetApp DataOps traditional environments.

This package contains all traditional storage-related operations including
volume management, snapshots, SnapMirror, FlexCache, and resource listing.
"""

from .volume_operations import (
    create_volume,
    clone_volume, 
    delete_volume,
    mount_volume,
    unmount_volume,
    createVolume,
    cloneVolume,
    deleteVolume,
    mountVolume,
    unmountVolume
)

from .snapshot_operations import (
    create_snapshot,
    delete_snapshot,
    restore_snapshot,
    createSnapshot,
    deleteSnapshot,
    restoreSnapshot
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

from .list_operations import (
    list_volumes,
    list_snapshots,
    listVolumes,
    listSnapshots
)
