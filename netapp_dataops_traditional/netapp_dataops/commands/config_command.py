"""
Config command module for NetApp DataOps Toolkit CLI.
"""

from .base_command import BaseCommand
from netapp_dataops.help_text import HELP_TEXT_CONFIG


class ConfigCommand(BaseCommand):
    """Handle config/setup command requests."""
    
    def execute(self) -> None:
        """Execute config command to create configuration file."""
        # Check for help flag
        if self.check_help_flag(HELP_TEXT_CONFIG):
            return
        
        # Check for invalid arguments
        if len(self.args) > 2:
            if self.args[2] not in ("-h", "--help"):
                self.handle_invalid_command(HELP_TEXT_CONFIG, invalid_opt_arg=True)
        
        # Set connection type (currently only ONTAP is supported)
        connection_type = "ONTAP"
        
        # Import createConfig function from main module to avoid circular imports
        import importlib.util
        import os
        import sys
        
        # Get the parent directory path and import the main CLI module
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        cli_module_path = os.path.join(parent_dir, 'netapp_dataops_cli.py')
        
        spec = importlib.util.spec_from_file_location("netapp_dataops_cli", cli_module_path)
        cli_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_module)
        
        # Create config file
        cli_module.createConfig(connectionType=connection_type)
