from typing import Dict, List, Optional
from netapp_ontap.resources import CifsShare as NetAppCifsShare
from netapp_ontap.resources import Svm as NetAppSvm
from netapp_ontap.resources import Volume as NetAppVolume
from netapp_ontap.error import NetAppRestError
import pandas as pd
from tabulate import tabulate

from ..exceptions import (
    InvalidConfigError,
    ConnectionTypeError, 
    APIConnectionError,
    InvalidCifsShareParameterError
)

from ..core import (
    _retrieve_config, 
    _instantiate_connection, 
    _print_invalid_config_error
)

from ...logging_utils import setup_logger

logger = setup_logger(__name__)

def create_cifs_share(
    name: str,
    volume_name: str,
    svm: str,
    comment: Optional[str] = None,
    acls: Optional[List[Dict]] = None,
    properties: Optional[List[str]] = None,
    cluster_name: Optional[str] = None,
    print_output: bool = False
) -> NetAppCifsShare:
    """
    Create a CIFS share.
    
    Args:
        name (str): Name of the CIFS share
        volume_name (str): Name of the volume to share. The volume's NAS path will be used as the share path.
        svm (str): Existing SVM in which to create the CIFS share.
        comment (str, optional): Comment for the share
        properties (List[str], optional): Share properties as a list of strings. Valid properties include:
            'browsable', 'oplocks', 'showsnapshot', 'changenotify', 'attributecache', 
            'continuously_available', 'encryption'. Example: ['browsable', 'oplocks']
        acls (List[Dict], optional): Access Control List entries as a list of dictionaries. 
            Each dictionary should contain:
            - 'user_or_group' (str): Windows user or group name
            - 'permission' (str): Access level ('no_access', 'read', 'change', 'full_control')
            - 'type' (str, optional): Principal type ('windows', 'unix_user', 'unix_group')
            Example: [{'user_or_group': 'Everyone', 'permission': 'full_control', 'type': 'windows'}]
        cluster_name (str, optional): Non default hosting cluster name
        print_output (bool): Whether to print output messages
        
    Returns:
        NetAppCifsShare: The created CIFS share object
        
    Raises:
        InvalidConfigError: Config file is missing or contains an invalid value
        APIConnectionError: The storage system API returned an error
        InvalidCifsShareParameterError: If invalid parameters are provided
        NetAppRestError: If the API request fails
    """

    # Validate parameter types
    if acls is not None:
        if not isinstance(acls, list):
            raise InvalidCifsShareParameterError("`acls` must be a list of dictionaries")
        for i, acl in enumerate(acls):
            if not isinstance(acl, dict):
                raise InvalidCifsShareParameterError(f"`acls[{i}]` must be a dictionary")
            if 'user_or_group' not in acl:
                raise InvalidCifsShareParameterError(f"`acls[{i}]` must contain 'user_or_group' key")
            if 'permission' not in acl:
                raise InvalidCifsShareParameterError(f"`acls[{i}]` must contain 'permission' key")
            if not isinstance(acl.get('user_or_group'), str):
                raise InvalidCifsShareParameterError(f"`acls[{i}]['user_or_group']` must be a string")
            if not isinstance(acl.get('permission'), str):
                raise InvalidCifsShareParameterError(f"`acls[{i}]['permission']` must be a string")
    
    if properties is not None:
        if not isinstance(properties, list):
            raise InvalidCifsShareParameterError("`properties` must be a list of strings")
        if not all(isinstance(p, str) for p in properties):
            raise InvalidCifsShareParameterError("`properties` must be a list of strings")

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

        if print_output:
            logger.info("Creating CIFS share %s for volume %s on SVM %s", name, volume_name, svm)
        
        try:
            # Verify SVM exists
            svm_object = NetAppSvm.find(name=svm)
            if not svm_object:
                raise InvalidCifsShareParameterError("SVM %s not found" % svm)
            
            # Get volume and retrieve its NAS path
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                raise InvalidCifsShareParameterError("Volume %s not found on SVM %s" % (volume_name, svm))
            
            volume.get(fields="nas.path")
            if not hasattr(volume, 'nas') or not hasattr(volume.nas, 'path'):
                raise InvalidCifsShareParameterError("Volume %s does not have a NAS path configured" % volume_name)
            
            path = volume.nas.path
            
            if print_output:
                logger.info("Using path %s from volume %s", path, volume_name)
            
            # Check if CIFS share already exists
            existing_share = NetAppCifsShare.find(name=name, svm=svm)
            if existing_share:
                raise InvalidCifsShareParameterError("CIFS share %s already exists on SVM %s" % (name, svm))
            
            # Create the CIFS share object
            cifs_share = NetAppCifsShare()
            cifs_share.name = name
            cifs_share.path = path
            cifs_share.svm = {"name": svm}
            
            # Add optional parameters
            if comment:
                cifs_share.comment = comment
                
            if properties:
                # Validate properties - common properties include: browsable, oplocks, etc.
                valid_properties = ['browsable', 'oplocks', 'showsnapshot', 'changenotify', 
                                'attributecache', 'continuously_available', 'encryption']
                for prop in properties:
                    if prop not in valid_properties:
                        if print_output:
                            logger.warning("Property '%s' may not be valid. Valid properties: %s", prop, valid_properties)
                cifs_share.properties = properties
                
            if acls:
                cifs_share.acls = acls
        
            # Create the share
            cifs_share.post(poll=True)
            
            if print_output:
                logger.info("CIFS share '%s' created successfully", name)
                
            return cifs_share
            
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)
    
    else:
        raise ConnectionTypeError()
    

