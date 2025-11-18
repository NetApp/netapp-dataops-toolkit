"""Base command class for NetApp DataOps Toolkit CLI commands"""

import sys
from abc import ABC, abstractmethod
from typing import List, NoReturn

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)


class BaseCommand(ABC):
    """Abstract base class implementing the Command Pattern.
    
    Provides common interface and functionality for all CLI commands.
    Each subclass implements specific command logic via the execute() method.
    """
    
    def __init__(self, action: str, args: List[str]) -> None:
        """Initialize the command.
        
        Args:
            action: Primary command action (e.g., 'clone', 'create')
            args: Command line arguments (sys.argv)
        """
        self.action = action
        self.args = args
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command.
        
        Must be implemented by subclasses to define specific command behavior.
        """
        pass
    
    def get_target(self) -> str:
        """Extract target from command arguments.
        
        Most commands follow: command target [options]
        Example: clone volume, create snapshot, list volumes
        
        Returns:
            Target string (e.g., 'volume', 'snapshot')
            
        Raises:
            SystemExit: If target is missing
        """
        try:
            return self.args[2]
        except IndexError:
            self.handle_invalid_command()
    
    def handle_invalid_command(
        self, 
        help_text: str = None, 
        invalid_opt_arg: bool = False
    ) -> NoReturn:
        """Handle invalid command and exit.
        
        Args:
            help_text: Custom help text to display (optional)
            invalid_opt_arg: True if error is invalid option/argument
        """
        if invalid_opt_arg:
            logger.error("Error: Invalid option/argument.")
        else:
            logger.error("Error: Invalid command.")
        
        if help_text:
            logger.error(help_text)
        else:
            from netapp_dataops.help_text import HELP_TEXT_STANDARD
            logger.error(HELP_TEXT_STANDARD)
        
        sys.exit(1)
