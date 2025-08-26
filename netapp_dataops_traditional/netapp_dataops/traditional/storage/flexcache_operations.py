"""
FlexCache operations for NetApp DataOps traditional environments.

This module contains FlexCache-related operations including prepopulate functionality.
"""

import functools

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Flexcache as NetAppFlexCache

from ..exceptions import (
    InvalidConfigError, 
    ConnectionTypeError, 
    APIConnectionError,
    InvalidVolumeParameterError
)
from ..core import (
    _retrieve_config, 
    _instantiate_connection, 
    _print_invalid_config_error
)


def deprecated(func):
    """
    Decorator to mark functions as deprecated.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import warnings
        warnings.warn(f"Function {func.__name__} is deprecated and will be removed in a future version.",
                     DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    return wrapper


def prepopulate_flex_cache(volume_name: str, paths: list, print_output: bool = False):
    # Retrieve config details from config file
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        # Retrieve svm from config file
        try:
            svm = config["svm"]
        except:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        if print_output:
            print("FlexCache '" + volume_name + "' - Prepopulating paths: ", paths)

        try:
            # Retrieve FlexCache
            flexcache = NetAppFlexCache.find(name=volume_name, svm=svm)
            if not flexcache:
                if print_output:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Prepopulate FlexCache
            flexcache.prepopulate = {"dir_paths": paths}
            flexcache.patch()

            if print_output:
                print("FlexCache prepopulated successfully.")

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


# Backward compatibility functions (deprecated)
@deprecated
def prepopulateFlexCache(volumeName: str, paths: list, printOutput: bool = False):
    prepopulate_flex_cache(volume_name=volumeName, paths=paths, print_output=printOutput)
