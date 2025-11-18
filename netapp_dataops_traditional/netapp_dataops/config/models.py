"""Configuration data models for NetApp DataOps Toolkit"""

import re
from dataclasses import dataclass
from typing import Optional, Dict, Any

from .exceptions import ConfigValidationError


@dataclass
class ONTAPConfig:
    """Configuration for ONTAP connection and default settings."""
    
    # Connection settings
    hostname: str
    svm: str
    data_lif: str
    username: str
    password: str  # Base64 encoded
    verify_ssl_cert: bool = True
    
    # Default settings for volume operations
    default_volume_type: str = "flexgroup"
    default_export_policy: str = "default"
    default_snapshot_policy: str = "none"
    default_unix_uid: str = "0"
    default_unix_gid: str = "0"
    default_unix_permissions: str = "0777"
    default_aggregate: str = ""
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_required_fields()
        self._validate_volume_type()
        self._validate_unix_permissions()
        self._validate_unix_ids()
    
    def _validate_required_fields(self) -> None:
        """Validate that required fields are not empty."""
        required_fields = ['hostname', 'svm', 'data_lif', 'username', 'password']
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ConfigValidationError(
                    f"Required field '{field_name}' cannot be empty",
                    field=field_name
                )
    
    def _validate_volume_type(self) -> None:
        """Validate volume type is valid."""
        valid_types = ["flexgroup", "flexvol"]
        if self.default_volume_type not in valid_types:
            raise ConfigValidationError(
                f"Invalid volume type '{self.default_volume_type}'. Must be one of: {valid_types}",
                field="default_volume_type"
            )
    
    def _validate_unix_permissions(self) -> None:
        """Validate Unix permissions format."""
        if not re.match(r"^0[0-7]{3}$", self.default_unix_permissions):
            raise ConfigValidationError(
                f"Invalid Unix permissions '{self.default_unix_permissions}'. Must be in format '0777'",
                field="default_unix_permissions"
            )
    
    def _validate_unix_ids(self) -> None:
        """Validate Unix UID and GID are integers."""
        try:
            int(self.default_unix_uid)
        except ValueError as e:
            raise ConfigValidationError(
                f"Invalid Unix UID '{self.default_unix_uid}'. Must be an integer",
                field="default_unix_uid"
            ) from e
        
        try:
            int(self.default_unix_gid)
        except ValueError as e:
            raise ConfigValidationError(
                f"Invalid Unix GID '{self.default_unix_gid}'. Must be an integer",
                field="default_unix_gid"
            ) from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "connectionType": "ONTAP",
            "hostname": self.hostname,
            "svm": self.svm,
            "dataLif": self.data_lif,
            "username": self.username,
            "password": self.password,
            "verifySSLCert": self.verify_ssl_cert,
            "defaultVolumeType": self.default_volume_type,
            "defaultExportPolicy": self.default_export_policy,
            "defaultSnapshotPolicy": self.default_snapshot_policy,
            "defaultUnixUID": self.default_unix_uid,
            "defaultUnixGID": self.default_unix_gid,
            "defaultUnixPermissions": self.default_unix_permissions,
            "defaultAggregate": self.default_aggregate
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ONTAPConfig':
        """Create ONTAPConfig from dictionary."""
        return cls(
            hostname=data.get("hostname", ""),
            svm=data.get("svm", ""),
            data_lif=data.get("dataLif", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            verify_ssl_cert=data.get("verifySSLCert", True),
            default_volume_type=data.get("defaultVolumeType", "flexgroup"),
            default_export_policy=data.get("defaultExportPolicy", "default"),
            default_snapshot_policy=data.get("defaultSnapshotPolicy", "none"),
            default_unix_uid=data.get("defaultUnixUID", "0"),
            default_unix_gid=data.get("defaultUnixGID", "0"),
            default_unix_permissions=data.get("defaultUnixPermissions", "0777"),
            default_aggregate=data.get("defaultAggregate", "")
        )


@dataclass
class S3Config:
    """Configuration for S3 operations."""
    
    endpoint: str
    access_key_id: str
    secret_access_key: str  # Base64 encoded
    verify_ssl_cert: bool = True
    ca_cert_bundle: str = ""
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_required_fields()
    
    def _validate_required_fields(self) -> None:
        """Validate that required fields are not empty."""
        required_fields = ['endpoint', 'access_key_id', 'secret_access_key']
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ConfigValidationError(
                    f"Required S3 field '{field_name}' cannot be empty",
                    field=field_name
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "s3Endpoint": self.endpoint,
            "s3AccessKeyId": self.access_key_id,
            "s3SecretAccessKey": self.secret_access_key,
            "s3VerifySSLCert": self.verify_ssl_cert,
            "s3CACertBundle": self.ca_cert_bundle
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'S3Config':
        """Create S3Config from dictionary."""
        return cls(
            endpoint=data.get("s3Endpoint", ""),
            access_key_id=data.get("s3AccessKeyId", ""),
            secret_access_key=data.get("s3SecretAccessKey", ""),
            verify_ssl_cert=data.get("s3VerifySSLCert", True),
            ca_cert_bundle=data.get("s3CACertBundle", "")
        )


@dataclass
class CloudSyncConfig:
    """Configuration for Cloud Sync operations."""
    
    refresh_token: str  # Base64 encoded
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_required_fields()
    
    def _validate_required_fields(self) -> None:
        """Validate that required fields are not empty."""
        if not self.refresh_token or not self.refresh_token.strip():
            raise ConfigValidationError(
                "Cloud Sync refresh token cannot be empty",
                field="refresh_token"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cloudCentralRefreshToken": self.refresh_token
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloudSyncConfig':
        """Create CloudSyncConfig from dictionary."""
        return cls(
            refresh_token=data.get("cloudCentralRefreshToken", "")
        )


@dataclass
class NetAppDataOpsConfig:
    """Complete NetApp DataOps Toolkit configuration."""
    
    ontap: ONTAPConfig
    s3: Optional[S3Config] = None
    cloud_sync: Optional[CloudSyncConfig] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert complete configuration to dictionary for JSON serialization."""
        config_dict = self.ontap.to_dict()
        
        if self.s3:
            config_dict.update(self.s3.to_dict())
        
        if self.cloud_sync:
            config_dict.update(self.cloud_sync.to_dict())
        
        return config_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetAppDataOpsConfig':
        """Create complete configuration from dictionary."""
        ontap_config = ONTAPConfig.from_dict(data)
        
        # Check if S3 configuration exists
        s3_config = None
        if data.get("s3Endpoint"):
            s3_config = S3Config.from_dict(data)
        
        # Check if Cloud Sync configuration exists
        cloud_sync_config = None
        if data.get("cloudCentralRefreshToken"):
            cloud_sync_config = CloudSyncConfig.from_dict(data)
        
        return cls(
            ontap=ontap_config,
            s3=s3_config,
            cloud_sync=cloud_sync_config
        )

    def has_s3_config(self) -> bool:
        """Check if S3 configuration is available."""
        return self.s3 is not None

    def has_cloud_sync_config(self) -> bool:
        """Check if Cloud Sync configuration is available."""
        return self.cloud_sync is not None
