"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Base Utilities

This module contains base utilities and helper functions for ANF operations.
"""

from typing import Any, Dict


def validate_required_params(**params) -> None:
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