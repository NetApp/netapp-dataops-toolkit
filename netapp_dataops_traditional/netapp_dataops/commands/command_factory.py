"""
Command factory for NetApp DataOps Toolkit CLI.

This factory implements the Factory Pattern to create appropriate command instances
based on the provided action string.
"""

from typing import List, Optional
from .base_command import BaseCommand
from .clone_command import CloneCommand
from .config_command import ConfigCommand
from .create_command import CreateCommand
from .delete_command import DeleteCommand
from .get_command import GetCommand
from .list_command import ListCommand
from .mount_command import MountCommand
from .unmount_command import UnmountCommand
from .prepopulate_command import PrepopulateCommand
from .s3_command import S3Command
from .restore_command import RestoreCommand
from .sync_command import SyncCommand
from .help_command import HelpCommand
from .version_command import VersionCommand


class CommandFactory:
    """
    Factory class for creating command instances.
    
    Implements the Factory Pattern to encapsulate command creation logic
    and provide a clean interface for the main CLI dispatcher.
    """
    
    # Command mapping using a dictionary for O(1) lookup
    _command_map = {
        # Clone commands
        "clone": CloneCommand,
        
        # Configuration commands
        "config": ConfigCommand,
        "setup": ConfigCommand,
        
        # Create commands
        "create": CreateCommand,
        
        # Delete commands
        "delete": DeleteCommand,
        "del": DeleteCommand,
        "rm": DeleteCommand,

        # Get commands
        "get": GetCommand,
        
        # List commands
        "list": ListCommand,
        "ls": ListCommand,
        
        # Mount/unmount commands
        "mount": MountCommand,
        "unmount": UnmountCommand,
        
        # Prepopulate commands
        "prepopulate": PrepopulateCommand,
        
        # S3 commands
        "pull-from-s3": S3Command,
        "pull-s3": S3Command,
        "s3-pull": S3Command,
        "push-to-s3": S3Command,
        "push-s3": S3Command,
        "s3-push": S3Command,
        
        # Restore commands
        "restore": RestoreCommand,
        
        # Sync commands
        "sync": SyncCommand,
        
        # Help commands
        "help": HelpCommand,
        "h": HelpCommand,
        "-h": HelpCommand,
        "--help": HelpCommand,
        
        # Version commands
        "version": VersionCommand,
        "v": VersionCommand,
        "-v": VersionCommand,
        "--version": VersionCommand,
    }
    
    @classmethod
    def create_command(cls, action: str, args: List[str]) -> Optional[BaseCommand]:
        """
        Create a command instance based on the action.
        
        Args:
            action: The command action string
            args: Command line arguments
            
        Returns:
            Command instance or None if action not found
        """
        command_class = cls._command_map.get(action)
        if command_class:
            return command_class(action, args)
        return None
    
    @classmethod
    def get_supported_commands(cls) -> List[str]:
        """
        Get list of all supported commands.
        
        Returns:
            List of supported command strings
        """
        return list(cls._command_map.keys())
