"""FlexCache operations for NetApp DataOps traditional environments."""

from typing import List
import re

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Flexcache as NetAppFlexCache

from netapp_dataops.logging_utils import setup_logger

from ..exceptions import (
    InvalidConfigError,
    ConnectionTypeError,
    APIConnectionError,
    InvalidVolumeParameterError,
    MountOperationError
)
from ..core import (
    _retrieve_config,
    _instantiate_connection,
    _print_invalid_config_error,
    deprecated
)
from .volume_operations import mount_volume

logger = setup_logger(__name__)


def prepopulate_flex_cache(volume_name: str, paths: List[str], print_output: bool = False) -> None:
    """Prepopulate a FlexCache volume with specified paths.
    
    Args:
        volume_name: Name of the FlexCache volume to prepopulate
        paths: List of directory paths to prepopulate
        print_output: If True, print status messages to console
        
    Raises:
        InvalidConfigError: If configuration is invalid
        ConnectionTypeError: If connection type is not ONTAP
        InvalidVolumeParameterError: If volume name is invalid
        APIConnectionError: If ONTAP API call fails
    """
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
        
    try:
        connectionType = config["connectionType"]
    except KeyError:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            svm = config["svm"]
        except KeyError:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        if print_output:
            logger.info("FlexCache '%s' - Prepopulating paths: %s", volume_name, paths)

        try:
            flexcache = NetAppFlexCache.find(name=volume_name, svm=svm)
            if not flexcache:
                if print_output:
                    logger.error("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            flexcache.prepopulate = {"dir_paths": paths}
            flexcache.patch()

            if print_output:
                logger.info("FlexCache prepopulated successfully.")

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()

def create_flexcache(source_vol: str, source_svm: str, flexcache_vol: str, flexcache_svm: str = None, cluster_name: str = None, flexcache_size: str = None, 
                     junction: str = None, export_policy: str = "default", mountpoint: str = None, readonly: bool = False, print_output: bool = False):
    """
    Creates a FlexCache volume from a specified source volume.

    Required Arguments:
        source_vol (str): Name of the source volume.
        source_svm (str): Name of the source SVM.
        flexcache_vol (str): Name of the FlexCache volume to create.

    Optional Arguments:
        flexcache_svm (str): Name of the FlexCache SVM (defaults to config SVM).
        cluster_name (str): Name of the hosting cluster (defaults to config cluster).
        flexcache_size (str): Size of the FlexCache volume (e.g., '100GB', '10TB'). Default is 10% of source volume size if not specified.
        junction (str): Custom junction path for the FlexCache volume export.
        export_policy (str): NFS export policy to use for the FlexCache volume (default: 'default').
        mountpoint (str): Local mountpoint to mount the FlexCache volume after creation. If not specified, the volume will not be mounted locally. On Linux hosts, must be run as root if specified.
        readonly (bool): Mount the FlexCache volume as read-only if True.
        print_output (bool): Print detailed output if True.

    Raises:
        InvalidConfigError: If configuration is missing or invalid.
        InvalidVolumeParameterError: If provided parameters are invalid.
        APIConnectionError: If there is an error connecting to the API.
        ConnectionTypeError: If the connection type is not supported.
    """
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

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        svm = config["svm"]
        if not flexcache_svm:
            flexcache_svm = svm
        if not export_policy :
            export_policy = config["defaultExportPolicy"]
        
        flexcache_size_bytes = None

        if flexcache_size:
            # Convert volume size to Bytes
            if re.search("^[0-9]+MB$", flexcache_size):
                # Convert from MB to Bytes
                flexcache_size_bytes = int(flexcache_size[:len(flexcache_size)-2]) * 1024**2
            elif re.search("^[0-9]+GB$", flexcache_size):
                # Convert from GB to Bytes
                flexcache_size_bytes = int(flexcache_size[:len(flexcache_size)-2]) * 1024**3
            elif re.search("^[0-9]+TB$", flexcache_size):
                # Convert from TB to Bytes
                flexcache_size_bytes = int(flexcache_size[:len(flexcache_size)-2]) * 1024**4
            else :
                if print_output:
                    logger.error("Error: Invalid flexcache volume size specified. Acceptable values are '1024MB', '100GB', '10TB', etc.")
                raise InvalidVolumeParameterError("size")
            
        # Create option to choose junction path.
        if junction:
            junction = junction
        else:
            junction = "/" + flexcache_vol

        try:
            newFlexCacheDict = {
                "name": flexcache_vol,
                "svm": {"name": flexcache_svm},
                "origins": [{
                    "svm": {"name": source_svm},
                    "volume": {"name": source_vol}
                }],
                "nas": {
                    "export_policy": {"name": export_policy},
                },
                "path": junction
            }
            if flexcache_size_bytes:
                newFlexCacheDict["size"] = flexcache_size_bytes
            if print_output:
                logger.info("Creating FlexCache: %s:%s -> %s:%s", source_svm, source_vol, flexcache_svm, flexcache_vol)
            newFlexCache = NetAppFlexCache.from_dict(newFlexCacheDict)
            newFlexCache.post(poll=True, poll_timeout=120)
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)
        
        # Check if FlexCache was created successfully
        try:
            uuid = None
            relation = None
            flexcache_relationship = NetAppFlexCache.get_collection(**{"name": flexcache_vol, "svm.name": flexcache_svm})
            for relation in flexcache_relationship:
            # Retrieve relationship details
                try:
                    relation.get()
                    uuid = relation.uuid
                except NetAppRestError as err:
                    if print_output:
                        logger.error("Error: ONTAP Rest API Error: %s", err)
                    raise APIConnectionError(err)
            if not uuid:
                if print_output:
                    logger.error("Error: FlexCache was not created: %s:%s", flexcache_svm, flexcache_vol)
                raise InvalidConfigError()
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if print_output:
            logger.info("FlexCache created successfully.")

        # Optionally mount newly created flexcache volume
        if mountpoint:
            try:
                mount_volume(volume_name=flexcache_vol, svm_name=flexcache_svm, mountpoint=mountpoint, readonly=readonly, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                if print_output:
                    logger.error("Error: Error mounting flexcache volume.")
                raise
    else:
        raise ConnectionTypeError()

@deprecated
def prepopulateFlexCache(volumeName: str, paths: List[str], printOutput: bool = False) -> None:
    """Deprecated: Use prepopulate_flex_cache instead."""
    prepopulate_flex_cache(volume_name=volumeName, paths=paths, print_output=printOutput)
