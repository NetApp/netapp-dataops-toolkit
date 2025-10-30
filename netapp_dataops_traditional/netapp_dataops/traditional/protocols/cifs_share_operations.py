from typing import Dict, List, Optional
from netapp_ontap.resources import CifsShare as NetAppCifsShare
from netapp_ontap.resources import Svm as NetAppSvm
from netapp_ontap.error import NetAppRestError

class InvalidCifsShareParameterError(Exception):
    """Error that will be raised when an invalid CIFS share parameter is given"""
    pass

def create_cifs_share(
    share_name: str,
    path: str,
    svm_name: str,
    comment: Optional[str] = None,
    acls: Optional[List[Dict]] = None,
    properties: Optional[List[str]] = None,
    print_output: bool = False
) -> NetAppCifsShare:
    """
    Create a CIFS share.
    
    Args:
        share_name (str): Name of the CIFS share
        path (str): Path in the owning SVM namespace that is shared through this share.
        svm_name (str): Existing SVM in which to create the CIFS share.
        comment (str, optional): Comment for the share
        properties (List[str], optional): Share properties (e.g., ['browsable', 'oplocks'])
        acls (List[Dict], optional): Access Control List entries
        print_output (bool): Whether to print output messages
        
    Returns:
        NetAppCifsShare: The created CIFS share object
        
    Raises:
        InvalidCifsShareParameterError: If invalid parameters are provided
        NetAppRestError: If the API request fails
    """
    
    if print_output:
        # logger.info("Creating CIFS share %s at path %s on SVM %s", share_name, path, svm_name)
        pass
    
    try:
        # Verify SVM exists
        svm = NetAppSvm.find(name=svm_name)
        if not svm:
            raise InvalidCifsShareParameterError("SVM %s not found", svm_name)
        
        # Check if CIFS share already exists
        existing_share = NetAppCifsShare.find(name=share_name, svm=svm_name)
        if existing_share:
            raise InvalidCifsShareParameterError("CIFS share %s already exists on SVM %s", share_name, svm_name)
        
        # Create the CIFS share object
        cifs_share = NetAppCifsShare()
        cifs_share.name = share_name
        cifs_share.path = path
        cifs_share.svm = {"name": svm_name}
        
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
                        # logger.warning("Property '%s' may not be valid. Valid properties: %s", prop, valid_properties)
                        pass
            cifs_share.properties = properties
            
        if acls:
            cifs_share.acls = acls
        
        # Create the share
        cifs_share.post(poll=True)
        
        if print_output:
            # logger.info("CIFS share '%s' created successfully", share_name)
            pass
            
        return cifs_share
        
    except NetAppRestError as err:
        error_msg = "Failed to create CIFS share '%s': %s" % (share_name, err)
        if print_output:
            # logger.error(error_msg)
            pass
        raise NetAppRestError(error_msg)
    
    except Exception as err:
        error_msg = "Unexpected error creating CIFS share '%s': %s" % (share_name, err)
        if print_output:
            # logger.error(error_msg)
            pass
        raise InvalidCifsShareParameterError(error_msg)

def list_cifs_shares(
    svm_name: Optional[str] = None,
    name_pattern: Optional[str] = None,
    print_output: bool = False
) -> List[NetAppCifsShare]:
    """
    List all CIFS shares.
    
    Args:
        svm_name (str, optional): Name of the SVM to filter shares
        name_pattern (str, optional): Pattern to filter share names
        print_output (bool): Whether to print output messages
        
    Returns:
        List[NetAppCifsShare]: List of CIFS share objects
        
    Raises:
        NetAppRestError: If the API request fails
        InvalidCifsShareParameterError: If invalid parameters are provided
    """
    
    if print_output:
        # logger.info("Retrieving CIFS shares...")
        pass
    
    try:
        # Build query parameters
        query = {}
        if svm_name:
            # Verify SVM exists
            svm = NetAppSvm.find(name=svm_name)
            if not svm:
                raise InvalidCifsShareParameterError("SVM %s not found", svm_name)
            query['svm.name'] = svm_name
            
        if name_pattern:
            query['name'] = name_pattern
        
        # Get CIFS shares
        if query:
            shares = list(NetAppCifsShare.get_collection(**query))
        else:
            shares = list(NetAppCifsShare.get_collection())
        
        if print_output:
            # logger.info("Found %d CIFS share(s)", len(shares))
            pass
            
        return shares
        
    except NetAppRestError as err:
        error_msg = "Failed to list CIFS shares: %s" % err
        if print_output:
            # logger.error(error_msg)
            pass
        raise NetAppRestError(error_msg)
    
    except Exception as err:
        error_msg = "Unexpected error listing CIFS shares: %s" % err
        if print_output:
            # logger.error(error_msg)
            pass
        raise InvalidCifsShareParameterError(error_msg)


def get_cifs_share(
    share_name: str,
    svm_name: str,
    print_output: bool = False
) -> NetAppCifsShare:
    """
    Get detailed configuration of a specific CIFS share.
    
    Args:
        share_name (str): Name of the CIFS share
        svm_name (str): Name of the Storage Virtual Machine (SVM)
        print_output (bool): Whether to print output messages
        
    Returns:
        NetAppCifsShare: The CIFS share object with detailed configuration
        
    Raises:
        InvalidCifsShareParameterError: If share or SVM not found
        NetAppRestError: If the API request fails
    """
    
    if print_output:
        # logger.info("Retrieving CIFS share %s from SVM %s", share_name, svm_name)
        pass
    
    try:
        # Verify SVM exists
        svm = NetAppSvm.find(name=svm_name)
        if not svm:
            raise InvalidCifsShareParameterError("SVM %s not found", svm_name)
        
        # Find the specific CIFS share
        cifs_share = NetAppCifsShare.find(name=share_name, svm=svm_name)
        
        if not cifs_share:
            raise InvalidCifsShareParameterError("CIFS share %s not found on SVM %s", share_name, svm_name)
        
        # Get detailed information by retrieving the full object
        cifs_share.get()

        if print_output:
            # Log share details
            # logger.info("Share Name: %s", cifs_share.name)
            # logger.info("Path: %s", cifs_share.path)
            # logger.info("SVM: %s", cifs_share.svm.name if hasattr(cifs_share.svm, 'name') else cifs_share.svm)
            # if hasattr(cifs_share, 'comment') and cifs_share.comment:
            #     logger.info("Comment: %s", cifs_share.comment)
            # if hasattr(cifs_share, 'properties') and cifs_share.properties:
            #     logger.info("Properties: %s", cifs_share.properties)
            # if hasattr(cifs_share, 'acls') and cifs_share.acls:
            #     logger.info("ACLs: %s", cifs_share.acls)
            pass
        
        if print_output:
            # logger.info("Successfully retrieved CIFS share %s", share_name)
            pass
            
        return cifs_share
        
    except NetAppRestError as err:
        error_msg = "Failed to get CIFS share '%s': %s" % (share_name, err)
        if print_output:
            # logger.error(error_msg)
            pass
        raise NetAppRestError(error_msg)
    
    except Exception as err:
        error_msg = "Unexpected error getting CIFS share '%s': %s" % (share_name, err)
        if print_output:
            # logger.error(error_msg)
            pass
        raise InvalidCifsShareParameterError(error_msg)