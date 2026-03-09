"""
Configuration Manager for NetApp DataOps Toolkit.

This module provides the ConfigManager class for handling configuration
lifecycle operations including creation, loading, saving, and validation.
"""

import json
import base64
import getpass
import keyring
import os
import subprocess
from pathlib import Path
from typing import Optional, List

from netapp_dataops.logging_utils import setup_logger
from .models import NetAppDataOpsConfig, ONTAPConfig, S3Config, CloudSyncConfig, DatasetManagerConfig
from .exceptions import (
    ConfigValidationError, 
    ConfigFileError, 
    ConfigCreationError
)
from netapp_dataops.constants import KEYRING_SERVICE_NAME

logger = setup_logger(__name__)
from .dataset_manager import DatasetManagerConfigurator
from .prompt_utils import PromptUtils


class ConfigManager:
    """
    Manages NetApp DataOps Toolkit configuration operations.
    
    Handles configuration file I/O, validation, and user interaction
    for creating and managing configuration settings.
    """
    
    DEFAULT_CONFIG_FILE = "config.json"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_file: Path to configuration file. If None, uses default.
        """
        self.config_file = Path(config_file or self.DEFAULT_CONFIG_FILE)
    
    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_file.exists()
    
    def load_config(self) -> NetAppDataOpsConfig:
        """
        Load configuration from file.
        
        Returns:
            NetAppDataOpsConfig: Loaded configuration
            
        Raises:
            ConfigFileError: If file doesn't exist or can't be read
            ConfigValidationError: If configuration is invalid
        """
        if not self.config_exists():
            raise ConfigFileError(f"Configuration file '{self.config_file}' not found")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return NetAppDataOpsConfig.from_dict(data)
            
        except json.JSONDecodeError as e:
            raise ConfigFileError(f"Invalid JSON in configuration file: {e}")
        except (ConfigValidationError, ValueError) as e:
            raise ConfigValidationError(f"Invalid configuration: {e}")
    
    def save_config(self, config: NetAppDataOpsConfig) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            
        Raises:
            ConfigFileError: If file cannot be written
        """
        try:
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=4)
                
        except IOError as e:
            raise ConfigFileError(f"Cannot write configuration file: {e}")
    
    def create_interactive_config(self) -> NetAppDataOpsConfig:
        """
        Create configuration through interactive prompts.
        
        Returns:
            NetAppDataOpsConfig: Created configuration
            
        Raises:
            ConfigCreationError: If configuration creation fails
        """
        try:
            logger.info("Configuring NetApp DataOps Toolkit\n")
            
            # Create ONTAP configuration
            ontap_config = self._create_ontap_config()
            
            # Optional S3 configuration
            s3_config = None
            if self._prompt_yes_no("Do you intend to use this toolkit to push/pull from S3?"):
                s3_config = self._create_s3_config()
            
            # Optional Cloud Sync configuration
            cloud_sync_config = None
            if self._prompt_yes_no("Do you intend to use this toolkit to trigger Cloud Sync operations?"):
                cloud_sync_config = self._create_cloud_sync_config()
            
            # Optional Dataset Manager configuration
            dataset_manager_config = None
            if PromptUtils.prompt_yes_no("Do you intend to use the toolkit's Dataset Manager functionality?"):
                logger.info("\nDataset Manager Configuration:")
                
                # IMPORTANT: Save base ONTAP config to disk BEFORE Dataset Manager setup
                # This allows Dataset Manager to connect to ONTAP and create volumes
                base_config = NetAppDataOpsConfig(
                    ontap=ontap_config,
                    s3=s3_config,
                    cloud_sync=cloud_sync_config,
                    dataset_manager=None  # Will be added after setup
                )
                self.save_config(base_config)
                
                # Now Dataset Manager can connect to ONTAP using the saved config
                dataset_manager_configurator = DatasetManagerConfigurator()
                dataset_manager_config = dataset_manager_configurator.configure_dataset_manager()
            
            # Create final configuration object
            final_config = NetAppDataOpsConfig(
                ontap=ontap_config,
                s3=s3_config,
                cloud_sync=cloud_sync_config,
                dataset_manager=dataset_manager_config
            )
            
            # Display configuration summary
            summary = self.get_config_summary(final_config)
            logger.info(summary)
            
            return final_config
            
        except Exception as e:
            raise ConfigCreationError(f"Failed to create configuration: {e}")
    
    def _create_ontap_config(self) -> ONTAPConfig:
        """
        Create ONTAP configuration through interactive prompts.
        
        Returns:
            ONTAPConfig: Configured ONTAP settings
        """
        logger.info("ONTAP Connection Settings:")
        
        hostname = self._prompt_required("Enter ONTAP management LIF hostname or IP address (Recommendation: Use SVM management interface)")
        svm = self._prompt_required("Enter SVM (Storage VM) name")
        data_lif = self._prompt_required("Enter SVM NFS data LIF hostname or IP address")
        username = self._prompt_required("Enter ONTAP API username (Recommendation: Use SVM account)")
        passwordString = self._prompt_password("Enter ONTAP API password (Recommendation: Use SVM account)")

        # Store the password securely using keyring
        if username is not None:
            keyring.set_password(KEYRING_SERVICE_NAME, "username", username)
        if passwordString is not None:
            keyring.set_password(KEYRING_SERVICE_NAME, "password", passwordString)

        verify_ssl = self._prompt_yes_no("Verify SSL certificate when calling ONTAP API", default=True)
        
        logger.info("\nVolume Defaults:")
        
        volume_type = self._prompt_choice(
            "Enter default volume type to use when creating new volumes",
            choices=["flexgroup", "flexvol"],
            default="flexgroup"
        )
        
        export_policy = self._prompt_with_default("Enter export policy to use by default when creating new volumes", "default")
        snapshot_policy = self._prompt_with_default("Enter snapshot policy to use by default when creating new volumes", "none")
        unix_uid = self._prompt_with_default("Enter unix filesystem user id (uid) to apply by default when creating new volumes (ex. '0' for root user)", "0")
        unix_gid = self._prompt_with_default("Enter unix filesystem group id (gid) to apply by default when creating new volumes (ex. '0' for root group)", "0")
        unix_permissions = self._prompt_with_default("Enter unix filesystem permissions to apply by default when creating new volumes (ex. '0777' for full read/write permissions for all users and groups)", "0777")
        default_aggregate = self._prompt_with_default("Enter aggregate to use by default when creating new FlexVol volumes", "")
        
        return ONTAPConfig(
            hostname=hostname,
            svm=svm,
            data_lif=data_lif,
            verify_ssl_cert=verify_ssl,
            default_volume_type=volume_type,
            default_export_policy=export_policy,
            default_snapshot_policy=snapshot_policy,
            default_unix_uid=unix_uid,
            default_unix_gid=unix_gid,
            default_unix_permissions=unix_permissions,
            default_aggregate=default_aggregate
        )
    
    def _create_s3_config(self) -> S3Config:
        """
        Create S3 configuration through interactive prompts.
        
        Returns:
            S3Config: Configured S3 settings
        """
        logger.info("\nS3 Configuration:")
        
        endpoint = PromptUtils.prompt_required("S3 endpoint URL")
        access_key_id = PromptUtils.prompt_required("S3 access key ID")
        secret_access_key = PromptUtils.prompt_password("S3 secret access key")
        
        verify_ssl = self._prompt_yes_no("Verify SSL certificate", default=True)
        ca_cert_bundle = self._prompt_with_default("CA certificate bundle (optional)", "")
        
        return S3Config(
            endpoint=endpoint,
            access_key_id=access_key_id,
            secret_access_key=base64.b64encode(secret_access_key.encode()).decode(),
            verify_ssl_cert=verify_ssl,
            ca_cert_bundle=ca_cert_bundle
        )
    
    def _create_cloud_sync_config(self) -> CloudSyncConfig:
        """
        Create Cloud Sync configuration through interactive prompts.
        
        Returns:
            CloudSyncConfig: Configured Cloud Sync settings
        """
        logger.info("\nCloud Sync Configuration:")
        
        refresh_token = PromptUtils.prompt_password("Cloud Central refresh token")
        
        return CloudSyncConfig(
            refresh_token=base64.b64encode(refresh_token.encode()).decode()
        )
    
    def _prompt_required(self, prompt: str) -> str:
        """
        Prompt for required input with validation.
        
        Args:
            prompt: The prompt message to display to the user
            
        Returns:
            str: The validated user input
        """
        while True:
            value = input(f"  {prompt}: ").strip()
            if value:
                return value
            logger.info("  Error: This field is required.")
    
    def _prompt_with_default(self, prompt: str, default: str) -> str:
        """
        Prompt with default value.
        
        Args:
            prompt: The prompt message to display to the user
            default: The default value to use if user provides no input
            
        Returns:
            str: The user input or default value
        """
        value = input(f"  {prompt} [{default}]: ").strip()
        return value if value else default
    
    def _prompt_password(self, prompt: str) -> str:
        """
        Prompt for password input (hidden).
        
        Args:
            prompt: The prompt message to display to the user
            
        Returns:
            str: The password entered by the user
        """
        while True:
            password = getpass.getpass(f"  {prompt}: ")
            if password:
                return password
            logger.info("  Error: Password cannot be empty.")
    
    def _prompt_yes_no(self, prompt: str, default: bool = False) -> bool:
        """
        Prompt for yes/no input.
        
        Args:
            prompt: The prompt message to display to the user
            default: The default value to use if user provides no input
            
        Returns:
            bool: True for yes, False for no
        """
        default_str = "Y/n" if default else "y/N"
        
        while True:
            value = input(f"  {prompt} [{default_str}]: ").strip().lower()
            
            if not value:
                return default
            elif value in ['y', 'yes']:
                return True
            elif value in ['n', 'no']:
                return False
            else:
                logger.info("  Error: Please enter 'y' or 'n'.")
    
    def _prompt_choice(self, prompt: str, choices: List[str], default: Optional[str] = None) -> str:
        """
        Prompt for choice from list of options.
        
        Args:
            prompt: The prompt message to display to the user
            choices: List of valid choices
            default: The default choice if user provides no input
            
        Returns:
            str: The selected choice
        """
        choices_str = "/".join(choices)
        if default:
            choices_str = choices_str.replace(default, default.upper())
            
        while True:
            value = input(f"  {prompt} [{choices_str}]: ").strip().lower()
            
            if not value and default:
                return default
            elif value in choices:
                return value
            else:
                logger.info(f"  Error: Choose from {', '.join(choices)}.")
    
    def get_config_summary(self, config: NetAppDataOpsConfig) -> str:
        """
        Get a summary of the configuration for display.
        
        Args:
            config: Configuration to summarize
            
        Returns:
            str: Configuration summary
        """
        summary = []
        summary.append("\nConfiguration Summary:")
        summary.append(f"  ONTAP Host: {config.ontap.hostname}")
        summary.append(f"  SVM: {config.ontap.svm}")
        summary.append(f"  Data LIF: {config.ontap.data_lif}")
        summary.append(f"  Volume Type: {config.ontap.default_volume_type}")
        summary.append("  Credentials: Stored securely in system keyring")
        
        if config.s3:
            summary.append(f"  S3 Endpoint: {config.s3.endpoint}")
        
        if config.cloud_sync:
            summary.append("  Cloud Sync: Enabled")
        
        if config.dataset_manager and config.dataset_manager.enabled:
            summary.append("  Dataset Manager: Enabled")
            summary.append(f"    Root Volume: {config.dataset_manager.root_volume_name}")
            summary.append(f"    Root Mountpoint: {config.dataset_manager.root_mountpoint}")
        
        return "\n".join(summary)
