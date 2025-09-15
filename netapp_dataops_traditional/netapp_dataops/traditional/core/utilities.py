"""
Utility functions for NetApp DataOps operations.

This module contains general utility functions used across different operations.
"""

import functools
import warnings
import re


def deprecated(func):
    """
    Decorator to mark functions as deprecated.
    """
    @functools.wraps(func)
    def warned_func(*args, **kwargs):
        warnings.warn("Function {} is deprecated.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        return func(*args, **kwargs)
    return warned_func


def _convert_bytes_to_pretty_size(size_in_bytes: str, num_decimal_points: int = 2) -> str :
    # Convert size in bytes to "pretty" size (size in KB, MB, GB, or TB)
    prettySize = float(size_in_bytes) / 1024
    if prettySize >= 1024:
        prettySize = float(prettySize) / 1024
        if prettySize >= 1024:
            prettySize = float(prettySize) / 1024
            if prettySize >= 1024:
                prettySize = float(prettySize) / 1024
                prettySize = round(prettySize, 2)
                prettySize = str(prettySize) + "TB"
            else:
                prettySize = round(prettySize, 2)
                prettySize = str(prettySize) + "GB"
        else:
            prettySize = round(prettySize, 2)
            prettySize = str(prettySize) + "MB"
    else:
        prettySize = round(prettySize, 2)
        prettySize = str(prettySize) + "KB"

    return prettySize


def _convert_size_string_to_bytes(size_string: str) -> int:
    """
    Convert a size string to bytes.
    
    This function provides consistent size parsing across the toolkit,
    using the same logic as volume operations.
    
    Args:
        size_string: Size string like "100GB", "1024MB", "10TB"
        
    Returns:
        Size in bytes as integer
        
    Raises:
        ValueError: If size string format is invalid
    """
    if re.search("^[0-9]+MB$", size_string):
        # Convert from MB to Bytes
        return int(size_string[:len(size_string)-2]) * 1024**2
    elif re.search("^[0-9]+GB$", size_string):
        # Convert from GB to Bytes  
        return int(size_string[:len(size_string)-2]) * 1024**3
    elif re.search("^[0-9]+TB$", size_string):
        # Convert from TB to Bytes
        return int(size_string[:len(size_string)-2]) * 1024**4
    else:
        # Try to parse as plain bytes (for ONTAP responses that might be in bytes)
        try:
            return int(size_string)
        except ValueError:
            raise ValueError(f"Invalid size format '{size_string}'. Acceptable values are '1024MB', '100GB', '10TB', etc.")


def _sizes_are_equivalent(size1: str, size2: str) -> bool:
    """
    Compare two size strings for equivalence after normalizing to bytes.
    
    Handles format differences like "100GB" vs "100 GB" vs bytes representation.
    
    Args:
        size1: First size string to compare
        size2: Second size string to compare
        
    Returns:
        True if sizes are equivalent, False otherwise
    """
    try:
        # Normalize both sizes by removing spaces and converting to uppercase
        normalized_size1 = size1.replace(" ", "").upper()
        normalized_size2 = size2.replace(" ", "").upper()
        
        # Convert both to bytes for comparison
        bytes1 = _convert_size_string_to_bytes(normalized_size1)
        bytes2 = _convert_size_string_to_bytes(normalized_size2)
        
        return bytes1 == bytes2
    except ValueError:
        # If either size can't be parsed, fall back to string comparison
        return size1 == size2
