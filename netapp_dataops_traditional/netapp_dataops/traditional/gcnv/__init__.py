"""
Google Cloud NetApp Volumes (GCNV) operations for NetApp DataOps traditional environments.

This package contains all GCNV-related operations including volume operations,
snapshot operations, and replication operations for Google Cloud NetApp Volumes.
"""

from .volume_operations import (
    create_volume,
    clone_volume,
    delete_volume,
    list_volumes
)

from .snapshot_operations import (
    create_snapshot,
    delete_snapshot,
    list_snapshots
)

__all__ = [
    # Volume operations
    'create_volume',
    'clone_volume',
    'delete_volume',
    'list_volumes',
    
    # Snapshot operations
    'create_snapshot',
    'delete_snapshot',
    'list_snapshots',
]
