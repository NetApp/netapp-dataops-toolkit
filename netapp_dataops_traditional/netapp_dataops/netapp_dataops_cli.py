#!/usr/bin/env python3

import sys
from pathlib import Path

# Only import what's needed for the main CLI and createConfig function
from netapp_dataops.help_text import HELP_TEXT_STANDARD
from netapp_dataops.config import ConfigManager, ConfigError
from netapp_dataops.traditional import ConnectionTypeError


## Function for creating config file
def createConfig(configDirPath: str = "~/.netapp_dataops", configFilename: str = "config.json", connectionType: str = "ONTAP", config_manager: ConfigManager = None):
    """
    Create configuration file using dependency injection with ConfigManager.
    
    This function demonstrates dependency injection by accepting a ConfigManager
    instance, making it more testable and flexible while maintaining compatibility.
    
    Args:
        configDirPath: Directory path for config file
        configFilename: Name of config file
        connectionType: Type of connection (currently only ONTAP)
        config_manager: Injectable ConfigManager instance (optional)
    """
    # If no config manager injected, create default one (Dependency Injection with fallback)
    if config_manager is None:
        # Use pathlib for modern path handling
        config_dir = Path(configDirPath).expanduser()
        config_file_path = config_dir / configFilename
        
        # Create default ConfigManager instance
        config_manager = ConfigManager(str(config_file_path))
    
    # Check if config file already exists
    if config_manager.config_exists():
        print("You already have an existing config file. Creating a new config file will overwrite this existing config.")
        
        # Prompt user to confirm overwrite
        while True:
            proceed = input("Are you sure that you want to proceed? (yes/no): ")
            if proceed.lower() in ("yes", "y"):
                break
            elif proceed.lower() in ("no", "n"):
                sys.exit(0)
            else:
                print("Invalid value. Must enter 'yes' or 'no'.")
    
    # Validate connection type
    if connectionType != "ONTAP":
        raise ConnectionTypeError()
    
    try:
        # Let ConfigManager handle directory creation and configuration management
        config = config_manager.create_interactive_config()
        config_manager.save_config(config)
        
        print(f"Created config file: '{config_manager.config_file}'.")
        
        # Display configuration summary
        print("\n" + config_manager.get_config_summary(config))
        
    except ConfigError as e:
        print(f"Error creating configuration: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error creating configuration: {e}")
        sys.exit(1)


def handleInvalidCommand(helpText: str = HELP_TEXT_STANDARD, invalidOptArg: bool = False):
    """Handle invalid command scenarios and exit."""
    if invalidOptArg:
        print("Error: Invalid option/argument.")
    else:
        print("Error: Invalid command.")
    print(helpText)
    sys.exit(1)


## Main function
if __name__ == '__main__':
    # Get desired action from command line args
    try:
        action = sys.argv[1]
    except:
        handleInvalidCommand()

    # Used Command Pattern and Factory Pattern
    try:
        from netapp_dataops.commands import CommandFactory
        
        # Create command instance using factory
        command = CommandFactory.create_command(action, sys.argv)
        
        if command:
            command.execute()
        else:
            handleInvalidCommand()
            
    except ImportError:
        handleInvalidCommand()

