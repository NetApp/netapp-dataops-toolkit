"""
Base command class for NetApp DataOps Toolkit CLI commands.

This provides a common interface and shared functionality for all command modules.
"""

import sys
from abc import ABC, abstractmethod
from typing import List, Optional


class BaseCommand(ABC):
    """
    Abstract base class for CLI commands.
    
    Implements the Command Pattern with a consistent interface for all command types.
    Each command subclass handles its specific logic while maintaining a standard API.
    """
    
    def __init__(self, action: str, args: List[str]):
        """
        Initialize the command with action and arguments.
        
        Args:
            action: The primary command action (e.g., 'clone', 'create', etc.)
            args: Command line arguments (sys.argv)
        """
        self.action = action
        self.args = args
    
    @abstractmethod
    def execute(self) -> None:
        """
        Execute the command.
        
        This method must be implemented by each command subclass to define
        the specific behavior for that command type.
        """
        pass
    
    def get_target(self) -> str:
        """
        Extract the target from command line arguments.
        
        Most commands follow the pattern: command target [options]
        For example: clone volume, create snapshot, list volumes
        
        Returns:
            The target string (e.g., 'volume', 'snapshot')
            
        Raises:
            SystemExit: If target is missing
        """
        try:
            return self.args[2]
        except IndexError:
            self.handle_invalid_command()
    
    def handle_invalid_command(self, help_text: str = None, invalid_opt_arg: bool = False) -> None:
        """
        Handle invalid command scenarios and exit.
        
        Args:
            help_text: Custom help text to display
            invalid_opt_arg: Whether the error is due to invalid option/argument
        """
        if invalid_opt_arg:
            print("Error: Invalid option/argument.")
        else:
            print("Error: Invalid command.")
        
        if help_text:
            print(help_text)
        else:
            # Import here to avoid circular imports
            from netapp_dataops.help_text import HELP_TEXT_STANDARD
            print(HELP_TEXT_STANDARD)
        
        sys.exit(1)
    
    def check_help_flag(self, help_text: str) -> bool:
        """
        Check if help flag is present and display help if needed.
        
        Args:
            help_text: The help text to display
            
        Returns:
            True if help was displayed (and program should exit)
            False if no help flag found
        """
        if len(self.args) > 2 and self.args[2] in ("-h", "--help"):
            print(help_text)
            sys.exit(0)
        return False
