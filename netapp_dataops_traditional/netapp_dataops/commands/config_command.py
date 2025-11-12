"""Config command for NetApp DataOps Toolkit CLI configuration setup."""

import sys
from pathlib import Path

from .base_command import BaseCommand, logger
from netapp_dataops.help_text import HELP_TEXT_CONFIG
from netapp_dataops.config import ConfigManager
from netapp_dataops.config.exceptions import ConfigError, ConfigCreationError


class ConfigCommand(BaseCommand):
    """Handle interactive configuration file creation for NetApp DataOps Toolkit."""
    
    def execute(self) -> None:
        """Execute config command to create configuration file."""
        # Check for help flag
        if len(self.args) > 2 and self.args[2] in ("-h", "--help"):
            logger.info(HELP_TEXT_CONFIG)
            sys.exit(0)
        
        # Check for invalid arguments
        if len(self.args) > 2:
            self.handle_invalid_command(HELP_TEXT_CONFIG, invalid_opt_arg=True)
        
        try:
            # Set up config file path (in ~/.netapp_dataops/)
            home_dir = Path.home()
            config_dir = home_dir / ".netapp_dataops"
            config_file = config_dir / "config.json"
            
            # Create config manager
            config_manager = ConfigManager(str(config_file))
            
            # Check if config already exists and handle overwrite
            if config_manager.config_exists():
                logger.info("You already have an existing config file. Creating a new config file will overwrite this existing config.")
                
                # Prompt user to confirm overwrite
                while True:
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed.lower() in ("yes", "y"):
                        break
                    elif proceed.lower() in ("no", "n"):
                        return
                    else:
                        logger.info("Invalid value. Must enter 'yes' or 'no'.")
            
            # Create configuration interactively
            logger.info("Creating NetApp DataOps Toolkit configuration...")
            config = config_manager.create_interactive_config()
            
            # Save configuration
            config_manager.save_config(config)
            
            # Display configuration summary
            summary = config_manager.get_config_summary(config)
            logger.info(summary)
            
        except ConfigCreationError as e:
            logger.error(f"Error creating configuration: {e}")
            sys.exit(1)
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
