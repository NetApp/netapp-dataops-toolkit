"""
Configuration Manager for NetApp DataOps Toolkit.

This module provides the ConfigManager class for handling configuration
lifecycle operations including creation, loading, saving, and validation.
"""

import json
import base64
import getpass
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from .models import NetAppDataOpsConfig, ONTAPConfig, S3Config, CloudSyncConfig, DatasetManagerConfig
from .exceptions import (
    ConfigError, 
    ConfigValidationError, 
    ConfigFileError, 
    ConfigCreationError
)
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
            with open(self.config_file, 'r') as f:
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
            
            with open(self.config_file, 'w') as f:
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
            print("\n=== NetApp DataOps Toolkit Configuration ===\n")
            
            # Create ONTAP configuration
            ontap_config = self._create_ontap_config()
            
            # Optional S3 configuration
            s3_config = None
            if PromptUtils.prompt_yes_no("Do you want to configure S3 settings?"):
                s3_config = self._create_s3_config()
            
            # Optional Cloud Sync configuration
            cloud_sync_config = None
            if PromptUtils.prompt_yes_no("Do you want to configure Cloud Sync settings?"):
                cloud_sync_config = self._create_cloud_sync_config()
            
            # Optional Dataset Manager configuration
            dataset_manager_config = None
            if PromptUtils.prompt_yes_no("Do you intend to use the toolkit's Dataset Manager functionality?"):
                dataset_manager_configurator = DatasetManagerConfigurator()
                dataset_manager_config = dataset_manager_configurator.configure_dataset_manager()
            
            return NetAppDataOpsConfig(
                ontap=ontap_config,
                s3=s3_config,
                cloud_sync=cloud_sync_config,
                dataset_manager=dataset_manager_config
            )
            
        except Exception as e:
            raise ConfigCreationError(f"Failed to create configuration: {e}")
    
    def _create_ontap_config(self) -> ONTAPConfig:
        """Create ONTAP configuration through interactive prompts."""
        print("--- ONTAP Connection Settings ---")
        
        hostname = PromptUtils.prompt_required("ONTAP management or data LIF hostname or IP address")
        svm = PromptUtils.prompt_required("SVM (Storage Virtual Machine) name")
        data_lif = PromptUtils.prompt_required("Data LIF hostname or IP address")
        username = PromptUtils.prompt_required("ONTAP admin username")
        password = PromptUtils.prompt_password("ONTAP admin password")
        
        verify_ssl = PromptUtils.prompt_yes_no("Verify SSL certificate?", default=True)
        
        print("\n--- Default Volume Settings ---")
        
        volume_type = PromptUtils.prompt_choice(
            "Default volume type",
            choices=["flexgroup", "flexvol"],
            default="flexgroup"
        )
        
        export_policy = PromptUtils.prompt_with_default("Default export policy", "default")
        snapshot_policy = PromptUtils.prompt_with_default("Default snapshot policy", "none")
        unix_uid = PromptUtils.prompt_with_default("Default Unix UID", "0")
        unix_gid = PromptUtils.prompt_with_default("Default Unix GID", "0")
        unix_permissions = PromptUtils.prompt_with_default("Default Unix permissions", "0777")
        default_aggregate = PromptUtils.prompt_with_default("Default aggregate (leave empty for auto)", "")
        
        return ONTAPConfig(
            hostname=hostname,
            svm=svm,
            data_lif=data_lif,
            username=username,
            password=base64.b64encode(password.encode()).decode(),
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
        """Create S3 configuration through interactive prompts."""
        print("\n--- S3 Settings ---")
        
        endpoint = PromptUtils.prompt_required("S3 endpoint URL")
        access_key_id = PromptUtils.prompt_required("S3 access key ID")
        secret_access_key = PromptUtils.prompt_password("S3 secret access key")
        
        verify_ssl = PromptUtils.prompt_yes_no("Verify S3 SSL certificate?", default=True)
        ca_cert_bundle = PromptUtils.prompt_with_default("CA certificate bundle path (optional)", "")
        
        return S3Config(
            endpoint=endpoint,
            access_key_id=access_key_id,
            secret_access_key=base64.b64encode(secret_access_key.encode()).decode(),
            verify_ssl_cert=verify_ssl,
            ca_cert_bundle=ca_cert_bundle
        )
    
    def _create_cloud_sync_config(self) -> CloudSyncConfig:
        """Create Cloud Sync configuration through interactive prompts."""
        print("\n--- Cloud Sync Settings ---")
        
        refresh_token = PromptUtils.prompt_password("Cloud Central refresh token")
        
        return CloudSyncConfig(
            refresh_token=base64.b64encode(refresh_token.encode()).decode()
        )
    
    def get_config_summary(self, config: NetAppDataOpsConfig) -> str:
        """
        Get a summary of the configuration for display.
        
        Args:
            config: Configuration to summarize
            
        Returns:
            str: Configuration summary
        """
        summary = []
        summary.append("Configuration Summary:")
        summary.append(f"  ONTAP Host: {config.ontap.hostname}")
        summary.append(f"  SVM: {config.ontap.svm}")
        summary.append(f"  Data LIF: {config.ontap.data_lif}")
        summary.append(f"  Username: {config.ontap.username}")
        summary.append(f"  Default Volume Type: {config.ontap.default_volume_type}")
        
        if config.s3:
            summary.append(f"  S3 Endpoint: {config.s3.endpoint}")
            summary.append(f"  S3 Access Key: {config.s3.access_key_id}")
        
        if config.cloud_sync:
            summary.append("  Cloud Sync: Configured")
        
        if config.dataset_manager and config.dataset_manager.enabled:
            summary.append("  Dataset Manager: Enabled")
            summary.append(f"    Root Volume: {config.dataset_manager.root_volume_name}")
            summary.append(f"    Root Mountpoint: {config.dataset_manager.root_mountpoint}")
        
        return "\n".join(summary)
