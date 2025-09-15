"""
Dataset class for NetApp DataOps traditional environments.

This module provides the Dataset class that abstracts ONTAP volume management
into a simple dataset interface for Data Engineers and Data Scientists.
"""

import os
import datetime
import re
from typing import List, Dict, Optional, Any
from pathlib import Path

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Volume as NetAppVolume
from netapp_ontap.resources import Snapshot as NetAppSnapshot

from ..exceptions import (
    InvalidConfigError,
    ConnectionTypeError,
    APIConnectionError,
    InvalidVolumeParameterError,
    InvalidSnapshotParameterError
)
from ..core import (
    _retrieve_config,
    _instantiate_connection,
    _print_invalid_config_error,
    _convert_bytes_to_pretty_size,
    _convert_size_string_to_bytes,
    _sizes_are_equivalent
)
from ..ontap.volume_operations import (
    create_volume,
    clone_volume,
    delete_volume,
    list_volumes
)
from ..ontap.snapshot_operations import (
    create_snapshot,
    list_snapshots
)
from .exceptions import (
    DatasetError,
    DatasetNotFoundError,
    DatasetExistsError,
    DatasetConfigError,
    DatasetVolumeError
)


class Dataset:
    """
    A Dataset abstraction that maps to an ONTAP volume.
    
    This class provides a simple interface for managing datasets (collections of files)
    backed by ONTAP volumes. Datasets are accessed through a pre-mounted root volume
    that provides local file system access to the underlying ONTAP storage.
    """
    
    def __init__(self, name: str, max_size: Optional[str] = None, print_output: bool = False):
        """
        Initialize a Dataset instance.
        
        Args:
            name: The name of the dataset
            max_size: Maximum size for new datasets (e.g., "100GB")
            print_output: Whether to print status messages
            
        Raises:
            DatasetConfigError: If dataset manager is not configured
            DatasetVolumeError: If there's an issue with the underlying volume
        """
        self.name = name
        self.print_output = print_output
        self._config = None
        self._root_volume_name = None
        self._root_mountpoint = None
        self._root_export_policy = None
        
        # Initialize configuration
        self._initialize_config()
        
        # Check if dataset already exists
        existing_volume = self._find_dataset_volume()
        
        if existing_volume:
            # Bind to existing dataset
            self._bind_to_existing(existing_volume, max_size)
        else:
            # Create new dataset
            if max_size is None:
                raise DatasetError(f"max_size must be specified when creating new dataset '{name}'")
            self._create_new_dataset(max_size)
    
    def _initialize_config(self):
        """Initialize dataset manager configuration."""
        try:
            self._config = _retrieve_config(print_output=self.print_output)
        except InvalidConfigError:
            raise DatasetConfigError("Invalid or missing configuration file")
        
        # Check for dataset manager configuration - support both old and new config formats
        dataset_manager_enabled = self._config.get("datasetManagerEnabled", False)
        if not dataset_manager_enabled:
            raise DatasetConfigError(
                "Dataset manager is not enabled. Run 'netapp_dataops_cli.py config' to configure."
            )
        
        self._root_volume_name = self._config.get("datasetManagerRootVolume")
        self._root_mountpoint = self._config.get("datasetManagerRootMountpoint")
        
        if not self._root_volume_name or not self._root_mountpoint:
            raise DatasetConfigError(
                "Dataset manager root volume and mountpoint must be configured. "
                "Run 'netapp_dataops_cli.py config' to configure."
            )
        
        # Validate that the root volume actually exists and is properly configured
        self._validate_root_volume()
    
    def _validate_root_volume(self):
        """Validate that the root volume exists in ONTAP and is properly junctioned.
        
        Also captures the root volume's export policy to ensure new dataset volumes
        inherit the same NFS access permissions for consistent traversal.
        """
        try:
            volumes = list_volumes(print_output=False)
            root_volume = None
            
            for volume in volumes:
                if volume.get("Volume Name") == self._root_volume_name:
                    root_volume = volume
                    break
            
            if not root_volume:
                raise DatasetConfigError(
                    f"Root volume '{self._root_volume_name}' does not exist in ONTAP. "
                    "Please create it or update your configuration."
                )
            
            # Check junction path exists
            junction_path = root_volume.get("Junction Path")
            if not junction_path:
                raise DatasetConfigError(
                    f"Root volume '{self._root_volume_name}' is not junctioned. "
                    "Please junction it to make datasets accessible locally."
                )
            
            # Verify local mountpoint exists and is accessible
            if not os.path.exists(self._root_mountpoint):
                raise DatasetConfigError(
                    f"Root mountpoint '{self._root_mountpoint}' does not exist locally. "
                    "Please mount the root volume or update your configuration."
                )
            
            # Verify the mountpoint is actually accessible (not just an empty directory)
            if not os.access(self._root_mountpoint, os.R_OK | os.W_OK):
                raise DatasetConfigError(
                    f"Root mountpoint '{self._root_mountpoint}' is not accessible. "
                    "Please check mount status and permissions."
                )
            
            # Store the root volume's export policy for new dataset volumes
            self._root_export_policy = root_volume.get("Export Policy")
            if not self._root_export_policy:
                # Fall back to "default" if no export policy is explicitly set
                self._root_export_policy = "default"
                if self.print_output:
                    print(f"Warning: Root volume has no explicit export policy, using 'default' for new datasets")
                
        except Exception as e:
            if isinstance(e, DatasetConfigError):
                raise
            raise DatasetConfigError(f"Failed to validate root volume: {str(e)}")
    
    def _find_dataset_volume(self) -> Optional[Dict[str, Any]]:
        """Find the volume corresponding to this dataset."""
        try:
            volumes = list_volumes(print_output=False)
            existing_volume = None
            
            # First, check if a volume with this name exists anywhere
            for volume in volumes:
                if volume.get("Volume Name") == self.name:
                    existing_volume = volume
                    break
            
            if existing_volume:
                # Volume exists - check if it's in the right location
                expected_junction = f"/{self._root_volume_name}/{self.name}"
                actual_junction = existing_volume.get("Junction Path")
                
                if actual_junction == expected_junction:
                    # Volume exists and is correctly managed by Dataset Manager
                    return existing_volume
                else:
                    # Volume exists but is not under Dataset Manager control
                    junction_info = f"junction: {actual_junction}" if actual_junction else "no junction path"
                    raise DatasetExistsError(
                        f"Volume '{self.name}' already exists but is not managed by the Dataset Manager "
                        f"({junction_info}). Please use a different name or move the existing volume to be "
                        f"managed under '{expected_junction}'."
                    )
            
            # No volume with this name exists - safe to create
            return None
            
        except DatasetExistsError:
            # Re-raise our specific error
            raise
        except Exception as e:
            raise DatasetVolumeError(f"Failed to search for dataset volume: {str(e)}")
    
    def _is_volume_clone(self, volume: Dict[str, Any]) -> bool:
        """
        Robustly determine if a volume is a clone using the same approach as volume_operations.py.
        
        Uses try/except to check for existence of clone parent fields rather than 
        comparing Clone field values, avoiding type safety issues with different 
        API response formats.
        """
        try:
            # If we can access clone parent fields, it's a clone
            # This matches the pattern used in volume_operations.py list_volumes()
            parent_svm = volume.get("Clone Parent SVM") or volume.get("Source SVM")
            parent_volume = volume.get("Clone Parent Volume") or volume.get("Source Volume") 
            
            # If either parent field exists and has a value, it's a clone
            if parent_svm or parent_volume:
                return True
            
            return False
        except:
            # Any error means not a clone (safe default)
            return False
    
    def _bind_to_existing(self, volume: Dict[str, Any], max_size: Optional[str]):
        """Bind to an existing dataset volume."""
        self.max_size = volume.get("Size")
        self.is_clone = self._is_volume_clone(volume)
        self.source_dataset_name = volume.get("Clone Parent Volume") if self.is_clone else None
        self.local_file_path = os.path.join(self._root_mountpoint, self.name)
        
        # Validate max_size if provided - use normalized comparison
        if max_size and not _sizes_are_equivalent(max_size, self.max_size):
            raise DatasetError(
                f"Specified max_size '{max_size}' does not match existing volume size '{self.max_size}'. "
                "Remove max_size parameter to bind to existing dataset."
            )
        
        if self.print_output:
            print(f"Bound to existing dataset '{self.name}'")
    
    def _create_new_dataset(self, max_size: str):
        """Create a new dataset volume."""
        try:
            # Calculate junction path
            junction_path = f"/{self._root_volume_name}/{self.name}"
            
            # Create the volume with the same export policy as the root volume
            create_volume(
                volume_name=self.name,
                volume_size=max_size,
                junction=junction_path,
                export_policy=self._root_export_policy,
                print_output=self.print_output
            )
            
            # Set attributes
            self.max_size = max_size
            self.is_clone = False
            self.source_dataset_name = None
            self.local_file_path = os.path.join(self._root_mountpoint, self.name)
            
            if self.print_output:
                print(f"Created new dataset '{self.name}' with size '{max_size}' using export policy '{self._root_export_policy}'")
                
        except Exception as e:
            raise DatasetVolumeError(f"Failed to create dataset '{self.name}': {str(e)}")
    
    def get_files(self) -> List[Dict[str, Any]]:
        """
        Get a list of all files in the dataset.
        
        Returns:
            List of dictionaries containing file information:
            - filename: Name of the file
            - filepath: Full path to the file
            - size: File size in bytes
            - size_human: Human-readable file size
        """
        files = []
        try:
            if not os.path.exists(self.local_file_path):
                return files
                
            for root, dirs, filenames in os.walk(self.local_file_path):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'size_human': _convert_bytes_to_pretty_size(stat.st_size)
                    })
        except Exception as e:
            raise DatasetError(f"Failed to list files in dataset: {str(e)}")
        
        return files
    
    def clone(self, name: str) -> 'Dataset':
        """
        Create a clone of this dataset.
        
        Args:
            name: Name for the cloned dataset
            
        Returns:
            New Dataset instance representing the clone
            
        Raises:
            DatasetExistsError: If a dataset with the given name already exists
            DatasetVolumeError: If the clone operation fails
        """
        # Check if clone already exists
        existing_clone = Dataset._check_dataset_exists(name)
        if existing_clone:
            raise DatasetExistsError(f"Dataset '{name}' already exists")
        
        try:
            # Calculate junction path for clone
            junction_path = f"/{self._root_volume_name}/{name}"
            
            # Clone the volume
            clone_volume(
                new_volume_name=name,
                source_volume_name=self.name,
                junction=junction_path,
                export_policy=self._root_export_policy,
                print_output=self.print_output
            )
            
            if self.print_output:
                print(f"Created clone '{name}' from dataset '{self.name}'")
            
            # Return new Dataset instance for the clone
            return Dataset(name=name, print_output=self.print_output)
            
        except Exception as e:
            raise DatasetVolumeError(f"Failed to clone dataset '{self.name}' to '{name}': {str(e)}")
    
    def snapshot(self, name: Optional[str] = None) -> str:
        """
        Create a snapshot of the dataset.
        
        Args:
            name: Optional name for the snapshot. If not provided, a timestamp-based name is used.
            
        Returns:
            The name of the created snapshot
            
        Raises:
            DatasetVolumeError: If the snapshot operation fails
        """
        try:
            snapshot_name = create_snapshot(
                volume_name=self.name,
                snapshot_name=name,
                print_output=self.print_output
            )
            
            if self.print_output:
                print(f"Created snapshot '{snapshot_name}' for dataset '{self.name}'")
            
            return snapshot_name
            
        except Exception as e:
            raise DatasetVolumeError(f"Failed to create snapshot for dataset '{self.name}': {str(e)}")
    
    def get_snapshots(self) -> List[Dict[str, Any]]:
        """
        Get a list of all snapshots for this dataset.
        
        Returns:
            List of dictionaries containing snapshot information:
            - name: Snapshot name
            - create_time: Snapshot creation time
        """
        try:
            snapshots = list_snapshots(
                volume_name=self.name,
                print_output=False
            )
            
            # Convert to expected format
            snapshot_list = []
            for snapshot in snapshots:
                snapshot_list.append({
                    'name': snapshot.get('Snapshot Name'),
                    'create_time': snapshot.get('Create Time')
                })
            
            return snapshot_list
            
        except Exception as e:
            raise DatasetVolumeError(f"Failed to list snapshots for dataset '{self.name}': {str(e)}")
    
    def delete(self):
        """
        Permanently delete this dataset.
        
        Raises:
            DatasetVolumeError: If the delete operation fails
        """
        try:
            delete_volume(
                volume_name=self.name,
                print_output=self.print_output
            )
            
            if self.print_output:
                print(f"Deleted dataset '{self.name}'")
                
        except Exception as e:
            raise DatasetVolumeError(f"Failed to delete dataset '{self.name}': {str(e)}")
    
    @classmethod
    def _check_dataset_exists(cls, name: str) -> bool:
        """Check if a dataset with the given name exists."""
        try:
            volumes = list_volumes(print_output=False)
            for volume in volumes:
                if volume.get("Volume Name") == name:
                    return True
            return False
        except:
            return False
    
    def __str__(self) -> str:
        """String representation of the dataset."""
        return f"Dataset(name='{self.name}', size='{self.max_size}', path='{self.local_file_path}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the dataset."""
        return (f"Dataset(name='{self.name}', max_size='{self.max_size}', "
                f"is_clone={self.is_clone}, local_file_path='{self.local_file_path}')")


