"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Module

This module provides functionality for managing Azure NetApp Files
through a clean, organized API structure.
"""

# Import all functions for easy access
from .volume_management import create_volume, clone_volume, delete_volume, list_volumes
from .snapshot_management import create_snapshot, delete_snapshot, list_snapshots
from .replication_management import create_replication
from .config import create_anf_config


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
    "create_anf_config"
]
