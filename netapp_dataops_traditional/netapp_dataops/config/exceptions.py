"""
Configuration-related exceptions for NetApp DataOps Toolkit.

This module defines custom exceptions for configuration management operations.
"""

from typing import Optional


class ConfigError(Exception):
    """Base exception for configuration-related errors."""
    
    def __init__(self, message: str, config_path: Optional[str] = None):
        super().__init__(message)
        self.config_path = config_path


class ConfigValidationError(ConfigError):
    """Exception raised when configuration validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, config_path: Optional[str] = None):
        super().__init__(message, config_path)
        self.field = field


class ConfigNotFoundError(ConfigError):
    """Exception raised when configuration file cannot be found."""
    
    def __init__(self, config_path: str):
        message = f"Configuration file not found: {config_path}"
        super().__init__(message, config_path)


class ConfigParseError(ConfigError):
    """Exception raised when configuration file cannot be parsed."""
    
    def __init__(self, config_path: str, original_error: Exception):
        message = f"Failed to parse configuration file {config_path}: {original_error}"
        super().__init__(message, config_path)
        self.original_error = original_error


class ConfigWriteError(ConfigError):
    """Exception raised when configuration file cannot be written."""
    
    def __init__(self, config_path: str, original_error: Exception):
        message = f"Failed to write configuration file {config_path}: {original_error}"
        super().__init__(message, config_path)
        self.original_error = original_error


class ConfigFileError(ConfigError):
    """Exception raised for general configuration file operations."""
    pass


class ConfigCreationError(ConfigError):
    """Exception raised when configuration creation fails."""
    pass
