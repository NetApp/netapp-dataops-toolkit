"""
Dataset Manager configuration module for NetApp DataOps Toolkit.

This module handles all Dataset Manager specific configuration operations
including root volume creation, mounting, and validation.
"""

import os
import platform
import re
import shutil
import subprocess
from typing import Optional, Dict, Any

from .models import DatasetManagerConfig
from .prompt_utils import PromptUtils
from ..traditional.ontap import volume_operations


class DatasetManagerConfigurator:
    """
    Handles Dataset Manager configuration operations.
    
    This class is responsible for setting up
    including root volume creation, mounting, and system requirements validation.
    """
    
    def __init__(self, print_output: bool = True):
        """
        Initialize the Dataset Manager configurator.
        
        Args:
            print_output: Whether to print output messages (useful for testing)
        """
        self.print_output = print_output
    
    @staticmethod
    def _check_required_utilities(*utilities: str) -> None:
        """
        Check if required system utilities are available.
        
        Args:
            *utilities: Variable number of utility names to check
            
        Raises:
            RuntimeError: If any required utility is missing
        """
        missing_utilities = []
        for utility in utilities:
            if not shutil.which(utility):
                missing_utilities.append(utility)
        
        if missing_utilities:
            utility_list = "', '".join(missing_utilities)
            error_msg = (
                f"ERROR: Required system utilities missing: '{utility_list}'\n"
                f"Please install the missing utilities and try again.\n"
            )
            
            # Add platform-specific installation hints
            if platform.system() == 'Linux':
                error_msg += "On Debian/Ubuntu: sudo apt-get install nfs-common\n"
                error_msg += "On RHEL/CentOS: sudo yum install nfs-utils\n"
            elif platform.system() == 'Darwin':
                error_msg += "On macOS, these utilities should be available by default.\n"
            
            raise RuntimeError(error_msg)
    
    def configure_dataset_manager(self) -> DatasetManagerConfig:
        """
        Create Dataset Manager configuration through interactive prompts.
        
        Returns:
            DatasetManagerConfig: Created configuration
        """        
        # Check if user has existing root volume
        has_existing = PromptUtils.prompt_yes_no("Do you have a pre-existing Dataset Manager 'root' volume?")
        
        if has_existing:
            # User claims they have existing root - collect config first
            return self._collect_existing_root_config()
        else:
            # No existing root - offer to create now
            create_new = PromptUtils.prompt_yes_no("Would you like to create a new Dataset Manager 'root' volume now?")
            if create_new:
                return self._collect_new_root_config()
            else:
                print("Dataset Manager configuration skipped.")
                print("Note: Dataset Manager requires a root volume to function.")
                return DatasetManagerConfig(enabled=False)
    
    def _collect_existing_root_config(self) -> DatasetManagerConfig:
        """Collect configuration for existing root volume without performing operations."""
        while True:
            root_volume_name = PromptUtils.prompt_required("Enter Dataset Manager \"root\" volume name (or 'abort' to cancel): ")
            
            # Allow user to abort
            if root_volume_name.lower() in ['abort', 'cancel', 'quit', 'exit']:
                print("Dataset Manager configuration cancelled.")
                return DatasetManagerConfig(enabled=False)
            
            # Basic validation - just check if volume exists
            try:
                volume_info = self._get_volume_info(root_volume_name)
                
                if volume_info is None:
                    print(f"Error: Volume '{root_volume_name}' not found on ONTAP.")
                    retry = PromptUtils.prompt_yes_no("Would you like to try again?")
                    if not retry:
                        print("Dataset Manager configuration cancelled.")
                        return DatasetManagerConfig(enabled=False)
                    continue
                
                print(f"✓ Volume '{root_volume_name}' found on ONTAP")
                break
                    
            except Exception as e:
                print(f"Error checking volume: {e}")
                retry = PromptUtils.prompt_yes_no("Would you like to try again?")
                if not retry:
                    print("Dataset Manager configuration cancelled.")
                    return DatasetManagerConfig(enabled=False)
                continue
        
        # Get local mountpoint
        root_mountpoint = PromptUtils.prompt_required("Enter desired local mountpoint for Dataset Manager \"root\" volume:")
        
        # Create configuration object
        config = DatasetManagerConfig(
            enabled=True,
            root_volume_name=root_volume_name,
            root_mountpoint=root_mountpoint
        )
        
        # Now perform operations after config is saved
        self._setup_existing_root_volume(config)
        
        return config

    def _collect_new_root_config(self) -> DatasetManagerConfig:
        """Collect configuration for new root volume without performing operations."""
        # 1. Collect inputs
        root_volume_name = PromptUtils.prompt_with_default("Enter desired Dataset Manager \"root\" volume name:", "dataset_mgr_root")
        root_mountpoint = PromptUtils.prompt_required("Enter desired local mountpoint for Dataset Manager \"root\" volume:")
        
        # Create configuration object
        config = DatasetManagerConfig(
            enabled=True,
            root_volume_name=root_volume_name,
            root_mountpoint=root_mountpoint
        )
        
        self._setup_new_root_volume(config)
        
        return config

    def _setup_existing_root_volume(self, config: DatasetManagerConfig) -> None:
        """Perform operations for existing root volume after config is saved."""
        root_volume_name = config.root_volume_name
        root_mountpoint = config.root_mountpoint
        
        # Verify the volume exists and validate junction path
        try:
            volume_info = self._get_volume_info(root_volume_name)
            
            if volume_info is None:
                print(f"Warning: Volume '{root_volume_name}' not found on ONTAP.")
                print("Configuration has been saved. Please verify the volume name and try setup again.")
                return
            
            # Check junction path
            junction_path = volume_info.get('NFS Mount Target', '')
            if ':' in junction_path:
                junction_path = junction_path.split(':', 1)[1]  # Extract path after data_lif:
            
            expected_junction = f"/{root_volume_name}"
            
            if junction_path != expected_junction:
                print(f"Warning: Volume '{root_volume_name}' exists but has junction path '{junction_path}'")
                print(f"Expected junction path: '{expected_junction}'")
                
                # Check if expected junction path is already taken by another volume
                if self._junction_path_exists(expected_junction, exclude_volume=root_volume_name):
                    print(f"Error: Junction path '{expected_junction}' is already in use by another volume.")
                    print("Configuration has been saved. Please resolve junction path conflicts manually.")
                    return
            else:
                print(f"Volume '{root_volume_name}' found with correct junction path '{junction_path}'")
                
        except Exception as e:
            print(f"Error validating volume: {e}")
            print("Configuration has been saved. Please verify volume setup manually.")
            return
        
        # Handle mounting with proper validation
        self._handle_root_volume_mounting(root_volume_name, root_mountpoint)

    def _setup_new_root_volume(self, config: DatasetManagerConfig) -> None:
        """Perform operations for new root volume after config is saved."""
        root_volume_name = config.root_volume_name
        root_mountpoint = config.root_mountpoint
        
        print(f"\nSetting up new Dataset Manager root volume '{root_volume_name}'...")
        
        while True:  # Loop for retrying with different names if needed
            try:
                # Check if volume already exists
                existing_volume = self._get_volume_info(root_volume_name)
                if existing_volume:
                    junction_path = existing_volume.get('NFS Mount Target', '')
                    if ':' in junction_path:
                        junction_path = junction_path.split(':', 1)[1]
                    
                    expected_junction = f"/{root_volume_name}"
                    
                    if junction_path == expected_junction:
                        print(f"Volume '{root_volume_name}' already exists with correct junction path.")
                        print("Proceeding with existing volume setup...")
                        break  # Volume is ready, proceed to mounting
                    else:
                        print(f"Volume '{root_volume_name}' exists but has junction path '{junction_path}'")
                        print(f"Expected: '{expected_junction}'")
                        print("Configuration has been saved. Please resolve junction path conflicts manually.")
                        return
                else:
                    # Check junction path collision
                    expected_junction = f"/{root_volume_name}"
                    if self._junction_path_exists(expected_junction):
                        print(f"Error: Junction path '{expected_junction}' is already in use by another volume.")
                        print("Configuration has been saved. Please choose a different volume name and reconfigure.")
                        return
                    
                    # Create the root volume
                    print(f"Creating Dataset Manager root volume '{root_volume_name}'...")
                    if not self._create_root_volume_on_ontap(root_volume_name):
                        print("Failed to create root volume.")
                        print("Configuration has been saved. Please create the volume manually or reconfigure with a different name.")
                        return
                    
                    print(f"Root volume '{root_volume_name}' created successfully")
                    break  # Volume created successfully
            
            except Exception as e:
                print(f"Error during volume operations: {e}")
                print("Configuration has been saved. Please create the volume manually or reconfigure.")
                return
        
        # Handle mounting with proper validation
        self._handle_root_volume_mounting(root_volume_name, root_mountpoint)
    
    def _get_volume_info(self, volume_name: str) -> Optional[Dict[str, Any]]:
        """Get volume information from ONTAP."""
        try:
            # Use list_volumes to find the specific volume
            # Always suppress output to avoid displaying volume lists during user input
            volumes = volume_operations.list_volumes(print_output=False)
            for volume in volumes:
                if volume.get("Volume Name") == volume_name:
                    return volume
            return None
        except Exception as e:
            if self.print_output:
                print(f"Error retrieving volume information: {e}")
            return None
    
    def _junction_path_exists(self, junction_path: str, exclude_volume: str = None) -> bool:
        """Check if a junction path is already in use by any volume."""
        try:
            # Always suppress output to avoid displaying volume lists during validation
            volumes = volume_operations.list_volumes(print_output=False)
            for volume in volumes:
                # Skip the excluded volume (useful when checking for conflicts)
                volume_name = volume.get("Volume Name")
                if exclude_volume and volume_name == exclude_volume:
                    continue
                    
                nfs_target = volume.get('NFS Mount Target')
                # Quick checks: skip if no NFS target or doesn't contain ':'
                if not nfs_target or ':' not in nfs_target:
                    continue
                
                # Extract junction path and compare
                vol_junction_path = nfs_target.split(':', 1)[1]
                if vol_junction_path == junction_path:
                    return True
            return False
        except Exception as e:
            if self.print_output:
                print(f"Error checking junction path existence: {e}")
            return False
    
    def _create_root_volume_on_ontap(self, volume_name: str) -> bool:
        """Create the root volume on ONTAP with appropriate settings."""
        try:
            # Create a small root volume - suppress output during creation
            volume_operations.create_volume(
                volume_name=volume_name,
                volume_size="1GB",  # Minimal size for root volume
                junction=f"/{volume_name}",
                print_output=False
            )
            return True
        except Exception as e:
            if self.print_output:
                print(f"Error creating volume: {e}")
            return False
    
    def _is_mounted(self, mountpoint: str) -> bool:
        """Check if a mountpoint is currently in use."""
        try:
            # Check if mountpoint utility is available
            self._check_required_utilities('mountpoint')
            
            result = subprocess.run(['mountpoint', '-q', mountpoint], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except RuntimeError as e:
            # Re-raise utility check errors
            raise
        except Exception:
            return False
    
    def _get_mount_target(self, mountpoint: str) -> str:
        """Get what is currently mounted at the given mountpoint."""
        try:
            # Check if mount utility is available
            self._check_required_utilities('mount')
            
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if f" {mountpoint} " in line:
                        # Extract the source (first part before " on ")
                        return line.split(' on ')[0]
            return "unknown"
        except RuntimeError as e:
            # Re-raise utility check errors
            raise
        except Exception:
            return "unknown"
    
    def _handle_root_volume_mounting(self, volume_name: str, mountpoint: str) -> None:
        """Handle one-time mounting of root volume with proper validation."""
        expected_nfs_target = self._get_expected_nfs_target(volume_name)
        
        # Check current mount status
        is_mounted = self._is_mounted(mountpoint)
        
        if is_mounted:
            current_target = self._get_mount_target(mountpoint)
            
            if expected_nfs_target in current_target or f"/{volume_name}" in current_target:
                print(f"✓ Volume '{volume_name}' is already correctly mounted at '{mountpoint}'")
                return
            else:
                print(f"Warning: Mountpoint '{mountpoint}' is in use by '{current_target}'")
                print(f"Expected: {expected_nfs_target}")
                return
        
        add_to_fstab = PromptUtils.prompt_yes_no(f"Would you like to add your Dataset Manager \"root\" volume to /etc/fstab now? (yes/no):")
        
        if add_to_fstab:
            # Add to fstab FIRST, then mount using fstab entry
            if self._add_to_fstab(volume_name, mountpoint, expected_nfs_target):
                print(f"Volume '{volume_name}' added to fstab and mounted successfully")
    
    def _add_to_fstab(self, volume_name: str, mountpoint: str, nfs_target: str) -> bool:
        """Add volume to fstab first, then mount using fstab entry (following requirements)."""
        try:
            # Check if fstab entry already exists
            if self._fstab_entry_exists(mountpoint, volume_name):
                print(f"/etc/fstab already contains an entry for this mount")
            else:
                # Create standardized fstab entry
                fstab_entry = self._create_fstab_entry(nfs_target, mountpoint)
                
                # Ensure mountpoint directory exists
                os.makedirs(mountpoint, exist_ok=True)
                
                # Add entry to fstab safely
                if not self._add_fstab_entry_safely(fstab_entry, nfs_target, mountpoint):
                    print("Failed to add entry to /etc/fstab")
                    return False
                
        except Exception as e:
            print(f"Error in fstab setup and mount: {e}")
            return False

    def _get_expected_nfs_target(self, volume_name: str) -> str:
        """Get the expected NFS target for a volume."""
        try:
            from ..traditional.core import _retrieve_config
            config = _retrieve_config(print_output=self.print_output)
            data_lif = config.get("dataLif", "unknown")
            return f"{data_lif}:/{volume_name}"
        except Exception:
            return f"<data_lif>:/{volume_name}"
    
    def _create_fstab_entry(self, nfs_target: str, mountpoint: str) -> str:
        """Create a standardized fstab entry for Dataset Manager volumes.
        
        Args:
            nfs_target: The NFS target (e.g., "data_lif:/volume_name")
            mountpoint: The local mountpoint path
            
        Returns:
            str: Complete fstab entry line
        """
        # Production-ready fstab entry with essential NFS options
        # For Dataset Manager root volume: permanent mount, no auto-unmount
        return f"{nfs_target} {mountpoint} nfs rw,_netdev,nfsvers=4.1,hard 0 0"
    
    def _add_fstab_entry_safely(self, fstab_entry: str, nfs_target: str, mountpoint: str) -> bool:
        """
        Add entry to /etc/fstab safely using regex-based parsing.
        
        This method:
        1. Checks for duplicate entries using regex to parse fstab fields
        2. Appends the new entry if not already present
        
        Args:
            fstab_entry: The complete fstab entry line to add
            nfs_target: The NFS target (for validation)
            mountpoint: The mountpoint path
            
        Returns:
            bool: True if successful, False otherwise
        """
        fstab_path = '/etc/fstab'
        
        try:
            # Step 1: Read existing fstab content
            try:
                with open(fstab_path, 'r') as f:
                    current_content = f.read()
            except FileNotFoundError:
                current_content = ""
            except PermissionError:
                # Try reading with sudo
                result = subprocess.run(['sudo', 'cat', fstab_path],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    current_content = result.stdout
                else:
                    current_content = ""
            
            # Parse existing entries using regex to avoid false positives
            # Regex pattern matches: <device> <mountpoint> <fstype> <options> <dump> <pass>
            # Example match: "192.168.1.10:/vol1 /mnt/data nfs rw,hard 0 0"
            fstab_pattern = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+\d+)?(?:\s+\d+)?\s*$')
            
            for line in current_content.splitlines():
                # Skip comments and empty lines
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Use regex to parse fstab entry fields
                match = fstab_pattern.match(stripped)
                if match:
                    existing_device = match.group(1)
                    existing_mountpoint = match.group(2)
                    
                    if existing_mountpoint == mountpoint:
                        print(f"Warning: An entry for mountpoint '{mountpoint}' already exists in /etc/fstab")
                        print(f"  Existing: {existing_device} -> {existing_mountpoint}")
                        print("Skipping duplicate entry. Please manually edit /etc/fstab if you need to update it.")
                        return True  # Not an error - entry already exists
            
            # Step 2: Append new entry with comment
            comment = "# Dataset Manager root volume\n"
            full_entry = f"{comment}{fstab_entry}\n"
            
            # Use shell redirection to append (safer than rewriting entire file)
            # Escape any special characters in the entry
            escaped_entry = full_entry.replace("'", "'\\''")
            
            result = subprocess.run(
                ['sudo', 'sh', '-c', f"printf '%s' '{escaped_entry}' >> {fstab_path}"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                print(f"Error appending to /etc/fstab: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error updating /etc/fstab: {e}")
            return False
    
    def _fstab_entry_exists(self, mountpoint: str, volume_name: str) -> bool:
        """
        Check if an fstab entry already exists for this mount using regex parsing.
        
        Args:
            mountpoint: The mountpoint path to check
            volume_name: The volume name to check
            
        Returns:
            bool: True if entry exists, False otherwise
        """
        try:
            with open('/etc/fstab', 'r') as f:
                content = f.read()
            
            # Use regex to parse fstab entries and avoid false positives
            # Regex pattern matches: <device> <mountpoint> <fstype> <options> <dump> <pass>
            # Example match: "192.168.1.10:/vol1 /mnt/data nfs rw,hard 0 0"
            fstab_pattern = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+\d+)?(?:\s+\d+)?\s*$')
            
            for line in content.splitlines():
                # Skip comments and empty lines
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Use regex to parse fstab entry fields
                match = fstab_pattern.match(stripped)
                if match:
                    device = match.group(1)
                    mount_point = match.group(2)
                    
                    # Check if this entry matches our mountpoint
                    if mount_point == mountpoint:
                        return True
                    
                    # Check if the device contains our volume name (e.g., "data_lif:/volume_name")
                    if f"/{volume_name}" in device:
                        return True
            
            # Also check for our comment marker
            if "Dataset Manager root volume" in content:
                return True
                
            return False
            
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Warning: Error checking fstab: {e}")
            return False
