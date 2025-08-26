"""
Version command module for NetApp DataOps Toolkit CLI.
"""

from .base_command import BaseCommand
from netapp_dataops import traditional


class VersionCommand(BaseCommand):
    """Handle version command requests."""
    
    def execute(self) -> None:
        """Display the toolkit version."""
        print("NetApp DataOps Toolkit for Traditional Environments - version "
              + traditional.__version__)
