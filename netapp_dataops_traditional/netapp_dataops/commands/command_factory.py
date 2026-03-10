"""Command factory for NetApp DataOps Toolkit CLI"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .base_command import BaseCommand


class CommandFactory:
    """Factory for creating command instances using lazy loading."""
    
    # Maps command aliases to (module_name, class_name) for lazy import
    _command_modules: Dict[str, Tuple[str, str]] = {
        # Clone commands
        "clone": ("clone_command", "CloneCommand"),
        
        # Configuration commands
        "config": ("config_command", "ConfigCommand"),
        "setup": ("config_command", "ConfigCommand"),
        
        # Create commands
        "create": ("create_command", "CreateCommand"),
        
        # Delete commands
        "delete": ("delete_command", "DeleteCommand"),
        "del": ("delete_command", "DeleteCommand"),
        "rm": ("delete_command", "DeleteCommand"),

        # Get commands
        "get": ("get_command", "GetCommand"),
        
        # Get commands
        "get": ("get_command", "GetCommand"),
        
        # List commands
        "list": ("list_command", "ListCommand"),
        "ls": ("list_command", "ListCommand"),
        
        # Mount/unmount commands
        "mount": ("mount_command", "MountCommand"),
        "unmount": ("unmount_command", "UnmountCommand"),
        
        # Prepopulate commands
        "prepopulate": ("prepopulate_command", "PrepopulateCommand"),
        
        # S3 commands
        "pull-from-s3": ("s3_command", "S3Command"),
        "pull-s3": ("s3_command", "S3Command"),
        "s3-pull": ("s3_command", "S3Command"),
        "push-to-s3": ("s3_command", "S3Command"),
        "push-s3": ("s3_command", "S3Command"),
        "s3-push": ("s3_command", "S3Command"),
        
        # Restore commands
        "restore": ("restore_command", "RestoreCommand"),
        
        # Sync commands
        "sync": ("sync_command", "SyncCommand"),
        
        # Update commands
        "update": ("update_command", "UpdateCommand"),
        
        # Help commands
        "help": ("help_command", "HelpCommand"),
        "h": ("help_command", "HelpCommand"),
        "-h": ("help_command", "HelpCommand"),
        "--help": ("help_command", "HelpCommand"),
        
        # Version commands
        "version": ("version_command", "VersionCommand"),
        "v": ("version_command", "VersionCommand"),
        "-v": ("version_command", "VersionCommand"),
        "--version": ("version_command", "VersionCommand"),
    }
    
    @classmethod
    def create_command(cls, action: str, args: List[str]) -> Optional['BaseCommand']:
        """Create a command instance for the given action.
        
        Args:
            action: The command action string
            args: Command line arguments
            
        Returns:
            Command instance or None if action not found
        """
        command_info = cls._command_modules.get(action)
        if command_info:
            module_name, class_name = command_info
            module = __import__(f"netapp_dataops.commands.{module_name}", fromlist=[class_name])
            command_class = getattr(module, class_name)
            return command_class(action, args)
        return None
