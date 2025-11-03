"""NetApp DataOps Toolkit - Qtree Operations for Traditional Environments

This module provides qtree management operations for traditional environments.

This module imports shared utilities and exceptions from the main traditional module
to avoid code duplication and ensure consistency across the toolkit.
"""

import os
import requests
import json
import base64
from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Qtree as NetAppQtree
from netapp_ontap import HostConnection

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


def get_qtree_metrics(volume_uuid: str, qtree_id: int, cluster_name: str = None,
                      print_output: bool = False) -> dict:
    """
    Retrieve historical performance metrics for a qtree.
    
    Note: Requires analytics/activity tracking to be enabled on the parent volume
    through ONTAP System Manager or CLI. May require ONTAP 9.8+ for qtree metrics support.

    Required Arguments:
        volume_uuid (str): UUID of the volume containing the qtree.
        qtree_id (int): ID of the qtree to retrieve metrics for.

    Optional Arguments:
        cluster_name (str): Name of the hosting cluster (defaults to config cluster).
        print_output (bool): Print detailed output if True.

    Raises:
        InvalidConfigError: If configuration is missing or invalid.
        InvalidVolumeParameterError: If the qtree does not exist or metrics are not available.
        APIConnectionError: If there is an error connecting to the API.

    Returns:
        dict: Dictionary containing qtree performance metrics.
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
            # First verify that the qtree exists
            qtree = NetAppQtree(id=qtree_id, **{"volume.uuid": volume_uuid})
            qtree.get(fields="*")
            
            # Check if qtree exists
            if not qtree.id:
                if print_output:
                    print("Error: Qtree not found.")
                raise InvalidVolumeParameterError("Qtree not found")
            
            if print_output:
                print(f"Debug: Qtree found. Available fields: {[attr for attr in dir(qtree) if not attr.startswith('_')]}")
                
                # Check if ext_performance_monitoring exists and is enabled
                try:
                    # Try to access ext_performance_monitoring as attribute
                    if hasattr(qtree, 'ext_performance_monitoring'):
                        ext_perf_mon = getattr(qtree, 'ext_performance_monitoring')
                        print(f"Debug: ext_performance_monitoring object: {ext_perf_mon}")
                        print(f"Debug: ext_performance_monitoring type: {type(ext_perf_mon)}")
                        if hasattr(ext_perf_mon, 'enabled'):
                            print(f"Debug: ext_performance_monitoring.enabled: {ext_perf_mon.enabled}")
                        else:
                            print("Debug: ext_performance_monitoring.enabled attribute not found")
                    else:
                        print("Debug: ext_performance_monitoring attribute not found")
                        
                    # Try to get it with specific field request
                    qtree_check = NetAppQtree(id=qtree_id, **{"volume.uuid": volume_uuid})
                    qtree_check.get(fields="ext_performance_monitoring")
                    if hasattr(qtree_check, 'ext_performance_monitoring'):
                        ext_perf_mon_check = qtree_check.ext_performance_monitoring
                        print(f"Debug: ext_performance_monitoring via field request: {ext_perf_mon_check}")
                        if hasattr(ext_perf_mon_check, 'enabled'):
                            print(f"Debug: ext_performance_monitoring.enabled via field request: {ext_perf_mon_check.enabled}")
                    
                except Exception as e:
                    print(f"Debug: Error checking ext_performance_monitoring: {e}")
                
            # Note: Qtree metrics may be available even without explicit extended monitoring field
            # The metrics endpoint will return appropriate error if metrics are not available

            # Use the config to construct the API request
            hostname = config["hostname"]
            username = config["username"]
            password = config["password"]
            verify_ssl = config.get("verifySslCert", False)
            
            # Decode base64 password if it's encoded
            try:
                # Try to decode the password as base64
                decoded_password = base64.b64decode(password).decode('utf-8')
                if print_output:
                    print(f"Debug: Password was base64 encoded, decoded successfully")
                password = decoded_password
            except Exception as e:
                # If decoding fails, assume password is already in plain text
                if print_output:
                    print(f"Debug: Password appears to be plain text (base64 decode failed): {e}")
            
            # Construct the metrics URL
            metrics_url = f"https://{hostname}/api/storage/qtrees/{volume_uuid}/{qtree_id}/metrics"
            
            if print_output:
                print(f"Debug: Making request to: {metrics_url}")
                print(f"Debug: Using username: {username}")
            
            # Make the API request
            response = requests.get(
                metrics_url,
                auth=(username, password),
                verify=verify_ssl,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 404:
                if print_output:
                    print("Error: Qtree metrics endpoint not found. This may indicate:")
                    print("  1. The qtree does not exist")
                    print("  2. Performance metrics are not enabled for this qtree")
                    print("  3. The ONTAP version may not support qtree metrics")
                raise InvalidVolumeParameterError("Qtree metrics not available")
            elif response.status_code == 401:
                if print_output:
                    print("Error: Unauthorized access to qtree metrics. This may indicate:")
                    print("  1. The user account lacks sufficient privileges for performance monitoring")
                    print("  2. Additional roles may be required (e.g., 'readonly' + performance monitoring privileges)")
                    print("  3. The user may need 'admin' or 'performance-admin' role")
                    print("  4. Qtree-level metrics may require special permissions beyond volume metrics")
                    print(f"Response: {response.text}")
                raise InvalidVolumeParameterError("Insufficient permissions for qtree metrics")
            elif response.status_code == 400:
                if print_output:
                    print("Error: Bad request. This may indicate:")
                    print("  1. Analytics/activity tracking is not enabled on the parent volume")
                    print("  2. Invalid qtree ID or volume UUID")
                    print("  3. Qtree metrics may not be supported in this ONTAP version")
                    print(f"Response: {response.text}")
                raise InvalidVolumeParameterError("Cannot retrieve qtree metrics - check analytics settings")
            elif response.status_code != 200:
                if print_output:
                    print(f"Error: Failed to retrieve metrics. Status code: {response.status_code}")
                    print(f"Response: {response.text}")
                raise APIConnectionError(f"Failed to retrieve metrics: {response.status_code}")
            
            metrics_data = response.json()
            
            # Check if we actually got metrics data
            if not metrics_data or ('records' in metrics_data and len(metrics_data['records']) == 0):
                if print_output:
                    print("Warning: No metrics data available for this qtree.")
                    print("This may indicate that:")
                    print("  1. Analytics/activity tracking needs to be enabled on the parent volume")
                    print("  2. Insufficient time has passed to collect metrics")
                    print("  3. No I/O activity has occurred on this qtree")
                return {"records": [], "message": "No metrics data available"}
            
            # Print metrics if requested
            if print_output:
                print("Qtree Performance Metrics:")
                print(f"  Volume UUID: {volume_uuid}")
                print(f"  Qtree ID: {qtree_id}")
                
                if 'records' in metrics_data:
                    print(f"  Number of data points: {len(metrics_data['records'])}")
                    
                    for i, record in enumerate(metrics_data['records'][:5]):  # Show first 5 records
                        print(f"  Data point {i+1}:")
                        if 'timestamp' in record:
                            print(f"    Timestamp: {record['timestamp']}")
                        if 'duration' in record:
                            print(f"    Duration: {record['duration']}")
                        
                        # Print IOPS metrics
                        if 'iops' in record:
                            iops = record['iops']
                            if 'read' in iops:
                                print(f"    Read IOPS: {iops['read']}")
                            if 'write' in iops:
                                print(f"    Write IOPS: {iops['write']}")
                            if 'total' in iops:
                                print(f"    Total IOPS: {iops['total']}")
                        
                        # Print latency metrics
                        if 'latency' in record:
                            latency = record['latency']
                            if 'read' in latency:
                                print(f"    Read Latency (μs): {latency['read']}")
                            if 'write' in latency:
                                print(f"    Write Latency (μs): {latency['write']}")
                            if 'total' in latency:
                                print(f"    Total Latency (μs): {latency['total']}")
                        
                        # Print throughput metrics
                        if 'throughput' in record:
                            throughput = record['throughput']
                            if 'read' in throughput:
                                print(f"    Read Throughput (bytes/s): {throughput['read']}")
                            if 'write' in throughput:
                                print(f"    Write Throughput (bytes/s): {throughput['write']}")
                            if 'total' in throughput:
                                print(f"    Total Throughput (bytes/s): {throughput['total']}")
                        
                        print()  # Empty line between records
                    
                    if len(metrics_data['records']) > 5:
                        print(f"  ... and {len(metrics_data['records']) - 5} more data points")
                else:
                    print("  No metrics data available")

            return metrics_data

        except NetAppRestError as err:
            if print_output:
                print("Error: Error retrieving qtree metrics.")
                print("API Error: ", err)
            raise APIConnectionError(err)
        except Exception as e:
            if print_output:
                print("Error: Failed to retrieve qtree metrics.")
                print("Exception: ", e)
            raise InvalidVolumeParameterError(f"Failed to retrieve metrics for qtree '{qtree_id}'")

    else:
        raise InvalidConfigError("Unsupported connection type")
