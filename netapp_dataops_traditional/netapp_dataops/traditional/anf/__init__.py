"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Module

This module provides functionality for managing Azure NetApp Files
through a clean, organized API structure.
"""

# Import all functions for easy access
from .volume_management import create_volume, clone_volume, delete_volume, list_volumes
from .snapshot_management import create_snapshot, delete_snapshot, list_snapshots
from .replication_management import create_replication, create_data_protection_volume
from .client import get_anf_client
from .base import _serialize

# Make all functions available at package level
__all__ = [
    "create_volume",
    "clone_volume", 
    "delete_volume",
    "list_volumes",
    "create_snapshot",
    "delete_snapshot",
    "list_snapshots",
    "create_replication",
    "create_data_protection_volume",
    "get_anf_client",
    "_serialize"
]