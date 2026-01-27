"""NetApp DataOps Toolkit for Traditional Environments import module."""

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

__version__ = "3.0.0"

from .exceptions import (
    InvalidConfigError,
    ConnectionTypeError,
    APIConnectionError,
    InvalidVolumeParameterError,
    InvalidSnapshotParameterError,
    MountOperationError,
    InvalidSnapMirrorParameterError,
    SnapMirrorSyncOperationError,
    CloudSyncSyncOperationError
)

# Import dataset exceptions
from .datasets.exceptions import (
    DatasetError,
    DatasetNotFoundError,
    DatasetExistsError,
    DatasetConfigError,
    DatasetVolumeError
)

# Import volume operations from ontap package
from .ontap.volume_operations import (
    clone_volume,
    create_volume,
    delete_volume,
    mount_volume,
    unmount_volume,
    list_volumes
)

from .ontap.snapshot_operations import (
    create_snapshot,
    delete_snapshot,
    restore_snapshot,
    list_snapshots
)

from .ontap.snapmirror_operations import (
    list_snap_mirror_relationships,
    create_snap_mirror_relationship,
    sync_snap_mirror_relationship
)

from .data_movement.cloud_sync_operations import (
    list_cloud_sync_relationships,
    sync_cloud_sync_relationship
)

from .data_movement.s3_operations import (
    pull_bucket_from_s3,
    pull_object_from_s3,
    push_directory_to_s3,
    push_file_to_s3
)

from .ontap.flexcache_operations import (
    prepopulate_flex_cache
)

__all__ = [
    '__version__',
    'InvalidConfigError',
    'ConnectionTypeError',
    'APIConnectionError',
    'InvalidVolumeParameterError',
    'InvalidSnapshotParameterError',
    'MountOperationError',
    'InvalidSnapMirrorParameterError',
    'SnapMirrorSyncOperationError',
    'CloudSyncSyncOperationError',
    'clone_volume',
    'create_volume',
    'delete_volume',
    'mount_volume',
    'unmount_volume',
    'list_volumes',
    'create_snapshot',
    'delete_snapshot',
    'restore_snapshot',
    'list_snapshots',
    'list_snap_mirror_relationships',
    'create_snap_mirror_relationship',
    'sync_snap_mirror_relationship',
    'list_cloud_sync_relationships',
    'sync_cloud_sync_relationship',
    'pull_bucket_from_s3',
    'pull_object_from_s3',
    'push_directory_to_s3',
    'push_file_to_s3',
    'prepopulate_flex_cache',
]

_lazy_modules = {}


def __getattr__(name):
    """Lazy import pattern for optional cloud provider modules.
    
    This allows gcnv module to be imported only when accessed, avoiding
    unnecessary dependencies for users who don't need cloud functionality.
    
    Args:
        name: The attribute name being accessed
        
    Returns:
        The requested module if available
        
    Raises:
        ImportError: If required dependencies are not installed
        AttributeError: If the attribute does not exist
    """
    if name == "gcnv":
        if name in _lazy_modules:
            return _lazy_modules[name]
            
        try:
            from google.cloud import netapp_v1  # noqa: F401
            from . import gcnv
            _lazy_modules[name] = gcnv
            return gcnv
        except ImportError as e:
            raise ImportError(
                "Google Cloud NetApp Volumes support requires 'google-cloud-netapp'. "
                "Install with: pip install 'netapp-dataops-traditional[gcp]'"
            ) from e
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

