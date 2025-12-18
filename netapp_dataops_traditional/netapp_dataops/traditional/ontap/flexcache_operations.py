"""FlexCache operations for NetApp DataOps traditional environments."""

from typing import List, Dict, Any, Optional
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
    _convert_bytes_to_pretty_size,
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


def list_flexcaches(cluster_name: str = None, svm_name: str = None, 
                           print_output: bool = False) -> List[Dict[str, Any]]:
    """List all FlexCache volumes with their origin information.
    
    This function retrieves details for all FlexCache volumes in the cluster/SVM, including
    the origin SVM, volume name, cluster information, IP address, size, and state.
    
    Args:
        cluster_name: Name of the cluster to query. If not specified, uses configured cluster.
        svm_name: Name of the SVM to query. If not specified, uses configured SVM.
        print_output: If True, print detailed output to console in a formatted table.
        
    Returns:
        List of dictionaries containing FlexCache information. Each dictionary includes:
            - FlexCache Name: Name of the FlexCache volume
            - FlexCache SVM: Name of the SVM containing the FlexCache
            - Size: Size of the FlexCache volume (pretty formatted)
            - Origin Volume: Name of the origin volume
            - Origin SVM: Name of the origin SVM
            - Origin Cluster: Name of the origin cluster (if available)
            - Origin IP: IP address of the origin (if available)
            - Origin Size: Size of the origin volume (pretty formatted, if available)
            - Origin State: State of the origin volume (if available)
        
    Raises:
        InvalidConfigError: If configuration is invalid
        ConnectionTypeError: If connection type is not ONTAP
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

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            svmname = config["svm"]
            if svm_name:
                svmname = svm_name

            # Retrieve all FlexCache volumes for SVM
            flexcaches = NetAppFlexCache.get_collection(**{"svm.name": svmname})
            
            # Construct list of FlexCache volumes with their origins
            flexcachesList = []
            for flexcache in flexcaches:
                # Get detailed information including origins
                try:
                    flexcache.get(fields="name,uuid,svm.name,svm.uuid,size,origins")
                except NetAppRestError as err:
                    if print_output:
                        logger.error("Error retrieving FlexCache details: %s", err)
                    continue
                
                # Convert size in bytes to "pretty" size (size in KB, MB, GB, or TB)
                prettySize = _convert_bytes_to_pretty_size(size_in_bytes=flexcache.size) if hasattr(flexcache, 'size') else "Unknown"
                
                # Process origin information
                if hasattr(flexcache, 'origins') and flexcache.origins:
                    for origin in flexcache.origins:
                        # Extract volume information
                        originVolumeName = origin.volume.name if (hasattr(origin, 'volume') and hasattr(origin.volume, 'name')) else "N/A"
                        
                        # Extract SVM information
                        originSvmName = origin.svm.name if (hasattr(origin, 'svm') and hasattr(origin.svm, 'name')) else "N/A"
                        
                        # Extract cluster information
                        originClusterName = origin.cluster.name if (hasattr(origin, 'cluster') and hasattr(origin.cluster, 'name')) else ""
                        
                        # Extract IP address
                        originIpAddress = origin.ip_address if hasattr(origin, 'ip_address') else ""
                        
                        # Extract and format origin size
                        originSize = ""
                        if hasattr(origin, 'size'):
                            originSize = _convert_bytes_to_pretty_size(size_in_bytes=origin.size)
                        
                        # Extract origin state
                        originState = origin.state if hasattr(origin, 'state') else ""
                        
                        # Construct dict containing FlexCache details
                        flexcacheDict = {
                            "FlexCache Name": flexcache.name,
                            "FlexCache SVM": flexcache.svm.name if hasattr(flexcache, 'svm') else "N/A",
                            "Size": prettySize,
                            "Origin Volume": originVolumeName,
                            "Origin SVM": originSvmName,
                            "Origin Cluster": originClusterName,
                            "Origin IP": originIpAddress,
                            "Origin Size": originSize,
                            "Origin State": originState
                        }
                        
                        # Append dict to list of FlexCaches
                        flexcachesList.append(flexcacheDict)
                else:
                    # FlexCache with no origin information
                    flexcacheDict = {
                        "FlexCache Name": flexcache.name,
                        "FlexCache SVM": flexcache.svm.name if hasattr(flexcache, 'svm') else "N/A",
                        "Size": prettySize,
                        "Origin Volume": "N/A",
                        "Origin SVM": "N/A",
                        "Origin Cluster": "",
                        "Origin IP": "",
                        "Origin Size": "",
                        "Origin State": ""
                    }
                    flexcachesList.append(flexcacheDict)

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if print_output:
            try:
                import pandas as pd
                from tabulate import tabulate
                flexcachesDF = pd.DataFrame.from_dict(flexcachesList, dtype="string")
                logger.info("\n%s", tabulate(flexcachesDF, showindex=False, headers=flexcachesDF.columns))
            except ImportError:
                logger.info("FlexCache volumes retrieved successfully")
                for fc in flexcachesList:
                    logger.info(fc)
            
        return flexcachesList

    else:
        raise ConnectionTypeError()


def get_flexcache_origin(uuid: str, cluster_name: str = None, print_output: bool = False) -> List[Dict[str, Any]]:
    """Retrieve origin details for a specific FlexCache volume by UUID.
    
    This function retrieves detailed information about the origin volumes of a FlexCache volume,
    using the FlexCache volume's UUID.
    
    Args:
        uuid: UUID of the FlexCache volume (required).
        cluster_name: Name of the cluster to query. If not specified, uses configured cluster.
        print_output: If True, print detailed output to console.
        
    Returns:
        List of dictionaries containing origin information for the FlexCache. Each dictionary includes:
            - Origin Volume: Name of the origin volume
            - Origin UUID: UUID of the origin volume
            - Origin SVM: Name of the origin SVM
            - Origin SVM UUID: UUID of the origin SVM
            - Origin Cluster: Name of the origin cluster
            - Origin Cluster UUID: UUID of the origin cluster
            - IP Address: IP address of the origin
            - Size: Size of the origin volume (pretty formatted)
            - State: State of the origin volume
            - Create Time: Creation timestamp
        
    Raises:
        InvalidConfigError: If configuration is invalid
        ConnectionTypeError: If connection type is not ONTAP
        APIConnectionError: If ONTAP API call fails
        InvalidVolumeParameterError: If FlexCache UUID is invalid
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

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            # Retrieve FlexCache volume by UUID
            flexcache = NetAppFlexCache(uuid=uuid)
            flexcache.get(fields="name,uuid,svm.name,svm.uuid,origins")
            
            if not hasattr(flexcache, 'name'):
                if print_output:
                    logger.error("Error: Invalid FlexCache UUID.")
                raise InvalidVolumeParameterError("uuid")
            
            # Extract FlexCache information
            flexcacheName = flexcache.name if hasattr(flexcache, 'name') else "N/A"
            flexcacheSvm = flexcache.svm.name if (hasattr(flexcache, 'svm') and hasattr(flexcache.svm, 'name')) else "N/A"
            
            # Construct list of origin details
            originsList = []
            
            # Process origin information
            if hasattr(flexcache, 'origins') and flexcache.origins:
                for origin in flexcache.origins:
                    # Extract volume information
                    originVolumeName = origin.volume.name if (hasattr(origin, 'volume') and hasattr(origin.volume, 'name')) else "N/A"
                    originVolumeUuid = origin.volume.uuid if (hasattr(origin, 'volume') and hasattr(origin.volume, 'uuid')) else ""
                    
                    # Extract SVM information
                    originSvmName = origin.svm.name if (hasattr(origin, 'svm') and hasattr(origin.svm, 'name')) else "N/A"
                    originSvmUuid = origin.svm.uuid if (hasattr(origin, 'svm') and hasattr(origin.svm, 'uuid')) else ""
                    
                    # Extract cluster information
                    originClusterName = origin.cluster.name if (hasattr(origin, 'cluster') and hasattr(origin.cluster, 'name')) else ""
                    originClusterUuid = origin.cluster.uuid if (hasattr(origin, 'cluster') and hasattr(origin.cluster, 'uuid')) else ""
                    
                    # Extract IP address
                    originIpAddress = origin.ip_address if hasattr(origin, 'ip_address') else ""
                    
                    # Extract and format origin size
                    originSize = ""
                    if hasattr(origin, 'size'):
                        originSize = _convert_bytes_to_pretty_size(size_in_bytes=origin.size)
                    
                    # Extract origin state
                    originState = origin.state if hasattr(origin, 'state') else ""
                    
                    # Extract create time
                    createTime = str(origin.create_time) if hasattr(origin, 'create_time') else ""
                    
                    # Construct dict containing origin details
                    originDict = {
                        "Origin Volume": originVolumeName,
                        "Origin UUID": originVolumeUuid,
                        "Origin SVM": originSvmName,
                        "Origin SVM UUID": originSvmUuid,
                        "Origin Cluster": originClusterName,
                        "Origin Cluster UUID": originClusterUuid,
                        "IP Address": originIpAddress,
                        "Size": originSize,
                        "State": originState,
                        "Create Time": createTime
                    }
                    
                    # Append dict to list of origins
                    originsList.append(originDict)
            else:
                if print_output:
                    logger.warning("Warning: FlexCache '%s' has no origin information.", flexcacheName)

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if print_output:
            logger.info("FlexCache Volume: %s (SVM: %s)", flexcacheName, flexcacheSvm)
            if originsList:
                logger.info("\nOrigin Details:")
                try:
                    import pandas as pd
                    from tabulate import tabulate
                    originsDF = pd.DataFrame.from_dict(originsList, dtype="string")
                    logger.info("\n%s", tabulate(originsDF, showindex=False, headers=originsDF.columns))
                except ImportError:
                    for idx, origin in enumerate(originsList, 1):
                        logger.info("  %d. %s:%s (Cluster: %s, State: %s, Size: %s)", 
                                  idx, origin["Origin SVM"], origin["Origin Volume"], 
                                  origin["Origin Cluster"], origin["State"], origin["Size"])
            
        return originsList

    else:
        raise ConnectionTypeError()


