"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Configuration Management

This module provides configuration management for ANF operations, including
interactive config creation and automatic config loading.
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

# Constants
DEFAULT_CONFIG_DIR = "~/.netapp_dataops"
DEFAULT_CONFIG_FILE = "anf_config.json"
DEFAULT_SUBNET_NAME = "default"


class InvalidConfigError(Exception):
    """Exception raised for invalid configuration."""
    pass


def create_anf_config(
    resource_group_name: str = None, 
    account_name: str = None,
    pool_name: str = None,
    location: str = None,
    virtual_network_name: str = None,
    subnet_name: str = DEFAULT_SUBNET_NAME,
    protocol_types: Optional[List[str]] = None,
    print_output: bool = False,
    config_dir_path: str = DEFAULT_CONFIG_DIR,
    config_filename: str = DEFAULT_CONFIG_FILE
) -> Optional[Dict[str, Any]]:
    """
    Create an ANF configuration file. Can work in two modes:
    1. Programmatic mode: When all required parameters are provided
    2. Interactive mode: When no parameters are provided (backward compatibility)
    
    Args:
        resource_group_name (str): Optional. The name of the resource group.
        account_name (str): Optional. The name of the NetApp account.
        pool_name (str): Optional. The name of the capacity pool.
        location (str): Optional. Azure region (e.g., "centralus").
        virtual_network_name (str): Optional. The name of the virtual network.
        subnet_name (str): Optional. The name of the subnet. Defaults to DEFAULT_SUBNET_NAME.
        protocol_types (List[str]): Optional. List of protocol types. Defaults to ["NFSv3"].
        print_output (bool): Optional. Whether to print output messages.
        config_dir_path (str): Directory path for config file. Defaults to DEFAULT_CONFIG_DIR.
        config_filename (str): Config file name. Defaults to DEFAULT_CONFIG_FILE.
        
    Returns:
        Dict[str, Any]: Status and details in programmatic mode, None in interactive mode.
        
    Raises:
        InvalidConfigError: If there's an error creating the config file.
    """
    # If all required parameters for programmatic mode are provided, use programmatic mode
    if all([resource_group_name, account_name, pool_name, location, virtual_network_name]):
        return _create_anf_config_programmatic(
            resource_group_name, account_name, pool_name, 
            location, virtual_network_name, subnet_name, protocol_types, 
            print_output, config_dir_path, config_filename
        )
    else:
        # Use interactive mode for backward compatibility
        create_anf_config_interactive(config_dir_path, config_filename)
        return None


