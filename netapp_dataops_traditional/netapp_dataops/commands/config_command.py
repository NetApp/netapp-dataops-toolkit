"""
Config command module for NetApp DataOps Toolkit CLI.
"""

import os
import sys
from pathlib import Path

from .base_command import BaseCommand
from netapp_dataops.help_text import HELP_TEXT_CONFIG
from netapp_dataops.config import ConfigManager
from netapp_dataops.config.exceptions import ConfigError, ConfigCreationError
from netapp_dataops.traditional import ConnectionTypeError


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
        
        try:
            # Validate connection type (currently only ONTAP is supported)
            connection_type = "ONTAP"
            if connection_type != "ONTAP":
                raise ConnectionTypeError()
            
            # Set up config file path (in ~/.netapp_dataops/)
            home_dir = Path.home()
            config_dir = home_dir / ".netapp_dataops"
            config_file = config_dir / "config.json"
            
            # Create config manager
            config_manager = ConfigManager(str(config_file))
            
            # Check if config already exists and handle overwrite
            if config_manager.config_exists():
                print(f"Configuration file already exists at: {config_file}")
                print("Creating a new config file will overwrite the existing configuration.")
                
                # Prompt user to confirm overwrite (matching original behavior)
                while True:
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed.lower() in ("yes", "y"):
                        break
                    elif proceed.lower() in ("no", "n"):
                        return
                    else:
                        print("Invalid value. Must enter 'yes' or 'no'.")
            
            # Create configuration interactively
            print("Creating NetApp DataOps Toolkit configuration...")
            config = config_manager.create_interactive_config()
            
            # Save configuration
            config_manager.save_config(config)
            
            print(f"\nConfiguration saved successfully to: {config_file}")
            print("\n" + config_manager.get_config_summary(config))
            
        except ConnectionTypeError:
            print("Error: Unsupported connection type.")
            sys.exit(1)
        except ConfigCreationError as e:
            print(f"Error creating configuration: {e}")
            sys.exit(1)
        except ConfigError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