def update_flexcache(uuid: str = None, volume_name: str = None, svm_name: str = None, 
                     cluster_name: str = None, prepopulate_paths: List[str] = None, 
                     prepopulate_exclude_paths: List[str] = None, writeback_enabled: bool = None,
                     relative_size_enabled: bool = None, relative_size_percentage: int = None,
                     atime_scrub_enabled: bool = None, atime_scrub_period: int = None,
                     cifs_change_notify_enabled: bool = None, print_output: bool = False) -> None:
    """Update properties of a FlexCache volume.
    
    This function updates the configuration of a FlexCache volume. You can specify the FlexCache
    either by UUID or by volume name and SVM name.
    
    Args:
        uuid: UUID of the FlexCache volume. If provided, volume_name and svm_name are ignored.
        volume_name: Name of the FlexCache volume (used if uuid is not provided).
        svm_name: Name of the SVM containing the FlexCache (used if uuid is not provided).
        cluster_name: Name of the cluster to query. If not specified, uses configured cluster.
        prepopulate_paths: List of directory paths to prepopulate in the FlexCache.
        prepopulate_exclude_paths: List of directory paths to exclude from prepopulation.
        writeback_enabled: Enable or disable writeback for the FlexCache volume.
        relative_size_enabled: Enable or disable relative sizing for the FlexCache volume.
        relative_size_percentage: Percentage size of FlexCache relative to origin (1-100).
        atime_scrub_enabled: Enable or disable atime-based scrubbing of inactive files.
        atime_scrub_period: Duration in days after which inactive files can be scrubbed (1-365).
        cifs_change_notify_enabled: Enable or disable CIFS change notification.
        print_output: If True, print status messages to console.
        
    Raises:
        InvalidConfigError: If configuration is invalid
        ConnectionTypeError: If connection type is not ONTAP
        InvalidVolumeParameterError: If volume identifiers or parameters are invalid
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

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            # Determine FlexCache UUID
            flexcache_uuid = uuid
            
            if not flexcache_uuid:
                # Find FlexCache by name and SVM
                if not volume_name:
                    if print_output:
                        logger.error("Error: Either uuid or volume_name must be provided.")
                    raise InvalidVolumeParameterError("uuid or volume_name")
                
                svmname = config["svm"]
                if svm_name:
                    svmname = svm_name
                
                # Find the FlexCache volume
                flexcache = NetAppFlexCache.find(name=volume_name, **{"svm.name": svmname})
                if not flexcache:
                    if print_output:
                        logger.error("Error: FlexCache volume '%s' not found in SVM '%s'.", volume_name, svmname)
                    raise InvalidVolumeParameterError("volume_name")
                
                flexcache_uuid = flexcache.uuid
            else:
                # Validate that the FlexCache exists for the given UUID
                try:
                    flexcache_check = NetAppFlexCache(uuid=flexcache_uuid)
                    flexcache_check.get(fields="name")
                    if not hasattr(flexcache_check, 'name'):
                        if print_output:
                            logger.error("Error: FlexCache volume with UUID '%s' does not exist.", flexcache_uuid)
                        raise InvalidVolumeParameterError("uuid")
                except NetAppRestError as err:
                    if print_output:
                        logger.error("Error: FlexCache volume with UUID '%s' does not exist or is invalid. API Error: %s", flexcache_uuid, err)
                    raise InvalidVolumeParameterError("uuid")
            
            # Build update dictionary with only provided parameters
            update_dict = {}
            
            # Prepopulate configuration
            if prepopulate_paths is not None or prepopulate_exclude_paths is not None:
                prepopulate_config = {}
                if prepopulate_paths is not None:
                    prepopulate_config["dir_paths"] = prepopulate_paths
                if prepopulate_exclude_paths is not None:
                    prepopulate_config["exclude_dir_paths"] = prepopulate_exclude_paths
                update_dict["prepopulate"] = prepopulate_config
            
            # Writeback configuration
            if writeback_enabled is not None:
                update_dict["writeback"] = {"enabled": writeback_enabled}
            
            # Relative size configuration
            if relative_size_enabled is not None or relative_size_percentage is not None:
                relative_size_config = {}
                if relative_size_enabled is not None:
                    relative_size_config["enabled"] = relative_size_enabled
                if relative_size_percentage is not None:
                    if not (1 <= relative_size_percentage <= 100):
                        if print_output:
                            logger.error("Error: relative_size_percentage must be between 1 and 100.")
                        raise InvalidVolumeParameterError("relative_size_percentage")
                    relative_size_config["percentage"] = relative_size_percentage
                update_dict["relative_size"] = relative_size_config
            
            # Atime scrub configuration
            if atime_scrub_enabled is not None or atime_scrub_period is not None:
                atime_scrub_config = {}
                if atime_scrub_enabled is not None:
                    atime_scrub_config["enabled"] = atime_scrub_enabled
                if atime_scrub_period is not None:
                    if not (1 <= atime_scrub_period <= 365):
                        if print_output:
                            logger.error("Error: atime_scrub_period must be between 1 and 365 days.")
                        raise InvalidVolumeParameterError("atime_scrub_period")
                    atime_scrub_config["period"] = atime_scrub_period
                update_dict["atime_scrub"] = atime_scrub_config
            
            # CIFS change notify configuration
            if cifs_change_notify_enabled is not None:
                update_dict["cifs_change_notify"] = {"enabled": cifs_change_notify_enabled}
            
            # Check if there are any updates to apply
            if not update_dict:
                if print_output:
                    logger.warning("Warning: No update parameters provided.")
                return
            
            if print_output:
                logger.info("Updating FlexCache volume (UUID: %s)...", flexcache_uuid)
            
            # Apply the updates
            flexcache = NetAppFlexCache(uuid=flexcache_uuid)
            for key, value in update_dict.items():
                setattr(flexcache, key, value)
            
            flexcache.patch(poll=True, poll_timeout=120)
            
            if print_output:
                logger.info("FlexCache volume updated successfully.")

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
