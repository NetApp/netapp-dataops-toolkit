"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Base Utilities

This module contains base utilities and helper functions for ANF operations.
"""

from typing import Any, Dict


def _validate_required_params(**params) -> None:
    """Validate that all required parameters are provided.
    
    Args:
        **params: Dictionary of parameter names and values to validate.
        
    Raises:
        ValueError: If any required parameter is missing or empty.
    """
    missing_params = []
    for name, value in params.items():
        if value is None:
            missing_params.append(name)
        elif isinstance(value, str) and (value == "" or value.strip() == ""):
            missing_params.append(name)
    
    if missing_params:
        param_list = ", ".join(missing_params)
        raise ValueError(f"The following required parameters are missing: {param_list}")


def _serialize(obj: Any) -> Any:
    """
    Serialize an object to a dictionary format for consistent response structure.
    
    Args:
        obj: The object to serialize
        
    Returns:
        Dictionary representation of the object or serializable primitive
    """
    # Handle None
    if obj is None:
        return None
    
    # Handle lists
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return {key: _serialize(value) for key, value in obj.items()}
    
    # Handle Azure SDK objects that have as_dict method
    if hasattr(obj, 'as_dict'):
        return obj.as_dict()
    
    # Handle objects with __dict__ (but not built-in types)
    if hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool)):
        result = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):
                try:
                    result[key] = _serialize(value)
                except (TypeError, AttributeError):
                    # If we can't serialize it, convert to string
                    result[key] = str(value)
        return result
    
    # Handle primitive types and other serializable objects
    try:
        # Test if it's JSON serializable
        import json
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # If not serializable, convert to string
        return str(obj)


def _get_clean_error_message(exception: Exception) -> str:
    """
    Extract clean error message from Azure SDK exceptions.
    
    Azure SDK exceptions contain Code and Message fields that duplicate information
    when converted to string. This function extracts just the core error message
    without the Code/Message duplication.
    
    Args:
        exception: The exception object
        
    Returns:
        str: Clean error message without Code/Message duplication
        
    Example:
        Instead of:
            (ResourceNotFound) Resource not found
            Code: ResourceNotFound
            Message: Resource not found
        
        Returns:
            (ResourceNotFound) Resource not found
    """
    # For Azure SDK exceptions, the full string has multiple lines with Code/Message
    # Extract just the first line which contains the main error message
    error_str = str(exception)
    if '\nCode:' in error_str or '\nMessage:' in error_str:
        # Return only the first line (before the Code: field)
        return error_str.split('\n')[0]
    
    # Try to get the message attribute from Azure SDK exceptions as fallback
    if hasattr(exception, 'message'):
        msg = exception.message
        # Check if message itself has Code/Message duplication
        if isinstance(msg, str) and ('\nCode:' in msg or '\nMessage:' in msg):
            return msg.split('\n')[0]
        return str(msg)
    
    # Fallback to full string representation for other exceptions
    return error_str