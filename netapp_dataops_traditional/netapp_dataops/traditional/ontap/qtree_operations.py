"""NetApp DataOps Toolkit - Qtree Operations for Traditional Environments

This module provides qtree management operations for traditional environments.

This module imports shared utilities and exceptions from the main traditional module
to avoid code duplication and ensure consistency across the toolkit.
"""

import os
from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Qtree as NetAppQtree

# Import shared functions and exceptions from the modular structure
from ..exceptions import (
    InvalidConfigError,
    InvalidVolumeParameterError,
    APIConnectionError,
    ConnectionTypeError
)
from ..core.config import _retrieve_config
from ..core.connection import _instantiate_connection


def create_qtree(qtree_name: str, volume_name: str, cluster_name: str = None, svm_name: str = None,
                 security_style: str = None, unix_permissions: str = None, export_policy: str = None,
                 print_output: bool = False):
    """
    Create a new qtree in a FlexVol or FlexGroup volume.

    Required Arguments:
        qtree_name (str): Name of the qtree to create.
        volume_name (str): Name of the volume in which to create the qtree.

    Optional Arguments:
        cluster_name (str): Name of the hosting cluster (defaults to config cluster).
        svm_name (str): Name of the SVM (defaults to config SVM).
        security_style (str): Security style for the qtree.
        unix_permissions (str): UNIX permissions for the qtree
        export_policy (str): Export policy of the SVM for the qtree.
        print_output (bool): Print detailed output if True.

    Raises:
        InvalidConfigError: If configuration is missing or invalid.
        InvalidVolumeParameterError: If provided parameters are invalid.
        APIConnectionError: If there is an error connecting to the API.

    Returns:
        None
    """
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if print_output:
            print("Error: Missing 'connectionType' in config file.")
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            if not svm_name:
                svm_name = config["svm"]
        except Exception as e:
            if print_output:
                print("Error: Missing required parameters (svm name) in config file.")
                print("Exception: ", e)
            raise InvalidConfigError()

        # Validate unix_permissions format
        if unix_permissions:
            try:
                # Convert octal string to integer to validate format
                permissions_int = int(unix_permissions, 8)
                if permissions_int < 0 or permissions_int > 0o7777:
                    raise ValueError("Permissions out of range")
            except ValueError:
                if print_output:
                    print("Error: Invalid UNIX permissions format. Use octal format (e.g., '0755').")
                raise InvalidVolumeParameterError("Invalid UNIX permissions format")

        # Check if qtree already exists
        try:
            existing_qtrees = NetAppQtree.get_collection(**{"svm.name": svm_name, "volume.name": volume_name, "name": qtree_name})
            existing_qtree_list = list(existing_qtrees)
            if existing_qtree_list:
                if print_output:
                    print("Error: Qtree '" + qtree_name + "' already exists in volume '" + volume_name + "'.")
                raise InvalidVolumeParameterError(f"Qtree '{qtree_name}' already exists")
        except NetAppRestError as err:
            if print_output:
                print("Error: Error checking for existing qtree.")
                print("API Error: ", err)
            raise APIConnectionError(err)

        # Create qtree
        if print_output:
            print("Creating qtree '" + qtree_name + "' in volume '" + volume_name + "' on SVM '" + svm_name + "'.")

        try:
            # Create NetApp Qtree resource
            qtree = NetAppQtree()
            qtree.svm = {"name": svm_name}
            qtree.volume = {"name": volume_name}
            qtree.name = qtree_name
            
            # Set security style if specified
            if security_style:
                qtree.security_style = security_style
            
            # Set UNIX permissions if specified
            if unix_permissions:
                qtree.unix_permissions = int(unix_permissions, 8)
                
            # Set export policy if specified
            if export_policy:
                qtree.export_policy = {"name": export_policy}

            # Create the qtree
            qtree.post(poll=True, poll_timeout=120)
            
            if print_output:
                print("Qtree '" + qtree_name + "' created successfully.")
                print("Qtree ID: " + str(qtree.id))

        except NetAppRestError as err:
            if print_output:
                print("Error: Error creating qtree.")
                print("API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise InvalidConfigError("Unsupported connection type")


def list_qtrees(volume_name: str = None, cluster_name: str = None, svm_name: str = None, 
                print_output: bool = False) -> list:
    """
    List qtrees in a volume or all qtrees in an SVM.

    Optional Arguments:
        volume_name (str): Name of the volume to list qtrees from. If not specified, lists qtrees from all volumes.
        cluster_name (str): Name of the hosting cluster (defaults to config cluster).
        svm_name (str): Name of the SVM (defaults to config SVM).
        print_output (bool): Print detailed output if True.

    Raises:
        InvalidConfigError: If configuration is missing or invalid.
        APIConnectionError: If there is an error connecting to the API.

    Returns:
        list: List of qtree information dictionaries.
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
            print("Error: Missing 'connectionType' in config file.")
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            if not svm_name:
                svm_name = config["svm"]
        except Exception as e:
            if print_output:
                print("Error: Missing required parameters (svm name) in config file.")
                print("Exception: ", e)
            raise InvalidConfigError()

        try:
            # Build query parameters
            query_params = {"svm.name": svm_name}
            if volume_name:
                query_params["volume.name"] = volume_name

            # Get qtrees collection
            qtrees = NetAppQtree.get_collection(fields="*", **query_params)
            qtrees_list = []

            # Process each qtree
            for qtree in qtrees:
                qtree_info = {
                    "id": qtree.id,
                    "name": qtree.name if qtree.name else "",
                    "volume": qtree.volume.name if hasattr(qtree.volume, 'name') else None,
                    "svm": qtree.svm.name if hasattr(qtree.svm, 'name') else None,
                    "security_style": qtree.security_style if hasattr(qtree, 'security_style') else None,
                    "unix_permissions": qtree.unix_permissions if hasattr(qtree, 'unix_permissions') else None,
                    "path": qtree.path if hasattr(qtree, 'path') else None,
                    "export_policy": qtree.export_policy.name if hasattr(qtree, 'export_policy') and qtree.export_policy else None,
                    "qos_policy": qtree.qos_policy.name if hasattr(qtree, 'qos_policy') and qtree.qos_policy else None
                }
                qtrees_list.append(qtree_info)

            # Print qtrees in tabular format if requested
            if print_output:
                if qtrees_list:
                    from tabulate import tabulate
                    headers = [
                        "ID", "Name", "Volume", "SVM", "Security Style", "UNIX Permissions", "Path", "Export Policy", "QoS Policy"
                    ]
                    table = []
                    for qtree in qtrees_list:
                        table.append([
                            qtree["id"],
                            qtree["name"] if qtree["name"] else "<root>",
                            qtree["volume"],
                            qtree["svm"],
                            qtree["security_style"],
                            qtree["unix_permissions"],
                            qtree["path"],
                            qtree["export_policy"],
                            qtree["qos_policy"]
                        ])
                    print(tabulate(table, headers=headers, tablefmt="simple"))
                else:
                    print("No qtrees found.")

            return qtrees_list

        except NetAppRestError as err:
            if print_output:
                print("Error: Error retrieving qtrees.")
                print("API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise InvalidConfigError("Unsupported connection type")


def get_qtree(volume_uuid: str, qtree_id: int, cluster_name: str = None, 
              print_output: bool = False) -> dict:
    """
    Retrieve properties for a specific qtree identified by volume UUID and qtree ID.

    Required Arguments:
        volume_uuid (str): UUID of the volume containing the qtree.
        qtree_id (int): ID of the qtree to retrieve.

    Optional Arguments:
        cluster_name (str): Name of the hosting cluster (defaults to config cluster).
        print_output (bool): Print detailed output if True.

    Raises:
        InvalidConfigError: If configuration is missing or invalid.
        InvalidVolumeParameterError: If the qtree does not exist.
        APIConnectionError: If there is an error connecting to the API.

    Returns:
        dict: Dictionary containing qtree information.
    """
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if print_output:
            print("Error: Missing 'connectionType' in config file.")
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            # Create qtree resource with volume UUID and qtree ID
            qtree = NetAppQtree(id=qtree_id, **{"volume.uuid": volume_uuid})
            
            # Get all properties of the qtree
            qtree.get(fields="*")
            
            # Build qtree information dictionary
            qtree_info = {
                "id": qtree.id,
                "name": qtree.name if qtree.name else "",
                "volume": {
                    "uuid": qtree.volume.uuid if hasattr(qtree.volume, 'uuid') else None,
                    "name": qtree.volume.name if hasattr(qtree.volume, 'name') else None
                },
                "svm": {
                    "uuid": qtree.svm.uuid if hasattr(qtree.svm, 'uuid') else None,
                    "name": qtree.svm.name if hasattr(qtree.svm, 'name') else None
                },
                "security_style": qtree.security_style if hasattr(qtree, 'security_style') else None,
                "unix_permissions": qtree.unix_permissions if hasattr(qtree, 'unix_permissions') else None,
                "path": qtree.path if hasattr(qtree, 'path') else None,
                "export_policy": {
                    "id": qtree.export_policy.id if hasattr(qtree, 'export_policy') and qtree.export_policy and hasattr(qtree.export_policy, 'id') else None,
                    "name": qtree.export_policy.name if hasattr(qtree, 'export_policy') and qtree.export_policy and hasattr(qtree.export_policy, 'name') else None
                },
                "qos_policy": {
                    "uuid": qtree.qos_policy.uuid if hasattr(qtree, 'qos_policy') and qtree.qos_policy and hasattr(qtree.qos_policy, 'uuid') else None,
                    "name": qtree.qos_policy.name if hasattr(qtree, 'qos_policy') and qtree.qos_policy and hasattr(qtree.qos_policy, 'name') else None
                },
                "user": {
                    "name": qtree.user.name if hasattr(qtree, 'user') and qtree.user and hasattr(qtree.user, 'name') else None
                },
                "group": {
                    "name": qtree.group.name if hasattr(qtree, 'group') and qtree.group and hasattr(qtree.group, 'name') else None
                }
            }

            # Print qtree details if requested
            if print_output:
                qtree_name = qtree_info["name"] if qtree_info["name"] else "<root>"
                print("Qtree Details:")
                print("  ID: " + str(qtree_info["id"]))
                print("  Name: " + qtree_name)
                print("  Volume: " + str(qtree_info["volume"]["name"]) + " (UUID: " + str(qtree_info["volume"]["uuid"]) + ")")
                print("  SVM: " + str(qtree_info["svm"]["name"]) + " (UUID: " + str(qtree_info["svm"]["uuid"]) + ")")
                print("  Security Style: " + str(qtree_info["security_style"]))
                print("  UNIX Permissions: " + str(qtree_info["unix_permissions"]))
                print("  Path: " + str(qtree_info["path"]))
                if qtree_info["export_policy"]["name"]:
                    print("  Export Policy: " + str(qtree_info["export_policy"]["name"]))
                if qtree_info["qos_policy"]["name"]:
                    print("  QoS Policy: " + str(qtree_info["qos_policy"]["name"]))
                if qtree_info["user"]["name"]:
                    print("  User: " + str(qtree_info["user"]["name"]))
                if qtree_info["group"]["name"]:
                    print("  Group: " + str(qtree_info["group"]["name"]))

            return qtree_info

        except NetAppRestError as err:
            if print_output:
                print("Error: Error retrieving qtree.")
                print("API Error: ", err)
            raise APIConnectionError(err)
        except Exception as e:
            if print_output:
                print("Error: Qtree with ID '" + str(qtree_id) + "' not found in volume '" + volume_uuid + "'.")
                print("Exception: ", e)
            raise InvalidVolumeParameterError(f"Qtree with ID '{qtree_id}' not found")

    else:
        raise InvalidConfigError("Unsupported connection type")