def list_cifs_shares(
    svm: Optional[str] = None,
    name_pattern: Optional[str] = None,
    cluster_name: Optional[str] = None,
    print_output: bool = False
) -> List[NetAppCifsShare]:
    """
    List all CIFS shares.
    
    Args:
        svm (str, optional): Name of the SVM to filter shares
        name_pattern (str, optional): Pattern to filter share names
        cluster_name (str, optional): Non default hosting cluster name
        print_output (bool): Whether to print output messages
        
    Returns:
        List[NetAppCifsShare]: List of CIFS share objects
        
    Raises:
        InvalidConfigError: Config file is missing or contains an invalid value
        APIConnectionError: The storage system API returned an error
        NetAppRestError: If the API request fails
        InvalidCifsShareParameterError: If invalid parameters are provided
    """

    # Define administrative/hidden shares to filter out
    admin_shares = ['c$', 'ipc$', 'admin$', 'print$']

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
    
        if print_output:
            logger.info("Retrieving CIFS shares...")
        
        try:
            # Build query parameters
            query = {}
            if svm:
                # Verify SVM exists
                svm_object = NetAppSvm.find(name=svm)
                if not svm_object:
                    raise InvalidCifsShareParameterError("SVM %s not found" % svm)
                query['svm.name'] = svm
                
            if name_pattern:
                query['name'] = name_pattern
            
            # Get CIFS shares
            if query:
                shares = list(NetAppCifsShare.get_collection(**query))
            else:
                shares = list(NetAppCifsShare.get_collection())

            # Filter out administrative shares
            shares = [share for share in shares if share.name and share.name.strip().lower() not in admin_shares]
            
            # Build a cache of volume paths to names for all relevant SVMs to avoid repeated queries
            volume_path_cache = {}
            if shares:
                # Get unique SVM names from shares
                svm_names = set()
                for share in shares:
                    share.get()
                    svm_name = share.svm.name if hasattr(share.svm, 'name') else str(share.svm)
                    svm_names.add(svm_name)
                
                # Build cache for each SVM
                for svm_name in svm_names:
                    try:
                        volumes = list(NetAppVolume.get_collection(svm=svm_name, fields="name,nas.path"))
                        for vol in volumes:
                            if hasattr(vol, 'nas') and hasattr(vol.nas, 'path'):
                                volume_path_cache[f"{svm_name}:{vol.nas.path}"] = vol.name
                    except:
                        pass
            
            # Construct list of CIFS shares
            sharesList = list()
            for share in shares:
                # Get detailed information for each share (already done above in cache building)
                if not hasattr(share, 'path'):
                    share.get()
                
                # Get SVM name
                svm_name = share.svm.name if hasattr(share.svm, 'name') else str(share.svm)
                
                # Get properties as comma-separated string
                properties_str = ', '.join(share.properties) if hasattr(share, 'properties') and share.properties else ""
                
                # Find volume for this share using the cache
                volume_name = volume_path_cache.get(f"{svm_name}:{share.path}", "")
                
                # Construct dict containing CIFS share details
                shareDict = {
                    "Share Name": share.name,
                    "SVM": svm_name,
                    "Volume Name": volume_name,
                    "Path": share.path,
                    "Comment": share.comment if hasattr(share, 'comment') and share.comment else "",
                    "Properties": properties_str
                }
                
                # Append dict to list of shares
                sharesList.append(shareDict)
            
            if print_output:
                # Convert shares array to Pandas DataFrame and print as table
                if sharesList:
                    sharesDF = pd.DataFrame.from_dict(sharesList, dtype="string")
                    logger.info(tabulate(sharesDF, showindex=False, headers=sharesDF.columns))
                else:
                    logger.info("No CIFS shares found.")
                
            return shares
            
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)
    
    else:
        raise ConnectionTypeError()
    

