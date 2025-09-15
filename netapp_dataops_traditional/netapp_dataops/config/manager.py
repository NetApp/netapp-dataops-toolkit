"""
Configuration Manager for NetApp DataOps Toolkit.

This module provides the ConfigManager class for handling configuration
lifecycle operations including creation, loading, saving, and validation.
"""

import json
import base64
import getpass
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from .models import NetAppDataOpsConfig, ONTAPConfig, S3Config, CloudSyncConfig, DatasetManagerConfig
from .exceptions import (
    ConfigError, 
    ConfigValidationError, 
    ConfigFileError, 
    ConfigCreationError
)
from ..traditional.ontap import volume_operations


class ConfigManager:
    """
    Manages NetApp DataOps Toolkit configuration operations.
    
    Handles configuration file I/O, validation, and user interaction
    for creating and managing configuration settings.
    """
    
    DEFAULT_CONFIG_FILE = "config.json"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_file: Path to configuration file. If None, uses default.
        """
        self.config_file = Path(config_file or self.DEFAULT_CONFIG_FILE)
    
    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_file.exists()
    
    def load_config(self) -> NetAppDataOpsConfig:
        """
        Load configuration from file.
        
        Returns:
            NetAppDataOpsConfig: Loaded configuration
            
        Raises:
            ConfigFileError: If file doesn't exist or can't be read
            ConfigValidationError: If configuration is invalid
        """
        if not self.config_exists():
            raise ConfigFileError(f"Configuration file '{self.config_file}' not found")
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            return NetAppDataOpsConfig.from_dict(data)
            
        except json.JSONDecodeError as e:
            raise ConfigFileError(f"Invalid JSON in configuration file: {e}")
        except (ConfigValidationError, ValueError) as e:
            raise ConfigValidationError(f"Invalid configuration: {e}")
    
    def save_config(self, config: NetAppDataOpsConfig) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            
        Raises:
            ConfigFileError: If file cannot be written
        """
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=4)
                
        except IOError as e:
            raise ConfigFileError(f"Cannot write configuration file: {e}")
    
    def create_interactive_config(self) -> NetAppDataOpsConfig:
        """
        Create configuration through interactive prompts.
        
        Returns:
            NetAppDataOpsConfig: Created configuration
            
        Raises:
            ConfigCreationError: If configuration creation fails
        """
        try:
            print("\n=== NetApp DataOps Toolkit Configuration ===\n")
            
            # Create ONTAP configuration
            ontap_config = self._create_ontap_config()
            
            # Optional S3 configuration
            s3_config = None
            if self._prompt_yes_no("Do you want to configure S3 settings?"):
                s3_config = self._create_s3_config()
            
            # Optional Cloud Sync configuration
            cloud_sync_config = None
            if self._prompt_yes_no("Do you want to configure Cloud Sync settings?"):
                cloud_sync_config = self._create_cloud_sync_config()
            
            # Optional Dataset Manager configuration
            dataset_manager_config = None
            if self._prompt_yes_no("Do you intend to use the toolkit's Dataset Manager functionality?"):
                dataset_manager_config = self._create_dataset_manager_config()
            
            return NetAppDataOpsConfig(
                ontap=ontap_config,
                s3=s3_config,
                cloud_sync=cloud_sync_config,
                dataset_manager=dataset_manager_config
            )
            
        except Exception as e:
            raise ConfigCreationError(f"Failed to create configuration: {e}")
    
    def _create_ontap_config(self) -> ONTAPConfig:
        """Create ONTAP configuration through interactive prompts."""
        print("--- ONTAP Connection Settings ---")
        
        hostname = self._prompt_required("ONTAP management or data LIF hostname or IP address")
        svm = self._prompt_required("SVM (Storage Virtual Machine) name")
        data_lif = self._prompt_required("Data LIF hostname or IP address")
        username = self._prompt_required("ONTAP admin username")
        password = self._prompt_password("ONTAP admin password")
        
        verify_ssl = self._prompt_yes_no("Verify SSL certificate?", default=True)
        
        print("\n--- Default Volume Settings ---")
        
        volume_type = self._prompt_choice(
            "Default volume type",
            choices=["flexgroup", "flexvol"],
            default="flexgroup"
        )
        
        export_policy = self._prompt_with_default("Default export policy", "default")
        snapshot_policy = self._prompt_with_default("Default snapshot policy", "none")
        unix_uid = self._prompt_with_default("Default Unix UID", "0")
        unix_gid = self._prompt_with_default("Default Unix GID", "0")
        unix_permissions = self._prompt_with_default("Default Unix permissions", "0777")
        default_aggregate = self._prompt_with_default("Default aggregate (leave empty for auto)", "")
        
        return ONTAPConfig(
            hostname=hostname,
            svm=svm,
            data_lif=data_lif,
            username=username,
            password=base64.b64encode(password.encode()).decode(),
            verify_ssl_cert=verify_ssl,
            default_volume_type=volume_type,
            default_export_policy=export_policy,
            default_snapshot_policy=snapshot_policy,
            default_unix_uid=unix_uid,
            default_unix_gid=unix_gid,
            default_unix_permissions=unix_permissions,
            default_aggregate=default_aggregate
        )
    
    def _create_s3_config(self) -> S3Config:
        """Create S3 configuration through interactive prompts."""
        print("\n--- S3 Settings ---")
        
        endpoint = self._prompt_required("S3 endpoint URL")
        access_key_id = self._prompt_required("S3 access key ID")
        secret_access_key = self._prompt_password("S3 secret access key")
        
        verify_ssl = self._prompt_yes_no("Verify S3 SSL certificate?", default=True)
        ca_cert_bundle = self._prompt_with_default("CA certificate bundle path (optional)", "")
        
        return S3Config(
            endpoint=endpoint,
            access_key_id=access_key_id,
            secret_access_key=base64.b64encode(secret_access_key.encode()).decode(),
            verify_ssl_cert=verify_ssl,
            ca_cert_bundle=ca_cert_bundle
        )
    
    def _create_cloud_sync_config(self) -> CloudSyncConfig:
        """Create Cloud Sync configuration through interactive prompts."""
        print("\n--- Cloud Sync Settings ---")
        
        refresh_token = self._prompt_password("Cloud Central refresh token")
        
        return CloudSyncConfig(
            refresh_token=base64.b64encode(refresh_token.encode()).decode()
        )
    
    def _create_dataset_manager_config(self) -> DatasetManagerConfig:
        """Create Dataset Manager configuration through interactive prompts."""
        print("\n--- Dataset Manager Settings ---")
        
        # Check if user has existing root volume
        has_existing = self._prompt_yes_no("Do you have a pre-existing Dataset Manager 'root' volume?")
        
        if has_existing:
            # User claims they have existing root - validate and bind
            return self._bind_existing_root_volume()
        else:
            # No existing root - offer to create now
            create_new = self._prompt_yes_no("Would you like to create a new Dataset Manager 'root' volume now?")
            if create_new:
                return self._create_new_root_volume()
            else:
                print("Dataset Manager configuration skipped.")
                print("Note: Dataset Manager requires a root volume to function.")
                return DatasetManagerConfig(enabled=False)
    
    def _bind_existing_root_volume(self) -> DatasetManagerConfig:
        """Bind to an existing root volume with validation."""
        while True:
            root_volume_name = self._prompt_required("Dataset Manager 'root' volume name")
            
            # Verify the volume exists and get its details
            try:
                volume_info = self._get_volume_info(root_volume_name)
                
                if volume_info is None:
                    print(f"Error: Volume '{root_volume_name}' not found on ONTAP.")
                    if not self._prompt_yes_no("Would you like to try a different name?"):
                        print("Dataset Manager configuration cancelled.")
                        return DatasetManagerConfig(enabled=False)
                    continue
                
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
                        action = self._prompt_choice(
                            "What would you like to do?",
                            choices=["rename", "cancel"],
                            default="rename"
                        )
                        if action == "rename":
                            continue  # Loop to ask for different name
                        else:
                            print("Dataset Manager configuration cancelled.")
                            return DatasetManagerConfig(enabled=False)
                    
                    action = self._prompt_choice(
                        "What would you like to do?",
                        choices=["fix", "rename", "cancel"],
                        default="fix"
                    )
                    
                    if action == "fix":
                        if self._fix_junction_path(root_volume_name, expected_junction):
                            print(f"Junction path fixed to '{expected_junction}'")
                            break
                        else:
                            print("Failed to fix junction path.")
                            continue
                    elif action == "rename":
                        continue  # Loop to ask for different name
                    else:
                        print("Dataset Manager configuration cancelled.")
                        return DatasetManagerConfig(enabled=False)
                else:
                    print(f"✓ Volume '{root_volume_name}' found with correct junction path '{junction_path}'")
                    break
                    
            except Exception as e:
                print(f"Error checking volume: {e}")
                if not self._prompt_yes_no("Would you like to try a different name?"):
                    print("Dataset Manager configuration cancelled.")
                    return DatasetManagerConfig(enabled=False)
                continue
        
        # Get local mountpoint
        root_mountpoint = self._prompt_required("Local mountpoint path for Dataset Manager 'root' volume")
        
        # Handle mounting with proper validation
        self._handle_root_volume_mounting(root_volume_name, root_mountpoint)
        
        return DatasetManagerConfig(
            enabled=True,
            root_volume_name=root_volume_name,
            root_mountpoint=root_mountpoint
        )
    
    def _create_new_root_volume(self) -> DatasetManagerConfig:
        """Create a new root volume with full setup."""
        while True:  # Loop for retrying with different names
            # 1. Collect inputs
            root_volume_name = self._prompt_with_default("Desired Dataset Manager 'root' volume name", "dataset_mgr_root")
            
            # 2. Preflight checks
            try:
                # Check if volume already exists
                existing_volume = self._get_volume_info(root_volume_name)
                if existing_volume:
                    junction_path = existing_volume.get('NFS Mount Target', '')
                    if ':' in junction_path:
                        junction_path = junction_path.split(':', 1)[1]
                    
                    expected_junction = f"/{root_volume_name}"
                    
                    if junction_path == expected_junction:
                        print(f"✓ Volume '{root_volume_name}' already exists with correct junction path.")
                        print("Proceeding with existing volume setup...")
                        break  # Volume is ready, proceed to mounting
                    else:
                        print(f"Volume '{root_volume_name}' exists but has junction path '{junction_path}'")
                        print(f"Expected: '{expected_junction}'")
                        
                        # Check if expected junction is taken by another volume
                        if self._junction_path_exists(expected_junction, exclude_volume=root_volume_name):
                            print(f"Error: Junction path '{expected_junction}' is already in use by another volume.")
                            if not self._prompt_yes_no("Would you like to choose a different root volume name?"):
                                print("Dataset Manager configuration cancelled.")
                                return DatasetManagerConfig(enabled=False)
                            continue  # Retry with different name
                        
                        if self._prompt_yes_no("Reuse this volume by fixing its junction path?"):
                            if self._fix_junction_path(root_volume_name, expected_junction):
                                print(f"Junction path fixed to '{expected_junction}'")
                                break  # Volume is ready, proceed to mounting
                            else:
                                print("Failed to fix junction path.")
                                if not self._prompt_yes_no("Would you like to choose a different root volume name?"):
                                    print("Dataset Manager configuration cancelled.")
                                    return DatasetManagerConfig(enabled=False)
                                continue  # Retry with different name
                        else:
                            if not self._prompt_yes_no("Would you like to choose a different root volume name?"):
                                print("Dataset Manager configuration cancelled.")
                                return DatasetManagerConfig(enabled=False)
                            continue  # Retry with different name
                else:
                    # Check junction path collision
                    expected_junction = f"/{root_volume_name}"
                    if self._junction_path_exists(expected_junction):
                        print(f"Error: Junction path '{expected_junction}' is already in use by another volume.")
                        if not self._prompt_yes_no("Would you like to choose a different root volume name?"):
                            print("Dataset Manager configuration cancelled.")
                            return DatasetManagerConfig(enabled=False)
                        continue  # Retry with different name
                    
                    # 3. Create the root volume
                    print(f"\nCreating Dataset Manager root volume '{root_volume_name}'...")
                    if not self._create_root_volume_on_ontap(root_volume_name):
                        print("Failed to create root volume.")
                        if not self._prompt_yes_no("Would you like to try with a different name?"):
                            print("Dataset Manager configuration cancelled.")
                            return DatasetManagerConfig(enabled=False)
                        continue  # Retry with different name
                    
                    print(f"✓ Root volume '{root_volume_name}' created successfully")
                    break  # Volume created successfully
            
            except Exception as e:
                print(f"Error during volume operations: {e}")
                if not self._prompt_yes_no("Would you like to try with a different name?"):
                    print("Dataset Manager configuration cancelled.")
                    return DatasetManagerConfig(enabled=False)
                continue  # Retry with different name
        
        # 4. Get local mountpoint and handle mounting
        while True:
            root_mountpoint = self._prompt_required("Local mountpoint path for Dataset Manager 'root' volume")
            
            # Check if mountpoint is already used by wrong volume
            if self._is_mounted(root_mountpoint):
                mounted_target = self._get_mount_target(root_mountpoint)
                expected_target = f"/{root_volume_name}"
                
                if expected_target not in mounted_target:
                    print(f"Warning: Mountpoint '{root_mountpoint}' is already in use by '{mounted_target}'")
                    if self._prompt_yes_no("Choose a different mountpoint?"):
                        continue
                    elif not self._prompt_yes_no("Continue with this mountpoint anyway?"):
                        print("Dataset Manager configuration cancelled.")
                        return DatasetManagerConfig(enabled=False)
            break
        
        # 5. Handle mounting with proper validation
        self._handle_root_volume_mounting(root_volume_name, root_mountpoint)
        
        return DatasetManagerConfig(
            enabled=True,
            root_volume_name=root_volume_name,
            root_mountpoint=root_mountpoint
        )
    
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
                if exclude_volume and volume.get("Volume Name") == exclude_volume:
                    continue
                    
                nfs_target = volume.get('NFS Mount Target', '')
                if ':' in nfs_target:
                    vol_junction_path = nfs_target.split(':', 1)[1]
                    if vol_junction_path == junction_path:
                        return True
            return False
        except Exception as e:
            print(f"Error checking junction path existence: {e}")
            return False
    
    def _fix_junction_path(self, volume_name: str, new_junction_path: str) -> bool:
        """Fix the junction path of an existing volume."""
        try:
            from ..traditional.core import _retrieve_config, _instantiate_connection
            
            # Get config and establish connection
            config = _retrieve_config(print_output=False)
            _instantiate_connection(config=config, connectionType="ONTAP", print_output=False)
            
            # Import here to avoid dependency issues at module load time
            from netapp_ontap.resources import Volume as NetAppVolume
            
            # Find the volume by name
            volume_collection = NetAppVolume.get_collection(svm=config["svm"], name=volume_name)
            volumes = list(volume_collection)
            
            if not volumes:
                print(f"Volume '{volume_name}' not found")
                return False
            
            volume = volumes[0]
            
            # Update the junction path
            volume.nas = {"path": new_junction_path}
            volume.patch()
            
            print(f"Junction path updated to '{new_junction_path}'")
            return True
            
        except Exception as e:
            print(f"Error fixing junction path: {e}")
            return False
    
    def _create_root_volume_on_ontap(self, volume_name: str) -> bool:
        """Create the root volume on ONTAP with appropriate settings."""
        try:
            # Create a small root volume with toolkit defaults
            volume_operations.create_volume(
                volume_name=volume_name,
                volume_size="1GB",  # Minimal size for root volume
                junction=f"/{volume_name}",  # Use 'junction' parameter
                volume_type="flexvol",  # Root volumes are typically flexvol
                snapshot_policy="none",  # No snapshots needed for root
                export_policy="default",
                unix_permissions="0755",  # Slightly more restrictive for root
                unix_uid="0",
                unix_gid="0",
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
    
    def _mount_volume(self, volume_name: str, mountpoint: str) -> bool:
        """Mount the volume to the specified mountpoint."""
        try:
            # Create mountpoint directory if it doesn't exist
            os.makedirs(mountpoint, exist_ok=True)
            
            # First try using the CLI to mount (handles the data LIF and NFS properly)
            result = subprocess.run([
                'python', '-m', 'netapp_dataops.netapp_dataops_cli',
                'mount', 'volume',
                '-n', volume_name,
                '-m', mountpoint
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            
            # If CLI mount fails, try direct NFS mount
            print(f"CLI mount failed, trying direct NFS mount...")
            nfs_target = self._get_expected_nfs_target(volume_name)
            
            result = subprocess.run([
                'sudo', 'mount', '-t', 'nfs', nfs_target, mountpoint
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"Mount command failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error mounting volume: {e}")
            return False
    
    def _handle_root_volume_mounting(self, volume_name: str, mountpoint: str) -> None:
        """Handle one-time mounting of root volume with proper validation."""
        expected_nfs_target = self._get_expected_nfs_target(volume_name)
        
        # Check current mount status
        is_mounted = self._is_mounted(mountpoint)
        
        if is_mounted:
            current_target = self._get_mount_target(mountpoint)
            
            if expected_nfs_target in current_target or f"/{volume_name}" in current_target:
                print(f"✓ Volume '{volume_name}' is already correctly mounted at '{mountpoint}'")
                
                # Check and handle fstab
                self._handle_fstab_setup(volume_name, mountpoint, expected_nfs_target)
                return
            else:
                print(f"Warning: Mountpoint '{mountpoint}' is in use by '{current_target}'")
                print(f"Expected: {expected_nfs_target}")
                
                if not self._prompt_yes_no("Unmount current and mount correct volume?"):
                    print("Skipping mount operation.")
                    return
                
                # Unmount current
                if not self._unmount_volume(mountpoint):
                    print("Failed to unmount. Please unmount manually and re-run configuration.")
                    return
        
        # Mount the volume
        if self._prompt_yes_no(f"Would you like to mount volume '{volume_name}' to '{mountpoint}' now?"):
            if self._mount_volume(volume_name, mountpoint):
                print(f"✓ Volume '{volume_name}' mounted to '{mountpoint}'")
                
                # Handle fstab setup
                self._handle_fstab_setup(volume_name, mountpoint, expected_nfs_target)
            else:
                print(f"Warning: Failed to mount volume. You'll need to mount it manually:")
                print(f"  sudo mount -t nfs {expected_nfs_target} {mountpoint}")
        else:
            print("Skipping mount operation.")
            print(f"To mount manually later: sudo mount -t nfs {expected_nfs_target} {mountpoint}")
    
    def _get_expected_nfs_target(self, volume_name: str) -> str:
        """Get the expected NFS target for a volume."""
        try:
            from ..traditional.core import _retrieve_config
            config = _retrieve_config(print_output=False)
            data_lif = config.get("dataLif", "unknown")
            return f"{data_lif}:/{volume_name}"
        except Exception:
            return f"<data_lif>:/{volume_name}"
    
    def _unmount_volume(self, mountpoint: str) -> bool:
        """Unmount a volume from the specified mountpoint."""
        try:
            result = subprocess.run(['sudo', 'umount', mountpoint], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _handle_fstab_setup(self, volume_name: str, mountpoint: str, nfs_target: str) -> None:
        """Handle fstab setup with intelligent checking and optional auto-editing."""
        if not self._prompt_yes_no("Would you like to make this mount persistent in /etc/fstab?"):
            return
        
        # Check if fstab entry already exists
        fstab_entry = f"{nfs_target} {mountpoint} nfs defaults 0 0"
        
        if self._fstab_entry_exists(mountpoint, volume_name):
            print(f"✓ /etc/fstab already contains an entry for this mount")
            return
        
        print(f"\nTo make the mount persistent, add this line to /etc/fstab:")
        print(f"# Dataset Manager root volume")
        print(f"{fstab_entry}")
        
        # Offer to add automatically if possible
        if self._prompt_yes_no("Would you like to add this entry to /etc/fstab automatically?"):
            if self._add_fstab_entry(fstab_entry):
                print(f"✓ Entry added to /etc/fstab successfully")
            else:
                print("Failed to add entry automatically. Please add manually:")
                print(f"  echo '# Dataset Manager root volume' | sudo tee -a /etc/fstab")
                print(f"  echo '{fstab_entry}' | sudo tee -a /etc/fstab")
        else:
            print("\nTo add manually:")
            print(f"  echo '# Dataset Manager root volume' | sudo tee -a /etc/fstab")
            print(f"  echo '{fstab_entry}' | sudo tee -a /etc/fstab")
    
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
    
    def _add_fstab_entry(self, fstab_entry: str) -> bool:
        """Add entry to /etc/fstab automatically."""
        try:
            # Add comment and entry
            result1 = subprocess.run([
                'sudo', 'sh', '-c', 
                f"echo '# Dataset Manager root volume' >> /etc/fstab"
            ], capture_output=True, text=True)
            
            result2 = subprocess.run([
                'sudo', 'sh', '-c', 
                f"echo '{fstab_entry}' >> /etc/fstab"
            ], capture_output=True, text=True)
            
            return result1.returncode == 0 and result2.returncode == 0
        except Exception:
            return False
    
    def _prompt_required(self, prompt: str) -> str:
        """Prompt for required input with validation."""
        while True:
            value = input(f"{prompt}: ").strip()
            if value:
                return value
            print("This field is required. Please enter a value.")
    
    def _prompt_with_default(self, prompt: str, default: str) -> str:
        """Prompt with default value."""
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    
    def _prompt_password(self, prompt: str) -> str:
        """Prompt for password input (hidden)."""
        while True:
            password = getpass.getpass(f"{prompt}: ")
            if password:
                return password
            print("Password cannot be empty. Please enter a password.")
    
    def _prompt_yes_no(self, prompt: str, default: bool = False) -> bool:
        """Prompt for yes/no input."""
        default_str = "Y/n" if default else "y/N"
        
        while True:
            value = input(f"{prompt} [{default_str}]: ").strip().lower()
            
            if not value:
                return default
            elif value in ['y', 'yes']:
                return True
            elif value in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def _prompt_choice(self, prompt: str, choices: list, default: str = None) -> str:
        """Prompt for choice from list of options."""
        choices_str = "/".join(choices)
        if default:
            choices_str = choices_str.replace(default, default.upper())
            
        while True:
            value = input(f"{prompt} [{choices_str}]: ").strip().lower()
            
            if not value and default:
                return default
            elif value in choices:
                return value
            else:
                print(f"Please choose from: {', '.join(choices)}")
    
    def get_config_summary(self, config: NetAppDataOpsConfig) -> str:
        """
        Get a summary of the configuration for display.
        
        Args:
            config: Configuration to summarize
            
        Returns:
            str: Configuration summary
        """
        summary = []
        summary.append("Configuration Summary:")
        summary.append(f"  ONTAP Host: {config.ontap.hostname}")
        summary.append(f"  SVM: {config.ontap.svm}")
        summary.append(f"  Data LIF: {config.ontap.data_lif}")
        summary.append(f"  Username: {config.ontap.username}")
        summary.append(f"  Default Volume Type: {config.ontap.default_volume_type}")
        
        if config.s3:
            summary.append(f"  S3 Endpoint: {config.s3.endpoint}")
            summary.append(f"  S3 Access Key: {config.s3.access_key_id}")
        
        if config.cloud_sync:
            summary.append("  Cloud Sync: Configured")
        
        if config.dataset_manager and config.dataset_manager.enabled:
            summary.append("  Dataset Manager: Enabled")
            summary.append(f"    Root Volume: {config.dataset_manager.root_volume_name}")
            summary.append(f"    Root Mountpoint: {config.dataset_manager.root_mountpoint}")
        
        return "\n".join(summary)