def get_datasets(print_output: bool = False) -> List[Dataset]:
    """
    Get all existing datasets.
    
    Args:
        print_output: Whether to print status messages
        
    Returns:
        List of Dataset instances for all existing datasets
        
    Raises:
        DatasetConfigError: If dataset manager is not configured
        DatasetVolumeError: If there's an issue accessing volumes
    """
    # Initialize configuration
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise DatasetConfigError("Invalid or missing configuration file")
    
    if not config.get("datasetManagerEnabled", False):
        raise DatasetConfigError(
            "Dataset manager is not enabled. Run 'netapp_dataops_cli.py config' to configure."
        )
    
    root_volume_name = config.get("datasetManagerRootVolume")
    if not root_volume_name:
        raise DatasetConfigError(
            "Dataset manager root volume must be configured. "
            "Run 'netapp_dataops_cli.py config' to configure."
        )
    
    try:
        volumes = list_volumes(print_output=False)
        datasets = []
        
        for volume in volumes:
            junction_path = volume.get("Junction Path", "")
            # Check if volume is nested under the root volume
            if junction_path.startswith(f"/{root_volume_name}/"):
                # Extract dataset name from junction path
                dataset_name = junction_path.split("/")[-1]
                if dataset_name and dataset_name != root_volume_name:
                    try:
                        dataset = Dataset(name=dataset_name, print_output=False)
                        datasets.append(dataset)
                    except Exception as e:
                        if print_output:
                            print(f"Warning: Failed to load dataset '{dataset_name}': {str(e)}")
        
        return datasets
        
    except Exception as e:
        raise DatasetVolumeError(f"Failed to retrieve datasets: {str(e)}")
