"""
Dataset Manager configuration module for NetApp DataOps Toolkit.

This module handles all Dataset Manager specific configuration operations
including root volume creation, mounting, and validation.
"""

import os
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
            # User claims they have existing root - validate and bind
            return self._bind_existing_root_volume()
        else:
            # No existing root - offer to create now
            create_new = PromptUtils.prompt_yes_no("Would you like to create a new Dataset Manager 'root' volume now?")
            if create_new:
                return self._create_new_root_volume()
            else:
                print("Dataset Manager configuration skipped.")
                print("Note: Dataset Manager requires a root volume to function.")
                return DatasetManagerConfig(enabled=False)
    
    def _ensure_nfs_client_available(self) -> bool:
        """
        Check and optionally install NFS client utilities when needed for mounting operations.
        
        Returns:
            bool: True if NFS client utilities are available, False otherwise
        """
        print("\n🔧 Checking system requirements for NFS mounting...")
        
        # Check for mount.nfs binary
        nfs_check = subprocess.run(['which', 'mount.nfs'], capture_output=True, text=True)
        if nfs_check.returncode == 0:
            print("✓ NFS client utilities found.")
            return True
        
        # Also check alternative locations
        nfs_paths = ['/sbin/mount.nfs', '/usr/sbin/mount.nfs', '/bin/mount.nfs']
        for path in nfs_paths:
            if os.path.exists(path):
                print(f"✓ NFS client utilities found at {path}")
                return True
        
        print("⚠️  NFS client utilities not found on this system.")
        print("   NFS client utilities are required for mounting Dataset Manager volumes.")
        
        print("\n📦 Installing NFS client utilities automatically...")
        if self._install_nfs_client():
            # Verify installation worked
            final_check = subprocess.run(['which', 'mount.nfs'], capture_output=True, text=True)
            if final_check.returncode == 0:
                print("✅ NFS client utilities installed and verified successfully.")
                return True
            else:
                print("⚠️  Installation completed but mount.nfs not found in PATH.")
                print("   Please verify installation manually.")
                return False
        else:
            print("❌ Failed to install NFS client utilities automatically.")
            self._show_manual_nfs_installation()
            return False
    
    def _show_manual_nfs_installation(self) -> None:
        """Show manual NFS client installation instructions."""
        print("\n📋 Manual NFS client installation:")
        print("   Ubuntu/Debian: sudo apt update && sudo apt install -y nfs-common")
        print("   RHEL/CentOS:   sudo yum install -y nfs-utils")
        print("   Fedora:        sudo dnf install -y nfs-utils") 
        print("   SUSE:          sudo zypper install -y nfs-client")
        print("\n   After installation, re-run: python -m netapp_dataops.netapp_dataops_cli config")
    
    def _bind_existing_root_volume(self) -> DatasetManagerConfig:
        """Bind to an existing root volume with validation."""
        while True:
            root_volume_name = PromptUtils.prompt_required("Dataset Manager 'root' volume name")
            
            # Verify the volume exists and get its details
            try:
                volume_info = self._get_volume_info(root_volume_name)
                
                if volume_info is None:
                    print(f"Error: Volume '{root_volume_name}' not found on ONTAP.")
                    if not PromptUtils.prompt_yes_no("Would you like to try a different name?"):
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
        
                        print("Dataset Manager configuration cancelled.")
                        return DatasetManagerConfig(enabled=False)
                else:
                    print(f"✓ Volume '{root_volume_name}' found with correct junction path '{junction_path}'")
                    break
                    
            except Exception as e:
                print(f"Error checking volume: {e}")
                if not PromptUtils.prompt_yes_no("Would you like to try a different name?"):
                    print("Dataset Manager configuration cancelled.")
                    return DatasetManagerConfig(enabled=False)
                continue
        
        # Get local mountpoint
        root_mountpoint = PromptUtils.prompt_required("Local mountpoint path for Dataset Manager 'root' volume")
        
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
            root_volume_name = PromptUtils.prompt_with_default("Desired Dataset Manager 'root' volume name", "dataset_mgr_root")
            
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
                else:
                    # Check junction path collision
                    expected_junction = f"/{root_volume_name}"
                    if self._junction_path_exists(expected_junction):
                        print(f"Error: Junction path '{expected_junction}' is already in use by another volume.")
                        if not PromptUtils.prompt_yes_no("Would you like to choose a different root volume name?"):
                            print("Dataset Manager configuration cancelled.")
                            return DatasetManagerConfig(enabled=False)
                        continue  # Retry with different name
                    
                    # 3. Create the root volume
                    print(f"\nCreating Dataset Manager root volume '{root_volume_name}'...")
                    if not self._create_root_volume_on_ontap(root_volume_name):
                        print("Failed to create root volume.")
                        if not PromptUtils.prompt_yes_no("Would you like to try with a different name?"):
                            print("Dataset Manager configuration cancelled.")
                            return DatasetManagerConfig(enabled=False)
                        continue  # Retry with different name
                    
                    print(f"✓ Root volume '{root_volume_name}' created successfully")
                    break  # Volume created successfully
            
            except Exception as e:
                print(f"Error during volume operations: {e}")
                if not PromptUtils.prompt_yes_no("Would you like to try with a different name?"):
                    print("Dataset Manager configuration cancelled.")
                    return DatasetManagerConfig(enabled=False)
                continue  # Retry with different name
        
        # 4. Get local mountpoint and handle mounting
        while True:
            root_mountpoint = PromptUtils.prompt_required("Local mountpoint path for Dataset Manager 'root' volume")
            
            # Check if mountpoint is already used by wrong volume
            if self._is_mounted(root_mountpoint):
                mounted_target = self._get_mount_target(root_mountpoint)
                expected_target = f"/{root_volume_name}"
                
                if expected_target not in mounted_target:
                    print(f"Warning: Mountpoint '{root_mountpoint}' is already in use by '{mounted_target}'")
                    continue
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
    
    def _mount_volume(self, volume_name: str, mountpoint: str) -> bool:
        """Mount the volume to the specified mountpoint."""
        try:
            # Create mountpoint directory if it doesn't exist
            os.makedirs(mountpoint, exist_ok=True)
            print(f"✓ Mountpoint directory '{mountpoint}' ready")
            
            # First try using the CLI to mount (handles the data LIF and NFS properly)
            print("   Attempting CLI mount...")
            result = subprocess.run([
                'python', '-m', 'netapp_dataops.netapp_dataops_cli',
                'mount', 'volume',
                '-n', volume_name,
                '-m', mountpoint
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ CLI mount successful")
                return True
            
            print(f"   CLI mount failed: {result.stderr.strip()}")
            
            # If CLI mount fails, try direct NFS mount
            print("   Attempting direct NFS mount...")
            nfs_target = self._get_expected_nfs_target(volume_name)
            
            result = subprocess.run([
                'sudo', 'mount', '-t', 'nfs', nfs_target, mountpoint
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Direct NFS mount successful")
                return True
            else:
                print(f"Mount command failed: {result.stderr.strip()}")
                return False
                
        except Exception as e:
            print(f"❌ Error during mount operation: {e}")
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
                
                if not PromptUtils.prompt_yes_no("Unmount current and mount correct volume?"):
                    print("Skipping mount operation.")
                    return
                
                # Unmount current
                if not self._unmount_volume(mountpoint):
                    print("Failed to unmount. Please unmount manually and re-run configuration.")
                    return
        
        # Check NFS utilities BEFORE attempting any mount operations
        print("\n🔧 Preparing for volume mounting...")
        if not self._ensure_nfs_client_available():
            print("\nCannot proceed with mounting without NFS client utilities.")
            print(f"To mount manually later: sudo mount -t nfs {expected_nfs_target} {mountpoint}")
            return
        
        # Now attempt to mount the volume
        print(f"\n🔧 Mounting volume '{volume_name}' to '{mountpoint}'...")
        if self._mount_volume(volume_name, mountpoint):
            print(f"✅ Volume '{volume_name}' mounted successfully to '{mountpoint}'")
            
            # Handle fstab setup
            self._handle_fstab_setup(volume_name, mountpoint, expected_nfs_target)
        else:
            print(f"❌ Failed to mount volume automatically.")
            print(f"To mount manually: sudo mount -t nfs {expected_nfs_target} {mountpoint}")
    
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
        if not PromptUtils.prompt_yes_no(f"Would you like to add your Dataset Manager '{volume_name}' volume to /etc/fstab now?"):
            # User declined - show manual instructions
            self._show_manual_fstab_instructions(nfs_target, mountpoint)
            return
        
        # User agreed - verify NFS utilities are available for fstab operations
        # Note: We don't need to re-install here since we already checked before mounting,
        # but we should verify mount.nfs is still available
        nfs_check = subprocess.run(['which', 'mount.nfs'], capture_output=True, text=True)
        if nfs_check.returncode != 0:
            print("⚠️  NFS client utilities not found - fstab entry may not work properly.")
            print("   Adding fstab entry anyway, but mounting may fail until NFS client is installed.")
        
        # User agreed - programmatically update /etc/fstab
        print(f"\n📝 Adding Dataset Manager volume to /etc/fstab...")
        
        # Check if fstab entry already exists
        if self._fstab_entry_exists(mountpoint, volume_name):
            print(f"✓ /etc/fstab already contains an entry for this mount")
            return
        
        # Create production-ready fstab entry with proper NFS options
        fstab_entry = f"{nfs_target} {mountpoint} nfs rw,_netdev,nfsvers=4.1,hard,timeo=600,retrans=2,x-systemd.automount,x-systemd.idle-timeout=600 0 0"
        
        # Ensure mountpoint directory exists
        try:
            os.makedirs(mountpoint, exist_ok=True)
            print(f"✓ Mountpoint directory '{mountpoint}' ready")
        except Exception as e:
            print(f"❌ Failed to create mountpoint directory: {e}")
            self._show_manual_fstab_instructions(nfs_target, mountpoint)
            return
        
        # Add entry to fstab (idempotently, without duplicates)
        if self._add_fstab_entry_safely(fstab_entry, nfs_target, mountpoint):
            print(f"✓ Entry added to /etc/fstab successfully")
            
            # Only attempt to mount from fstab if the volume isn't already mounted
            if not self._is_mounted(mountpoint):
                # Mount immediately using fstab entry
                print(f"🔧 Mounting volume using fstab entry...")
                if self._mount_from_fstab(mountpoint):
                    print(f"✅ Volume '{volume_name}' mounted successfully and will persist across reboots")
                    
                    # Validate the mount
                    if self._validate_mount(mountpoint, nfs_target):
                        print(f"✓ Mount validation successful")
                    else:
                        print(f"⚠️  Mount validation failed - please check manually")
                else:
                    print(f"❌ Failed to mount using fstab entry")
                    print(f"   The fstab entry was added, but the mount failed.")
                    print(f"   This may be due to missing NFS client utilities or network issues.")
                    self._show_manual_fstab_instructions(nfs_target, mountpoint)
            else:
                print(f"✓ Volume is already mounted - fstab entry will ensure persistence across reboots")
        else:
            print("❌ Failed to add entry to /etc/fstab automatically")
            self._show_manual_fstab_instructions(nfs_target, mountpoint)
    
    def _show_manual_fstab_instructions(self, nfs_target: str, mountpoint: str) -> None:
        """Show manual instructions for fstab setup."""
        fstab_entry = f"{nfs_target} {mountpoint} nfs rw,_netdev,nfsvers=4.1,hard,timeo=600,retrans=2,x-systemd.automount,x-systemd.idle-timeout=600 0 0"
        
        print(f"\n📋 Manual setup instructions:")
        print(f"1. Add this line to /etc/fstab:")
        print(f"   # Dataset Manager root volume")
        print(f"   {fstab_entry}")
        print(f"")
        print(f"2. Create mountpoint and mount:")
        print(f"   sudo mkdir -p {mountpoint}")
        print(f"   sudo mount {mountpoint}")
        print(f"")
        print(f"3. Verify the mount:")
        print(f"   mount | grep {mountpoint}")
    
    def _mount_from_fstab(self, mountpoint: str) -> bool:
        """Mount using fstab entry (reads options from /etc/fstab)."""
        try:
            result = subprocess.run([
                'sudo', 'mount', mountpoint
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"Mount command failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error mounting from fstab: {e}")
            return False
    
    def _validate_mount(self, mountpoint: str, expected_target: str) -> bool:
        """Validate that the mount is working correctly."""
        try:
            # Check if mountpoint is mounted
            if not self._is_mounted(mountpoint):
                print(f"❌ Mountpoint '{mountpoint}' is not mounted")
                return False
            
            # Check if the correct target is mounted
            current_target = self._get_mount_target(mountpoint)
            if expected_target not in current_target and mountpoint.split('/')[-1] not in current_target:
                print(f"❌ Wrong target mounted. Expected: {expected_target}, Got: {current_target}")
                return False
            
            # Test write access
            test_file = os.path.join(mountpoint, '.dataset_manager_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return True
            except Exception as e:
                print(f"❌ Write test failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Mount validation error: {e}")
            return False
    
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
                        print(f"⚠️  Replacing existing fstab entry for {mountpoint}")
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
    
    def _detect_os(self) -> str:
        """Detect the operating system type."""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content or 'debian' in content:
                    return 'debian'
                elif 'red hat' in content or 'rhel' in content or 'centos' in content or 'fedora' in content:
                    return 'redhat'
                elif 'suse' in content:
                    return 'suse'
        except:
            pass
        
        # Fallback detection
        import platform
        system = platform.system().lower()
        if system == 'linux':
            # Try to detect package manager
            try:
                subprocess.run(['apt', '--version'], capture_output=True, check=True)
                return 'debian'
            except:
                pass
            try:
                subprocess.run(['yum', '--version'], capture_output=True, check=True)
                return 'redhat'
            except:
                pass
            try:
                subprocess.run(['zypper', '--version'], capture_output=True, check=True)
                return 'suse'
            except:
                pass
        
        return 'unknown'
    
    def _install_nfs_client(self) -> bool:
        """Automatically install NFS client utilities based on the detected OS."""
        os_type = self._detect_os()
        
        print(f"Detected OS type: {os_type}")
        
        install_commands = {
            'debian': ['sudo', 'apt', 'update', '&&', 'sudo', 'apt', 'install', '-y', 'nfs-common'],
            'redhat': ['sudo', 'yum', 'install', '-y', 'nfs-utils'],
            'suse': ['sudo', 'zypper', 'install', '-y', 'nfs-client']
        }
        
        if os_type not in install_commands:
            print(f"Unsupported OS type: {os_type}")
            print("Please install NFS client utilities manually:")
            print("  Ubuntu/Debian: sudo apt install -y nfs-common")
            print("  RHEL/CentOS:   sudo yum install -y nfs-utils")
            print("  SUSE:          sudo zypper install -y nfs-client")
            return False
        
        try:
            print(f"Installing NFS client utilities for {os_type}...")
            
            if os_type == 'debian':
                # For Debian/Ubuntu, run update and install separately
                print("Updating package list...")
                result1 = subprocess.run(['sudo', 'apt', 'update'], 
                                       capture_output=True, text=True)
                if result1.returncode != 0:
                    print(f"Package update failed: {result1.stderr}")
                    return False
                
                print("Installing nfs-common...")
                result2 = subprocess.run(['sudo', 'apt', 'install', '-y', 'nfs-common'], 
                                       capture_output=True, text=True)
                success = result2.returncode == 0
                if not success:
                    print(f"NFS client installation failed: {result2.stderr}")
            else:
                # For other distros, run single command
                result = subprocess.run(install_commands[os_type], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
                if not success:
                    print(f"NFS client installation failed: {result.stderr}")
            
            if success:
                print("✓ NFS client utilities installed successfully")
                
                # Verify installation
                try:
                    result = subprocess.run(['which', 'mount.nfs'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✓ NFS mount helper found at: {result.stdout.strip()}")
                        return True
                    else:
                        print("⚠️  mount.nfs not found after installation")
                        return False
                except:
                    print("⚠️  Could not verify NFS installation")
                    return False
            
            return success
            
        except Exception as e:
            print(f"Error during NFS client installation: {e}")
            return False