def _create_anf_config_programmatic(
    resource_group_name: str, 
    account_name: str,
    pool_name: str,
    location: str,
    virtual_network_name: str,
    subnet_name: str = DEFAULT_SUBNET_NAME,
    protocol_types: Optional[List[str]] = None,
    print_output: bool = False,
    config_dir_path: str = DEFAULT_CONFIG_DIR,
    config_filename: str = DEFAULT_CONFIG_FILE
) -> Dict[str, Any]:
    """
    Create an ANF configuration file with provided parameters (programmatic mode).
    
    Args:
        resource_group_name (str): The name of the resource group.
        account_name (str): The name of the NetApp account.
        pool_name (str): The name of the capacity pool.
        location (str): Azure region (e.g., "centralus").
        virtual_network_name (str): The name of the virtual network.
        subnet_name (str): Optional. The name of the subnet. Defaults to DEFAULT_SUBNET_NAME.
        protocol_types (List[str]): Optional. List of protocol types. Defaults to ["NFSv3"].
        print_output (bool): Optional. Whether to print output messages.
        config_dir_path (str): Directory path for config file. Defaults to DEFAULT_CONFIG_DIR.
        config_filename (str): Config file name. Defaults to DEFAULT_CONFIG_FILE.
        
    Returns:
        Dict[str, Any]: Status and details of the config creation.
        
    Raises:
        InvalidConfigError: If there's an error creating the config file.
    """
    try:
        # Set default protocol types if not provided
        if protocol_types is None:
            protocol_types = ["NFSv3"]
        
        # Expand config directory path
        config_dir_path = os.path.expanduser(config_dir_path)
        config_file_path = os.path.join(config_dir_path, config_filename)
        
        if print_output:
            logger.info(f"Creating ANF configuration file: {config_file_path}")
        
        # Create configuration dictionary
        config = {
            "resourceGroupName": resource_group_name,
            "accountName": account_name,
            "poolName": pool_name,
            "location": location,
            "virtualNetworkName": virtual_network_name,
            "subnetName": subnet_name,
            "protocolTypes": protocol_types
        }
        
        # Create config directory if it doesn't exist
        try:
            os.makedirs(config_dir_path, exist_ok=True)
        except Exception as e:
            error_msg = f"Failed to create config directory '{config_dir_path}': {str(e)}"
            logger.error(error_msg)
            raise InvalidConfigError(error_msg)
        
        # Write config file
        try:
            with open(config_file_path, 'w') as config_file:
                json.dump(config, config_file, indent=2)
        except Exception as e:
            error_msg = f"Failed to write config file '{config_file_path}': {str(e)}"
            logger.error(error_msg)
            raise InvalidConfigError(error_msg)
        
        if print_output:
            logger.info(f"ANF configuration created successfully: {config_file_path}")
        
        return {
            "status": "success",
            "details": f"Configuration file created: {config_file_path}",
            "config_path": config_file_path,
            "config": config
        }
        
    except InvalidConfigError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error creating ANF config: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error", 
            "details": error_msg
        }


