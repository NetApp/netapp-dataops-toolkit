"""Utility functions for NetApp DataOps operations."""

import functools
import warnings
from typing import Callable, Any


def deprecated(func: Callable) -> Callable:
    """Decorator to mark functions as deprecated."""
    @functools.wraps(func)
    def warned_func(*args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            f"Function {func.__name__} is deprecated.",
            category=DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return warned_func


def _convert_bytes_to_pretty_size(size_in_bytes: str, num_decimal_points: int = 2) -> str:
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
