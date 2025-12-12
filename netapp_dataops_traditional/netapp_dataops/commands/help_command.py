"""Help command module for NetApp DataOps Toolkit CLI."""

from .base_command import BaseCommand, logger
from netapp_dataops.help_text import HELP_TEXT_STANDARD


class HelpCommand(BaseCommand):
    """Handle help command requests."""
    
    def execute(self) -> None:
        """Display the standard help text."""
        logger.info(HELP_TEXT_STANDARD)
