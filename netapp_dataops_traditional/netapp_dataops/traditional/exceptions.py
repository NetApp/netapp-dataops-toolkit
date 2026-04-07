"""
Exception classes for NetApp DataOps Traditional operations.

This module contains all custom exceptions used throughout the traditional
package, providing clear error handling and type safety.
"""


class CloudSyncSyncOperationError(Exception) :
    """Error that will be raised when a Cloud Sync sync operation fails"""
    pass

  
class ConnectionTypeError(Exception):
    """Error that will be raised when an invalid connection type is given"""
    pass


class InvalidConfigError(Exception):
    """Error that will be raised when the config file is invalid or missing"""
    pass


class InvalidSnapMirrorParameterError(Exception) :
    """Error that will be raised when an invalid SnapMirror parameter is given"""
    pass


class InvalidSnapshotParameterError(Exception):
    """Error that will be raised when an invalid snapshot parameter is given"""
    pass


class InvalidVolumeParameterError(Exception):
    """Error that will be raised when an invalid volume parameter is given"""
    pass


class MountOperationError(Exception):
    """Error that will be raised when a mount operation fails"""
    pass


class SnapMirrorSyncOperationError(Exception) :
    """Error that will be raised when a SnapMirror sync operation fails"""
    pass


class APIConnectionError(Exception) :
    '''Error that will be raised when an API connection cannot be established'''
    pass

class InvalidCifsShareParameterError(Exception):
    """Error that will be raised when an invalid CIFS share parameter is given"""
    pass