"""Version command module for NetApp DataOps Toolkit CLI."""

from .base_command import BaseCommand, logger
from netapp_dataops import traditional


class VersionCommand(BaseCommand):
    """Handle version command requests."""
    
    def execute(self) -> None:
        """Display the toolkit version."""
        logger.info("NetApp DataOps Toolkit for Traditional Environments - version "
              + traditional.__version__)