def get_cifs_share(
    name: str,
    svm: str,
    cluster_name: Optional[str] = None,
    print_output: bool = False
) -> NetAppCifsShare:
    """
    Get detailed configuration of a specific CIFS share.
    
    Args:
        name (str): Name of the CIFS share
        svm (str): Name of the Storage Virtual Machine (SVM)
        cluster_name (str, optional): Non default hosting cluster name
        print_output (bool): Whether to print output messages
        
    Returns:
        NetAppCifsShare: The CIFS share object with detailed configuration
        
    Raises:
        InvalidConfigError: Config file is missing or contains an invalid value
        APIConnectionError: The storage system API returned an error
        InvalidCifsShareParameterError: If share or SVM not found
        NetAppRestError: If the API request fails
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
    
        if print_output:
            logger.info("Retrieving CIFS share %s from SVM %s", name, svm)
        
        try:
            # Verify SVM exists
            svm_object = NetAppSvm.find(name=svm)
            if not svm_object:
                raise InvalidCifsShareParameterError("SVM %s not found" % svm)
            
            # Find the specific CIFS share
            cifs_share = NetAppCifsShare.find(name=name, svm=svm)
            
            if not cifs_share:
                raise InvalidCifsShareParameterError("CIFS share %s not found on SVM %s" % (name, svm))
            
            # Get detailed information by retrieving the full object
            cifs_share.get()

            if print_output:
                # Find volume for this share by matching the path
                volume_name = ""
                try:
                    volumes = list(NetAppVolume.get_collection(svm=svm, fields="name,nas.path"))
                    for vol in volumes:
                        vol.get(fields="nas.path")
                        if hasattr(vol, 'nas') and hasattr(vol.nas, 'path') and vol.nas.path == cifs_share.path:
                            volume_name = vol.name
                            break
                except:
                    pass
                
                # Log share details
                logger.info("Share Name: %s", cifs_share.name)
                logger.info("SVM: %s", cifs_share.svm.name if hasattr(cifs_share.svm, 'name') else cifs_share.svm)
                if volume_name:
                    logger.info("Volume Name: %s", volume_name)
                logger.info("Path: %s", cifs_share.path)
                if hasattr(cifs_share, 'comment') and cifs_share.comment:
                    logger.info("Comment: %s", cifs_share.comment)
                if hasattr(cifs_share, 'properties') and cifs_share.properties:
                    logger.info("Properties: %s", cifs_share.properties)
                if hasattr(cifs_share, 'acls') and cifs_share.acls:
                    logger.info("ACLs: %s", cifs_share.acls)
            
            if print_output:
                logger.info("Successfully retrieved CIFS share %s", name)
                
            return cifs_share
              
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)
    
    else:
        raise ConnectionTypeError()