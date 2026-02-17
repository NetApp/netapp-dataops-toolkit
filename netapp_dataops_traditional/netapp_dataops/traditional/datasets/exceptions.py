"""
Exception classes for NetApp DataOps Dataset operations.

This module contains all custom exceptions used for dataset operations,
providing clear error handling and type safety.
"""


class DatasetError(Exception):
    """Base error for dataset operations"""
    pass


class DatasetNotFoundError(DatasetError):
    """Error that will be raised when a dataset is not found"""
    pass


class DatasetExistsError(DatasetError):
    """Error that will be raised when trying to create a dataset that already exists"""
    pass


class DatasetConfigError(DatasetError):
    """Error that will be raised when dataset configuration is invalid"""
    pass


class DatasetVolumeError(DatasetError):
    """Error that will be raised when there's an issue with the underlying volume"""
    pass
