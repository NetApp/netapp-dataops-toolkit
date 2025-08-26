"""
Utility functions for NetApp DataOps operations.

This module contains general utility functions used across different operations.
"""


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
