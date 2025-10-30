"""
Protocol operations for NetApp DataOps Traditional.

This package contains protocol-specific operations for NetApp DataOps Traditional.
Currently, it includes operations for managing CIFS shares.
"""

from .cifs_share_operations import (
    create_cifs_share,
    list_cifs_shares,
    get_cifs_share
)