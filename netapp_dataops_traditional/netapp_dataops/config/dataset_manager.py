"""
Dataset Manager configuration module for NetApp DataOps Toolkit.

This module handles all Dataset Manager specific configuration operations
including root volume creation, mounting, and validation.
"""

import os
import platform
import subprocess
from typing import Optional, Dict, Any

from .models import DatasetManagerConfig
from .prompt_utils import PromptUtils
from ..traditional.ontap import volume_operations


class DatasetManagerConfigurator:
    """
    Handles Dataset Manager configuration operations.
    
    This class is responsible for setting up and configuring Dataset Manager
    including root volume creation, mounting, and system requirements validation.
    """
    
    def configure_dataset_manager(self) -> DatasetManagerConfig:
        """
        Create Dataset Manager configuration through interactive prompts.
        
        Returns:
            DatasetManagerConfig: Created configuration
        """
        print("\n--- Dataset Manager Settings ---")
        
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
            root_volume_name = PromptUtils.prompt_required("Enter Dataset Manager \"root\" volume name: ")
            
            # Basic validation - just check if volume exists
            try:
                volume_info = self._get_volume_info(root_volume_name)
                
                if volume_info is None:
                    print(f"Error: Volume '{root_volume_name}' not found on ONTAP.")
                    continue
                
                print(f"✓ Volume '{root_volume_name}' found on ONTAP")
                break
                    
            except Exception as e:
                print(f"Error checking volume: {e}")
                continue
        
        # Get local mountpoint
        root_mountpoint = PromptUtils.prompt_required("Enter desired local mountpoint for Dataset Manager \"root\" volume:")
        
        # Create configuration object
        config = DatasetManagerConfig(
            enabled=True,
            root_volume_name=root_volume_name,
            root_mountpoint=root_mountpoint
        )
        
        print("✅ Dataset Manager configuration created successfully!")
        print(f"   Root volume: {root_volume_name}")
        print(f"   Mountpoint: {root_mountpoint}")
        
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
        
        print(f"\nSetting up existing Dataset Manager root volume '{root_volume_name}'...")
        
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
                print(f"✓ Volume '{root_volume_name}' found with correct junction path '{junction_path}'")
                
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
            volumes = volume_operations.list_volumes(print_output=False)
            for volume in volumes:
                if volume.get("Volume Name") == volume_name:
                    return volume
            return None
        except Exception as e:
            print(f"Error retrieving volume information: {e}")
            return None
    
    def _junction_path_exists(self, junction_path: str, exclude_volume: str = None) -> bool:
        """Check if a junction path is already in use by any volume."""
        try:
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
            print(f"Error checking junction path existence: {e}")
            return False
    
    def _create_root_volume_on_ontap(self, volume_name: str) -> bool:
        """Create the root volume on ONTAP with appropriate settings."""
        try:
            # Create a small root volume - let create_volume handle defaults from config
            volume_operations.create_volume(
                volume_name=volume_name,
                volume_size="1GB",  # Minimal size for root volume
                junction=f"/{volume_name}",
                print_output=False
            )
            return True
        except Exception as e:
            print(f"Error creating volume: {e}")
            return False
    
    def _is_mounted(self, mountpoint: str) -> bool:
        """Check if a mountpoint is currently in use."""
        try:
            result = subprocess.run(['mountpoint', '-q', mountpoint], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_mount_target(self, mountpoint: str) -> str:
        """Get what is currently mounted at the given mountpoint."""
        try:
            result = subprocess.run(['mount'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if f" {mountpoint} " in line:
                        # Extract the source (first part before " on ")
                        return line.split(' on ')[0]
            return "unknown"
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
        
        print(f"\nConfiguring mount options for volume '{volume_name}'...")
        add_to_fstab = PromptUtils.prompt_yes_no(f"Would you like to add your Dataset Manager \"root\" volume to /etc/fstab now? (yes/no):")
        
        if add_to_fstab:
            # Add to fstab FIRST, then mount using fstab entry
            if self._add_to_fstab(volume_name, mountpoint, expected_nfs_target):
                print(f"Volume '{volume_name}' added to fstab and mounted successfully")
    
    def _add_to_fstab(self, volume_name: str, mountpoint: str, nfs_target: str) -> bool:
        """Add volume to fstab first, then mount using fstab entry (following requirements)."""
        try:
            print(f"\nAdding Dataset Manager volume to /etc/fstab...")
            
            # Check if fstab entry already exists
            if self._fstab_entry_exists(mountpoint, volume_name):
                print(f"/etc/fstab already contains an entry for this mount")
            else:
                # Create standardized fstab entry
                fstab_entry = self._create_fstab_entry(nfs_target, mountpoint)
                
                # Ensure mountpoint directory exists
                os.makedirs(mountpoint, exist_ok=True)
                print(f"Mountpoint directory '{mountpoint}' ready")
                
                # Add entry to fstab safely
                if not self._add_fstab_entry_safely(fstab_entry, nfs_target, mountpoint):
                    print("Failed to add entry to /etc/fstab")
                    return False
                
                print(f"Entry added to /etc/fstab successfully")
                
        except Exception as e:
            print(f"Error in fstab setup and mount: {e}")
            return False

    def _get_expected_nfs_target(self, volume_name: str) -> str:
        """Get the expected NFS target for a volume."""
        try:
            from ..traditional.core import _retrieve_config
            config = _retrieve_config(print_output=False)
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
        """Add entry to /etc/fstab safely, avoiding duplicates."""
        try:
            # Read current fstab content
            try:
                with open('/etc/fstab', 'r') as f:
                    current_content = f.read()
            except Exception:
                current_content = ""
            
            # Check for existing entries for this mountpoint
            lines = current_content.strip().split('\n')
            new_lines = []
            found_existing = False
            
            for line in lines:
                if line.strip() and not line.strip().startswith('#'):
                    # Parse fstab line: device mountpoint fstype options dump pass
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == mountpoint:
                        # Found existing entry for this mountpoint - replace it
                        print(f"Replacing existing fstab entry for {mountpoint}")
                        new_lines.append(f"# Dataset Manager root volume")
                        new_lines.append(fstab_entry)
                        found_existing = True
                        continue
                
                new_lines.append(line)
            
            # If no existing entry found, add new one
            if not found_existing:
                if new_lines and new_lines[-1].strip():  # Add blank line if needed
                    new_lines.append("")
                new_lines.append("# Dataset Manager root volume")
                new_lines.append(fstab_entry)
            
            # Write updated content
            updated_content = '\n'.join(new_lines)
            if not updated_content.endswith('\n'):
                updated_content += '\n'
            
            # Use a more robust approach to write to fstab
            result = subprocess.run([
                'sudo', 'sh', '-c', 
                f"cat > /etc/fstab << 'EOF'\n{updated_content}EOF"
            ], capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error updating /etc/fstab: {e}")
            return False
    
    def _fstab_entry_exists(self, mountpoint: str, volume_name: str) -> bool:
        """Check if an fstab entry already exists for this mount."""
        try:
            with open('/etc/fstab', 'r') as f:
                content = f.read()
                
            # Check for either mountpoint or volume name in fstab
            return (mountpoint in content or 
                    f"/{volume_name}" in content or
                    "Dataset Manager root volume" in content)
        except Exception:
            return False