def create_anf_config_interactive(config_dir_path: str = DEFAULT_CONFIG_DIR, config_filename: str = DEFAULT_CONFIG_FILE) -> None:
    """
    Create an ANF configuration file through interactive prompts.
    
    Args:
        config_dir_path (str): Directory path for config file. Defaults to DEFAULT_CONFIG_DIR.
        config_filename (str): Config file name. Defaults to DEFAULT_CONFIG_FILE.
        
    Raises:
        InvalidConfigError: If there's an error creating the config file.
    """
    # Check to see if user has an existing config file
    config_dir_path = os.path.expanduser(config_dir_path)
    config_file_path = os.path.join(config_dir_path, config_filename)
    
    # Print welcome banner
    print("\n" + "=" * 60)
    print("=== NetApp DataOps Toolkit - ANF Configuration Setup ===")
    print("=" * 60)
    print("\nThis wizard will help you create a configuration file for Azure NetApp Files.")
    print(f"The configuration will be saved to: {config_file_path}")
    
    if os.path.isfile(config_file_path):
        print(f"\nWARNING: An existing config file was found at {config_file_path}")
        print("Creating a new config file will overwrite the existing configuration.")
        
        # If existing config file is present, ask user if they want to proceed
        while True:
            proceed = input("\nAre you sure that you want to proceed? (yes/no): ").lower()
            if proceed == "yes":
                break
            elif proceed == "no":
                print("Configuration setup cancelled.")
                sys.exit(0)
            else:
                print("Invalid value. Must enter 'yes' or 'no'.")
    else:
        input("\nPress Enter to continue or Ctrl+C to cancel...")

    # Instantiate dict for storing connection details
    config = dict()

    print("\n" + "=" * 60)
    print("Note: Subscription ID is no longer needed in the config.")
    print("It will be automatically retrieved from Azure CLI.")
    print("Make sure you've run: az login --tenant <TENANT_ID>")
    print("=" * 60)

    # Prompt user to enter infrastructure config details
    print("\n" + "=" * 35)
    print("=== Infrastructure Configuration ===")
    print("=" * 35)
    config["resourceGroupName"] = input("Enter resource group name: ")
    config["accountName"] = input("Enter NetApp account name: ")
    config["poolName"] = input("Enter capacity pool name: ")
    config["location"] = input("Enter Azure region (e.g., 'eastus', 'westus2'): ")

    # Prompt user to enter network configuration
    print("\n" + "=" * 30)
    print("=== Network Configuration ===")
    print("=" * 30)
    config["virtualNetworkName"] = input("Enter virtual network name: ")
    config["subnetName"] = input("Enter subnet name [default]: ") or "default"

    # Prompt user to enter default protocol types
    print("\n" + "=" * 30)
    print("=== Protocol Configuration ===")
    print("=" * 30)
    print("Enter default protocol types (comma-separated):")
    print("  Available options: NFSv3, NFSv4.1, CIFS")
    print("  Example: NFSv3,NFSv4.1")
    
    while True:
        protocol_input = input("  Default [NFSv3]: ") or "NFSv3"
        # Parse comma-separated input
        protocol_types = [p.strip() for p in protocol_input.split(',')]
        
        # Validate protocol types
        valid_protocols = ["NFSv3", "NFSv4.1", "CIFS"]
        invalid_protocols = [p for p in protocol_types if p not in valid_protocols]
        
        if invalid_protocols:
            print(f"Error: Invalid protocol types: {invalid_protocols}")
            print(f"Valid options are: {valid_protocols}")
        else:
            config["protocolTypes"] = protocol_types
            break

    # Display configuration summary
    print("\n" + "=" * 35)
    print("=== Configuration Summary ===")
    print("=" * 35)
    
    print(f"Resource Group: {config['resourceGroupName']}")
    print(f"NetApp Account: {config['accountName']}")
    print(f"Capacity Pool: {config['poolName']}")
    print(f"Location: {config['location']}")
    print(f"Virtual Network: {config['virtualNetworkName']}")
    print(f"Subnet: {config['subnetName']}")
    print(f"Protocol Types: {config['protocolTypes']}")
    print("\nNote: Subscription ID will be retrieved automatically from Azure CLI")

    # Confirm before saving
    while True:
        save_config = input("\nSave this configuration? [y/N]: ").lower()
        if save_config in ['y', 'yes']:
            break
        elif save_config in ['n', 'no', '']:
            print("Configuration setup cancelled.")
            sys.exit(0)
        else:
            print("Please enter 'y' for yes or 'n' for no.")

    # Create config dir if it doesn't already exist
    try:
        os.makedirs(config_dir_path, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create config directory '{config_dir_path}': {str(e)}")
        raise InvalidConfigError(f"Failed to create config directory: {str(e)}")

    # Create config file in config dir
    try:
        with open(config_file_path, 'w') as config_file:
            json.dump(config, config_file, indent=2)
    except Exception as e:
        logger.error(f"Failed to write config file '{config_file_path}': {str(e)}")
        raise InvalidConfigError(f"Failed to write config file: {str(e)}")

    print(f"\nConfiguration saved successfully to: {config_file_path}")
    
    # Display next steps
    print("\n" + "=" * 20)
    print("=== Next Steps ===")
    print("=" * 20)
    print("You can now use simplified function calls:")
    print("  ")
    print("  # Before config - specify all parameters")
    print("  create_volume(")
    print('      volume_name="my-volume",')
    print('      creation_token="my-vol-001",')
    print('      usage_threshold=107374182400,')
    print(f'      resource_group_name="{config["resourceGroupName"]}",')
    print(f'      account_name="{config["accountName"]}",')
    print("      # ... many more parameters")
    print("  )")
    print("  ")
    print("  # After config - specify only unique parameters  ")
    print("  create_volume(")
    print('      volume_name="my-volume",')
    print('      creation_token="my-vol-001",')
    print('      usage_threshold=107374182400')
    print("      # All infrastructure parameters loaded from config!")
    print("  )")
    print("\nConfiguration setup complete!")

    logger.info(f"Created ANF config file: {config_file_path}")


def _retrieve_anf_config(config_dir_path: str = DEFAULT_CONFIG_DIR, config_filename: str = DEFAULT_CONFIG_FILE, 
                        print_output: bool = False) -> Dict[str, Any]:
    """
    Retrieve ANF configuration from config file.
    
    Args:
        config_dir_path (str): Directory path for config file. Defaults to "~/.netapp_dataops".
        config_filename (str): Config file name. Defaults to "anf_config.json".
        print_output (bool): Whether to print debug output.
        
    Returns:
        Dict containing configuration parameters.
        
    Raises:
        InvalidConfigError: If config file is missing or invalid.
    """
    config_dir_path = os.path.expanduser(config_dir_path)
    config_file_path = os.path.join(config_dir_path, config_filename)
    
    if not os.path.isfile(config_file_path):
        error_msg = (f"ANF configuration file not found at '{config_file_path}'. "
                    f"Run create_anf_config() to create configuration file with default values for your ANF environment.")
        if print_output:
            logger.error(error_msg)
        raise InvalidConfigError(error_msg)
    
    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in ANF config file '{config_file_path}': {str(e)}"
        if print_output:
            logger.error(error_msg)
        raise InvalidConfigError(error_msg)
    except Exception as e:
        error_msg = f"Failed to read ANF config file '{config_file_path}': {str(e)}"
        if print_output:
            logger.error(error_msg)
        raise InvalidConfigError(error_msg)
    
    # Validate required config fields
    required_fields = ["resourceGroupName", "accountName", "poolName", 
                      "location", "virtualNetworkName", "subnetName", "protocolTypes"]
    
    missing_fields = [field for field in required_fields if field not in config or not config[field]]
    if missing_fields:
        error_msg = f"Missing required fields in ANF config: {missing_fields}. Please recreate config using create_anf_config()."
        if print_output:
            logger.error(error_msg)
        raise InvalidConfigError(error_msg)
    
    if print_output:
        logger.info("ANF configuration loaded successfully")
    
    return config


def get_config_value(parameter_name: str, function_value: Any, config: Dict[str, Any], 
                    print_output: bool = False) -> Any:
    """
    Get parameter value with function parameter taking precedence over config.
    
    Args:
        parameter_name (str): Name of the parameter.
        function_value (Any): Value passed to function (None if not provided).
        config (Dict[str, Any]): Configuration dictionary.
        print_output (bool): Whether to print debug output.
        
    Returns:
        The resolved parameter value.
        
    Raises:
        InvalidConfigError: If parameter not found in either function call or config.
    """
    # Function parameter takes precedence
    if function_value is not None:
        return function_value
    
    # Map function parameter names to config keys
    config_key_map = {
        'resource_group_name': 'resourceGroupName', 
        'account_name': 'accountName',
        'pool_name': 'poolName',
        'location': 'location',
        'virtual_network_name': 'virtualNetworkName',
        'subnet_name': 'subnetName',
        'protocol_types': 'protocolTypes'
    }
    
    config_key = config_key_map.get(parameter_name, parameter_name)
    
    if config_key in config and config[config_key] is not None:
        return config[config_key]
    
    # Parameter not found in either place
    error_msg = (f"Parameter '{parameter_name}' not provided in function call and not found in config file. "
                f"Either pass the parameter directly or run create_anf_config() to set default values.")
    if print_output:
        logger.error(error_msg)
    raise InvalidConfigError(error_msg)


def _print_invalid_config_error() -> None:
    """Print detailed error message for invalid config."""
    print("\nANF Configuration Error")
    print("Your ANF configuration file is missing or invalid.")
    print("\nTo fix this issue:")
    print("1. Run: from netapp_dataops.traditional.anf.config import create_anf_config")
    print("2. Run: create_anf_config()")
    print("3. Follow the interactive prompts to set up your ANF environment")
    print("\nThis will create a config file with your Azure infrastructure details.")
