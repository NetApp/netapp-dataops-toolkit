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

from netapp_dataops.logging_utils import setup_logger
from .models import DatasetManagerConfig
from .prompt_utils import PromptUtils
from ..traditional.ontap import volume_operations

logger = setup_logger(__name__)


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
        has_existing = PromptUtils.prompt_yes_no("  Do you have a pre-existing Dataset Manager 'root' volume?")
        
        if has_existing:
            # User claims they have existing root - collect config first
            return self._collect_existing_root_config()
        else:
            # No existing root - offer to create now
            create_new = PromptUtils.prompt_yes_no("  Would you like to create a new Dataset Manager 'root' volume now?")
            if create_new:
                return self._collect_new_root_config()
            else:
                logger.info("  Dataset Manager configuration skipped.")
                logger.info("  Note: Dataset Manager requires a root volume to function.")
                return DatasetManagerConfig(enabled=False)
    
    def _collect_existing_root_config(self) -> DatasetManagerConfig:
        """Collect configuration for existing root volume without performing operations."""
        while True:
            root_volume_name = PromptUtils.prompt_required("  Enter Dataset Manager \"root\" volume name (or 'abort' to cancel) ")
            
            # Allow user to abort
            if root_volume_name.lower() in ['abort', 'cancel', 'quit', 'exit']:
                logger.info("  Dataset Manager configuration cancelled.")
                return DatasetManagerConfig(enabled=False)
            
            # Basic validation - just check if volume exists
            try:
                volume_info = self._get_volume_info(root_volume_name)
                
                if volume_info is None:
                    logger.info(f"  Error: Volume '{root_volume_name}' not found on ONTAP.")
                    retry = PromptUtils.prompt_yes_no("  Would you like to try again?")
                    if not retry:
                        logger.info("  Dataset Manager configuration cancelled.")
                        return DatasetManagerConfig(enabled=False)
                    continue
                
                break
                    
            except Exception as e:
                logger.info(f"  Error checking volume: {e}")
                retry = PromptUtils.prompt_yes_no("  Would you like to try again?")
                if not retry:
                    logger.info("  Dataset Manager configuration cancelled.")
                    return DatasetManagerConfig(enabled=False)
                continue
        
        # Get local mountpoint
        root_mountpoint = PromptUtils.prompt_required("  Enter desired local mountpoint for Dataset Manager \"root\" volume")
        
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
        root_volume_name = PromptUtils.prompt_with_default("  Enter desired Dataset Manager \"root\" volume name:", "dataset_mgr_root")
        root_mountpoint = PromptUtils.prompt_required("  Enter desired local mountpoint for Dataset Manager \"root\" volume")
        
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
                logger.info(f"  Warning: Volume '{root_volume_name}' not found on ONTAP.")
                logger.info("  Configuration has been saved. Please verify the volume name and try setup again.")
                return
            
            # Check junction path
            junction_path = volume_info.get('NFS Mount Target', '')
            if ':' in junction_path:
                junction_path = junction_path.split(':', 1)[1]  # Extract path after data_lif:
            
            expected_junction = f"/{root_volume_name}"
            
            if junction_path != expected_junction:
                logger.info(f"  Warning: Volume '{root_volume_name}' exists but has junction path '{junction_path}'")
                logger.info(f"  Expected junction path: '{expected_junction}'")
                
                # Check if expected junction path is already taken by another volume
                if self._junction_path_exists(expected_junction, exclude_volume=root_volume_name):
                    logger.info(f"  Error: Junction path '{expected_junction}' is already in use by another volume.")
                    logger.info("  Configuration has been saved. Please resolve junction path conflicts manually.")
                    return
                
        except Exception as e:
            logger.info(f"  Error validating volume: {e}")
            logger.info("  Configuration has been saved. Please verify volume setup manually.")
            return
        
        # Handle mounting with proper validation
        self._handle_root_volume_mounting(root_volume_name, root_mountpoint)

    def _setup_new_root_volume(self, config: DatasetManagerConfig) -> None:
        """Perform operations for new root volume after config is saved."""
        root_volume_name = config.root_volume_name
        root_mountpoint = config.root_mountpoint
        
        logger.info(f"\n  Setting up new Dataset Manager root volume '{root_volume_name}'...")
        
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
                        logger.info(f"  Volume '{root_volume_name}' already exists with correct junction path.")
                        logger.info("  Proceeding with existing volume setup...")
                        break  # Volume is ready, proceed to mounting
                    else:
                        logger.info(f"  Volume '{root_volume_name}' exists but has junction path '{junction_path}'")
                        logger.info(f"  Expected: '{expected_junction}'")
                        logger.info("  Configuration has been saved. Please resolve junction path conflicts manually.")
                        return
                else:
                    # Check junction path collision
                    expected_junction = f"/{root_volume_name}"
                    if self._junction_path_exists(expected_junction):
                        logger.info(f"  Error: Junction path '{expected_junction}' is already in use by another volume.")
                        logger.info("  Configuration has been saved. Please choose a different volume name and reconfigure.")
                        return
                    
                    # Create the root volume
                    logger.info(f"  Creating Dataset Manager root volume '{root_volume_name}'...")
                    if not self._create_root_volume_on_ontap(root_volume_name):
                        logger.info("  Failed to create root volume.")
                        logger.info("  Configuration has been saved. Please create the volume manually or reconfigure with a different name.")
                        return
                    
                    logger.info(f"  Root volume '{root_volume_name}' created successfully")
                    break  # Volume created successfully
            
            except Exception as e:
                logger.info(f"  Error during volume operations: {e}")
                logger.info("  Configuration has been saved. Please create the volume manually or reconfigure.")
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
                logger.info(f"Error retrieving volume information: {e}")
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
                logger.info(f"Error checking junction path existence: {e}")
            return False
    
    def _create_root_volume_on_ontap(self, volume_name: str) -> bool:
        """Create the root volume on ONTAP with appropriate settings."""
        try:
            # Create a small root volume - suppress output during creation
            volume_operations.create_volume(
                volume_name=volume_name,
                volume_size="1GB",  # Minimal size for root volume
                junction=f"/{volume_name}",
                unix_permissions="444",  # Read-only permissions for root volume
                print_output=False
            )
            return True
        except Exception as e:
            if self.print_output:
                logger.info(f"Error creating volume: {e}")
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
                logger.info(f"  Volume '{volume_name}' is already correctly mounted at '{mountpoint}'")
                return
            else:
                logger.info(f"  Warning: Mountpoint '{mountpoint}' is in use by '{current_target}'")
                logger.info(f"  Expected: {expected_nfs_target}")
                return
        
        add_to_fstab = PromptUtils.prompt_yes_no(f"  Would you like to add your Dataset Manager \"root\" volume to /etc/fstab now?")
        
        if add_to_fstab:
            # Add to fstab FIRST, then mount using fstab entry
            if self._add_to_fstab(volume_name, mountpoint, expected_nfs_target):
                logger.info(f"  Volume '{volume_name}' added to fstab")
    
    def _add_to_fstab(self, volume_name: str, mountpoint: str, nfs_target: str) -> bool:
        """Add volume to fstab first, then mount using fstab entry (following requirements)."""
        try:
            # Check if fstab entry already exists
            if not self._fstab_entry_exists(mountpoint, volume_name):
                # Create standardized fstab entry
                fstab_entry = self._create_fstab_entry(nfs_target, mountpoint)
                
                # Ensure mountpoint directory exists
                os.makedirs(mountpoint, exist_ok=True)
                
                # Add entry to fstab safely
                if not self._add_fstab_entry_safely(fstab_entry, nfs_target, mountpoint):
                    logger.info("  Failed to add entry to /etc/fstab")
                    return False
                
                # Success message already printed by _add_fstab_entry_safely()
                return True
            else:
                logger.info(f"  Entry already exists in /etc/fstab")
                return True
                
        except Exception as e:
            logger.info(f"  Error in fstab setup and mount: {e}")
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
        # NFS version is auto-negotiated by the OS to use the highest supported version
        return f"{nfs_target} {mountpoint} nfs rw,_netdev,hard 0 0"
    
    def _add_fstab_entry_safely(self, fstab_entry: str, nfs_target: str, mountpoint: str) -> bool:
        """
        Add entry to /etc/fstab safely using atomic write pattern.
        
        This method:
        1. Detects if sudo is required and uses a single sudo session for all operations
        2. Creates a backup of /etc/fstab before modification
        3. Checks for duplicate entries using regex to parse fstab fields
        4. Uses atomic write (temp file + mv) to append the new entry
        5. Restores from backup if the operation fails
        
        Args:
            fstab_entry: The complete fstab entry line to add
            nfs_target: The NFS target (for validation)
            mountpoint: The mountpoint path
            
        Returns:
            bool: True if successful, False otherwise
        """
        fstab_path = '/etc/fstab'
        fstab_backup = '/etc/fstab.bak'
        fstab_temp = '/tmp/fstab.tmp'
        
        try:
            # Step 1: Check if we need sudo by testing write access to /etc
            needs_sudo = not os.access('/etc', os.W_OK)
            
            # Step 2: Read existing fstab content
            try:
                with open(fstab_path, 'r') as f:
                    current_content = f.read()
            except FileNotFoundError:
                current_content = ""
            except PermissionError:
                if needs_sudo:
                    result = subprocess.run(['sudo', 'cat', fstab_path],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        current_content = result.stdout
                    else:
                        current_content = ""
                else:
                    current_content = ""
            
            # Step 3: Parse existing entries using regex to avoid false positives
            fstab_pattern = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+\d+)?(?:\s+\d+)?\s*$')
            
            for line in current_content.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                match = fstab_pattern.match(stripped)
                if match:
                    existing_device = match.group(1)
                    existing_mountpoint = match.group(2)
                    
                    if existing_mountpoint == mountpoint:
                        logger.info(f"  Warning: An entry for mountpoint '{mountpoint}' already exists in /etc/fstab")
                        logger.info(f"    Existing: {existing_device} -> {existing_mountpoint}")
                        logger.info("  Skipping duplicate entry. Please manually edit /etc/fstab if you need to update it.")
                        return True
            
            # Step 4: Prepare entry with comment
            comment = ""
            if "# Dataset Manager root volume" not in current_content:
                comment = "# Dataset Manager root volume\n"
            
            full_entry = f"{comment}{fstab_entry}\n"
            
            # Step 5: Prepare new content
            new_content = current_content
            if not new_content.endswith('\n') and new_content:
                new_content += '\n'
            new_content += full_entry
            
            # Step 6: Write to temporary file
            try:
                with open(fstab_temp, 'w') as f:
                    f.write(new_content)
            except Exception as e:
                logger.info(f"  ERROR: Failed to write temporary file: {e}")
                return False
            
            # Step 7: Execute all operations in a single sudo session if needed
            if needs_sudo:
                logger.info("  Elevated privileges required to modify /etc/fstab...")
                
                # Single sudo command that does: backup, move temp to fstab
                # Using shell to chain commands in one sudo session (only one password prompt)
                shell_cmd = f"cp {fstab_path} {fstab_backup} && mv {fstab_temp} {fstab_path}"
                result = subprocess.run(['sudo', 'sh', '-c', shell_cmd],
                                      capture_output=True, text=True)
                
                if result.returncode != 0:
                    # Operation failed - try to restore from backup if it was created
                    error_msg = result.stderr.strip()
                    
                    # Check if backup was created before the failure
                    if os.path.exists(fstab_backup):
                        logger.info(f"  ERROR: Failed to update /etc/fstab. Restoring from backup...")
                        subprocess.run(['sudo', 'cp', fstab_backup, fstab_path],
                                     capture_output=True, text=True)
                    
                    # Clean up temp file
                    try:
                        if os.path.exists(fstab_temp):
                            os.remove(fstab_temp)
                    except:
                        pass
                    
                    logger.info(f"  ERROR: Failed to modify /etc/fstab ({error_msg}). Please manually add: {fstab_entry}")
                    return False
                
                logger.info(f"  Created backup: {fstab_backup}")
            else:
                # No sudo needed - do operations directly
                try:
                    # Create backup
                    subprocess.run(['cp', fstab_path, fstab_backup], check=True,
                                 capture_output=True, text=True)
                    logger.info(f"  Created backup: {fstab_backup}")
                    
                    # Move temp file to fstab
                    subprocess.run(['mv', fstab_temp, fstab_path], check=True,
                                 capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    # Restore from backup
                    if os.path.exists(fstab_backup):
                        logger.info(f"  ERROR: Failed to update /etc/fstab. Restoring from backup...")
                        subprocess.run(['cp', fstab_backup, fstab_path],
                                     capture_output=True, text=True)
                    
                    # Clean up temp file
                    try:
                        if os.path.exists(fstab_temp):
                            os.remove(fstab_temp)
                    except:
                        pass
                    
                    logger.info(f"  ERROR: Failed to modify /etc/fstab. Please manually add: {fstab_entry}")
                    return False
            
            # Step 8: Clean up temp file if it still exists
            try:
                if os.path.exists(fstab_temp):
                    os.remove(fstab_temp)
            except:
                pass
            
            logger.info(f"  Successfully added entry to /etc/fstab")
            return True
            
        except Exception as e:
            # Clean up temp file
            try:
                if os.path.exists(fstab_temp):
                    os.remove(fstab_temp)
            except:
                pass
            
            logger.info(f"  ERROR: Error updating /etc/fstab: {e}")
            logger.info(f"  Please manually add: {fstab_entry}")
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
                    # Only return True if we find a matching volume AND matching mountpoint
                    # to avoid false positives from old entries
                    if f"/{volume_name}" in device and mount_point == mountpoint:
                        return True
                
            return False
            
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.info(f"Warning: Error checking fstab: {e}")
            return False
