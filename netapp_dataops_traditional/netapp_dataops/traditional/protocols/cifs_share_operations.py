from typing import Dict, List, Optional
from netapp_ontap.resources import CifsShare as NetAppCifsShare
from netapp_ontap.resources import Svm as NetAppSvm
from netapp_ontap.resources import CifsService as NetAppCifsService
from netapp_ontap.error import NetAppRestError

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

def _check_and_create_cifs_server(
    svm: str,
    workgroup: str = "WORKGROUP",
    cifs_server_name: Optional[str] = None,
    print_output: bool = False
) -> bool:
    """
    Check if CIFS server exists on SVM, create one if it doesn't exist.
    
    Args:
        svm (str): Name of the SVM
        workgroup (str): Workgroup name for the CIFS server (default: WORKGROUP)
        cifs_server_name (str, optional): CIFS server name (default: auto-generated)
        print_output (bool): Whether to print output messages
        
    Returns:
        bool: True if CIFS server exists or was created successfully
        
    Raises:
        InvalidCifsShareParameterError: If unable to create CIFS server
        APIConnectionError: If API request fails
    """
    try:
        # Check if CIFS service already exists
        existing_cifs = NetAppCifsService.find(svm={"name": svm})
      
        if existing_cifs:
            if print_output:
                logger.info("CIFS server already exists on SVM %s", svm)
            return True
        
        # CIFS server doesn't exist, create one
        if print_output:
            logger.info("CIFS server not found on SVM %s. Creating CIFS server...", svm)
        
        # Auto-generate CIFS server name if not provided
        if not cifs_server_name:
            # Use SVM name with CIFS prefix, limited to 15 characters for NetBIOS compatibility
            cifs_server_name = f"CIFS-{svm.upper()}"[:15]
        
        # Create CIFS service object
        cifs_service = NetAppCifsService()
        cifs_service.svm = {"name": svm}
        cifs_service.name = cifs_server_name
        cifs_service.workgroup = workgroup
        
        # Create the CIFS server
        cifs_service.post(poll=True)
        
        if print_output:
            logger.info("CIFS server '%s' created successfully on SVM %s in workgroup '%s'", 
                       cifs_server_name, svm, workgroup)
        
        return True
        
    except NetAppRestError as err:
        error_msg = f"Failed to create CIFS server on SVM {svm}: {err}"
        if print_output:
            logger.error(error_msg)
        raise InvalidCifsShareParameterError(error_msg)


def create_cifs_share(
    name: str,
    path: str,
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
        path (str): Path in the owning SVM namespace that is shared through this share.
        svm (str): Existing SVM in which to create the CIFS share.
        comment (str, optional): Comment for the share
        properties (List[str], optional): Share properties (e.g., ['browsable', 'oplocks'])
        acls (List[Dict], optional): Access Control List entries
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
            logger.info("Creating CIFS share %s at path %s on SVM %s", name, path, svm)
            pass
        
        try:
            # Verify SVM exists
            svm_object = NetAppSvm.find(name=svm)
            if not svm_object:
                raise InvalidCifsShareParameterError("SVM %s not found" % svm)
            
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
                            pass
                cifs_share.properties = properties
                
            if acls:
                cifs_share.acls = acls
        
            # Create the share
            cifs_share.post(poll=True)
            
            if print_output:
                logger.info("CIFS share '%s' created successfully", name)
                pass
                
            return cifs_share
            
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
                pass
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
            pass
        
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
            
            if print_output:
                logger.info("Found %d CIFS share(s)", len(shares))
                pass
                
            return shares
            
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
                pass
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
            pass
        
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
                # Log share details
                logger.info("Share Name: %s", cifs_share.name)
                logger.info("Path: %s", cifs_share.path)
                logger.info("SVM: %s", cifs_share.svm.name if hasattr(cifs_share.svm, 'name') else cifs_share.svm)
                if hasattr(cifs_share, 'comment') and cifs_share.comment:
                    logger.info("Comment: %s", cifs_share.comment)
                if hasattr(cifs_share, 'properties') and cifs_share.properties:
                    logger.info("Properties: %s", cifs_share.properties)
                if hasattr(cifs_share, 'acls') and cifs_share.acls:
                    logger.info("ACLs: %s", cifs_share.acls)
                pass
            
            if print_output:
                logger.info("Successfully retrieved CIFS share %s", name)
                pass
                
            return cifs_share
              
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
                pass
            raise APIConnectionError(err)
    
    else:
        raise ConnectionTypeError()