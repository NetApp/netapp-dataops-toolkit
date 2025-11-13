"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Configuration Management

This module provides configuration management for ANF operations, including
interactive config creation and automatic config loading.
"""

import os
import json
import sys
from typing import Dict, Any

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)


class InvalidConfigError(Exception):
    """Exception raised for invalid configuration."""
    pass


def create_anf_config(config_dir_path: str = "~/.netapp_dataops", config_filename: str = "anf_config.json") -> None:
    """
    Create an ANF configuration file through interactive prompts.
    
    Args:
        config_dir_path (str): Directory path for config file. Defaults to "~/.netapp_dataops".
        config_filename (str): Config file name. Defaults to "anf_config.json".
        
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

    # Prompt user to enter Azure subscription details
    print("\n" + "=" * 40)
    print("=== Azure Subscription Configuration ===")
    print("=" * 40)
    config["subscriptionId"] = input("Enter your Azure subscription ID: ")

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
    
    # Mask subscription ID for display
    masked_subscription = config["subscriptionId"][:8] + "-****-****-****-********" + config["subscriptionId"][-4:]
    
    print(f"Subscription ID: {masked_subscription}")
    print(f"Resource Group: {config['resourceGroupName']}")
    print(f"NetApp Account: {config['accountName']}")
    print(f"Capacity Pool: {config['poolName']}")
    print(f"Location: {config['location']}")
    print(f"Virtual Network: {config['virtualNetworkName']}")
    print(f"Subnet: {config['subnetName']}")
    print(f"Protocol Types: {config['protocolTypes']}")

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


def _retrieve_anf_config(config_dir_path: str = "~/.netapp_dataops", config_filename: str = "anf_config.json", 
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
    required_fields = ["subscriptionId", "resourceGroupName", "accountName", "poolName", 
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
        'subscription_id': 'subscriptionId',
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
