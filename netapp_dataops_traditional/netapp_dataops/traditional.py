"""NetApp DataOps Toolkit for Traditional Environments import module.

This module provides the public functions available to be imported directly
by applications using the import method of utilizing the toolkit.
"""

import base64
import functools
import json
import os
import re
import subprocess
import sys
import time
import warnings
import datetime
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.client import Config as BotoConfig
from netapp_ontap import config as netappConfig
from netapp_ontap.error import NetAppRestError
from netapp_ontap.host_connection import HostConnection as NetAppHostConnection
from netapp_ontap.resources import Flexcache as NetAppFlexCache
from netapp_ontap.resources import SnapmirrorRelationship as NetAppSnapmirrorRelationship
from netapp_ontap.resources import SnapmirrorTransfer as NetAppSnapmirrorTransfer
from netapp_ontap.resources import Snapshot as NetAppSnapshot
from netapp_ontap.resources import Volume as NetAppVolume
from netapp_ontap.resources import ExportPolicy as NetAppExportPolicy
from netapp_ontap.resources import SnapshotPolicy as NetAppSnapshotPolicy
from netapp_ontap.resources import CLI as NetAppCLI
import pandas as pd
import requests
from tabulate import tabulate
import yaml


__version__ = "2.1.0"


# Using this decorator in lieu of using a dependency to manage deprecation
def deprecated(func):
    @functools.wraps(func)
    def warned_func(*args, **kwargs):
        warnings.warn("Function {} is deprecated.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        return func(*args, **kwargs)
    return warned_func


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


def _print_api_response(response: requests.Response):
    print("API Response:")
    print("Status Code: ", response.status_code)
    print("Header: ", response.headers)
    if response.text:
        print("Body: ", response.text)


def _download_from_s3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool,
                   s3CACertBundle: str, s3Bucket: str, s3ObjectKey: str, localFile: str, print_output: bool = False):
    # Instantiate S3 session
    try:
        s3 = _instantiate_s3_session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId,
                                  s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert,
                                  s3CACertBundle=s3CACertBundle, print_output=print_output)
    except Exception as err:
        if print_output:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)

    if print_output:
        print(
            "Downloading object '" + s3ObjectKey + "' from bucket '" + s3Bucket + "' and saving as '" + localFile + "'.")

    # Create directories that don't exist
    if localFile.find(os.sep) != -1:
        dirs = localFile.split(os.sep)
        dirpath = os.sep.join(dirs[:len(dirs) - 1])
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

    # Download the file
    try:
        s3.Object(s3Bucket, s3ObjectKey).download_file(localFile)
    except Exception as err:
        if print_output:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)


def _get_cloud_central_access_token(refreshToken: str, print_output: bool = False) -> str:
    # Define parameters for API call
    url = "https://netapp-cloud-account.auth0.com/oauth/token"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refreshToken,
        "client_id": "Mu0V1ywgYteI6w1MbD15fKfVIUrNXGWC"
    }

    # Call API to optain access token
    response = requests.post(url=url, headers=headers, data=json.dumps(data))

    # Parse response to retrieve access token
    try:
        responseBody = json.loads(response.text)
        accessToken = responseBody["access_token"]
    except:
        errorMessage = "Error obtaining access token from Cloud Sync API"
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    return accessToken


def _get_cloud_sync_access_parameters(refreshToken: str, print_output: bool = False) -> (str, str):
    try:
        accessToken = _get_cloud_central_access_token(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/accounts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + accessToken
    }

    # Call API to obtain account ID
    response = requests.get(url=url, headers=headers)

    # Parse response to retrieve account ID
    try:
        responseBody = json.loads(response.text)
        accountId = responseBody[0]["accountId"]
    except:
        errorMessage = "Error obtaining account ID from Cloud Sync API"
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    # Return access token and account ID
    return accessToken, accountId


def _instantiate_connection(config: dict, connectionType: str = "ONTAP", print_output: bool = False):
    if connectionType == "ONTAP":
        ## Connection details for ONTAP cluster
        try:
            ontapClusterMgmtHostname = config["hostname"]
            ontapClusterAdminUsername = config["username"]
            ontapClusterAdminPasswordBase64 = config["password"]
            verifySSLCert = config["verifySSLCert"]
        except:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        # Decode base64-encoded password
        ontapClusterAdminPasswordBase64Bytes = ontapClusterAdminPasswordBase64.encode("ascii")
        ontapClusterAdminPasswordBytes = base64.b64decode(ontapClusterAdminPasswordBase64Bytes)
        ontapClusterAdminPassword = ontapClusterAdminPasswordBytes.decode("ascii")

        # Instantiate connection to ONTAP cluster
        netappConfig.CONNECTION = NetAppHostConnection(
            host=ontapClusterMgmtHostname,
            username=ontapClusterAdminUsername,
            password=ontapClusterAdminPassword,
            verify=verifySSLCert
        )

    else:
        raise ConnectionTypeError()


def _instantiate_s3_session(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str, print_output: bool = False):
    # Instantiate session
    session = boto3.session.Session(aws_access_key_id=s3AccessKeyId, aws_secret_access_key=s3SecretAccessKey)
    config = BotoConfig(signature_version='s3v4')

    if s3VerifySSLCert:
        if s3CACertBundle:
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=s3CACertBundle, config=config)
        else:
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, config=config)
    else:
        s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=False, config=config)

    return s3


def _print_invalid_config_error() :
    print("Error: Missing or invalid config file. Run `netapp_dataops_cli.py config` to create config file.")


def _retrieve_config(configDirPath: str = "~/.netapp_dataops", configFilename: str = "config.json",
                   print_output: bool = False) -> dict:
    configDirPath = os.path.expanduser(configDirPath)
    configFilePath = os.path.join(configDirPath, configFilename)
    try:
        with open(configFilePath, 'r') as configFile:
            # Read connection details from config file; read into dict
            config = json.load(configFile)
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()
    return config


def _retrieve_cloud_central_refresh_token(print_output: bool = False) -> str:
    # Retrieve refresh token from config file
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        refreshTokenBase64 = config["cloudCentralRefreshToken"]
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Decode base64-encoded refresh token
    refreshTokenBase64Bytes = refreshTokenBase64.encode("ascii")
    refreshTokenBytes = base64.b64decode(refreshTokenBase64Bytes)
    refreshToken = refreshTokenBytes.decode("ascii")

    return refreshToken


def _retrieve_s3_access_details(print_output: bool = False) -> (str, str, str, bool, str):
    # Retrieve refresh token from config file
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        s3Endpoint = config["s3Endpoint"]
        s3AccessKeyId = config["s3AccessKeyId"]
        s3SecretAccessKeyBase64 = config["s3SecretAccessKey"]
        s3VerifySSLCert = config["s3VerifySSLCert"]
        s3CACertBundle = config["s3CACertBundle"]
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Decode base64-encoded refresh token
    s3SecretAccessKeyBase64Bytes = s3SecretAccessKeyBase64.encode("ascii")
    s3SecretAccessKeyBytes = base64.b64decode(s3SecretAccessKeyBase64Bytes)
    s3SecretAccessKey = s3SecretAccessKeyBytes.decode("ascii")

    return s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle


def _upload_to_s3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str,
               s3Bucket: str, localFile: str, s3ObjectKey: str, s3ExtraArgs: str = None, print_output: bool = False):
    # Instantiate S3 session
    try:
        s3 = _instantiate_s3_session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId,
                                  s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert,
                                  s3CACertBundle=s3CACertBundle, print_output=print_output)
    except Exception as err:
        if print_output:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)

    # Upload file
    if print_output:
        print("Uploading file '" + localFile + "' to bucket '" + s3Bucket + "' and applying key '" + s3ObjectKey + "'.")

    try:
        if s3ExtraArgs:
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile, ExtraArgs=json.loads(s3ExtraArgs))
        else:
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile)
    except Exception as err:
        if print_output:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)


def _convert_bytes_to_pretty_size(size_in_bytes: str, num_decimal_points: int = 2) -> str :
    # Convert size in bytes to "pretty" size (size in KB, MB, GB, or TB)
    prettySize = float(size_in_bytes) / 1024
    if prettySize >= 1024:
        prettySize = float(prettySize) / 1024
        if prettySize >= 1024:
            prettySize = float(prettySize) / 1024
            if prettySize >= 1024:
                prettySize = float(prettySize) / 1024
                prettySize = round(prettySize, 2)
                prettySize = str(prettySize) + "TB"
            else:
                prettySize = round(prettySize, 2)
                prettySize = str(prettySize) + "GB"
        else:
            prettySize = round(prettySize, 2)
            prettySize = str(prettySize) + "MB"
    else:
        prettySize = round(prettySize, 2)
        prettySize = str(prettySize) + "KB"

    return prettySize


#
# Public importable functions specific to the traditional package
#


def clone_volume(new_volume_name: str, source_volume_name: str, cluster_name: str = None, source_snapshot_name: str = None,
                 source_svm: str = None, target_svm: str = None, export_hosts: str = None, export_policy: str = None, split: bool = False, 
                 unix_uid: str = None, unix_gid: str = None, mountpoint: str = None, junction: str= None, readonly: bool = False,
                 snapshot_policy: str = None, refresh: bool = False, svm_dr_unprotect: bool = False, print_output: bool = False):
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

        # Retrieve values from config file if not passed into function
        try:            
            sourcesvm = config["svm"]
            if source_svm: 
                sourcesvm = source_svm 
            
            targetsvm = sourcesvm
            if target_svm:
                targetsvm = target_svm 

            if not unix_uid:
                unix_uid = config["defaultUnixUID"]
            if not unix_gid:
                unix_gid = config["defaultUnixGID"]

        except Exception as e:
            if print_output:
                print(e)
                _print_invalid_config_error()
            raise InvalidConfigError()

        # Check unix uid for validity
        try:
            unix_uid = int(unix_uid)
        except:
            if print_output:
                print("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        # Check unix gid for validity
        try:
            unix_gid = int(unix_gid)
        except:
            if print_output:
                print("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        #check if clone volume already exists 
        try:
            currentVolume = NetAppVolume.find(name=new_volume_name, svm=targetsvm)        
            if currentVolume and not refresh:
                if print_output:
                    print("Error: clone:"+new_volume_name+" already exists.")
                raise InvalidVolumeParameterError("name") 
            
            #for refresh we want to keep the existing policy
            if currentVolume and refresh and not export_policy and not export_hosts:
                export_policy = currentVolume.nas.export_policy.name

            # if refresh and not provided new snapshot_policy
            if currentVolume and refresh and not snapshot_policy:                
                snapshot_policy = currentVolume.snapshot_policy.name

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)
        
        #delete existing clone when refresh
        try:
            if currentVolume and refresh:
                if "CLONENAME:" in currentVolume.comment:
                    delete_volume(volume_name=new_volume_name, cluster_name=cluster_name, svm_name=target_svm, delete_mirror=True, print_output=True)
                else:
                    if print_output:
                        print("Error: refresh clone is only supported when existing clone created using the tool (based on volume comment)")
                    raise InvalidVolumeParameterError("name")                
        except:
            print("Error: could not delete previous clone")
            raise InvalidVolumeParameterError("name")       
        
        try:
            if not snapshot_policy :                
                snapshot_policy = config["defaultSnapshotPolicy"]
        except:
            print("Error: default snapshot policy could not be found in config file")
            raise InvalidVolumeParameterError("name")   

        # check export policies 
        try:
            if not export_policy and not export_hosts:
                export_policy = config["defaultExportPolicy"]
            elif export_policy:
                currentExportPolicy = NetAppExportPolicy.find(name=export_policy, svm=targetsvm)
                if not currentExportPolicy:
                    if print_output:
                        print("Error: export policy:"+export_policy+" dones not exists.")
                    raise InvalidVolumeParameterError("name")
            elif export_hosts:
                export_policy = "netapp_dataops_"+new_volume_name
                currentExportPolicy = NetAppExportPolicy.find(name=export_policy, svm=targetsvm)
                if currentExportPolicy:
                    currentExportPolicy.delete()
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        #exists check if snapshot-policy 
        try:
            snapshotPoliciesDetails  = NetAppSnapshotPolicy.get_collection(**{"name":snapshot_policy})   
            clusterSnapshotPolicy = False
            svmSnapshotPolicy = False  
            for snapshotPolicyDetails in snapshotPoliciesDetails:
                if str(snapshotPolicyDetails.name) == snapshot_policy:
                    try:
                        if str(snapshotPolicyDetails.svm.name) == targetsvm:
                            svmSnapshotPolicy = True
                    except:
                        clusterSnapshotPolicy = True

            if not clusterSnapshotPolicy and not svmSnapshotPolicy:
                if print_output:
                    print("Error: snapshot-policy:"+snapshot_policy+" could not be found")
                raise InvalidVolumeParameterError("snapshot_policy")                
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)            

        # Create volume
        if print_output:
            print("Creating clone volume '" + targetsvm+':'+new_volume_name + "' from source volume '" + sourcesvm+':'+source_volume_name + "'.")

        try:
            # Retrieve source volume
            sourceVolume = NetAppVolume.find(name=source_volume_name, svm=sourcesvm)
            if not sourceVolume:
                if print_output:
                    print("Error: Invalid source volume name.")
                raise InvalidVolumeParameterError("name")

            # Create option to choose junction path.
            if junction:
                junction=junction
            else:
                junction = "/"+new_volume_name
           

            # Construct dict representing new volume
            newVolumeDict = {
                "name": new_volume_name,
                "svm": {"name": targetsvm},
                "nas": {
                    "path": junction
                },
                "clone": {
                    "is_flexclone": True,
                    "parent_svm": {
                        #"name": sourceVolume.svm.name,
                        "name": sourcesvm,
                        #"uuid": sourceVolume.svm.uuid
                    },
                    "parent_volume": {
                        "name": sourceVolume.name,
                        "uuid": sourceVolume.uuid
                    }
                }
            }
            
            if unix_uid != 0:
                newVolumeDict["nas"]["uid"] = unix_uid
            else:
                if print_output:
                    print("Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.")
            if unix_gid != 0:
                newVolumeDict["nas"]["gid"] = unix_gid
            else:
                if print_output:
                    print("Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.")

            # Add source snapshot details to volume dict if specified
            if source_snapshot_name and not source_snapshot_name.endswith("*"):
                # Retrieve source snapshot
                sourceSnapshot = NetAppSnapshot.find(sourceVolume.uuid, name=source_snapshot_name)
                if not sourceSnapshot:
                    if print_output:
                        print("Error: Invalid source snapshot name.")
                    raise InvalidSnapshotParameterError("name")
              

                # Append source snapshot details to volume dict
                newVolumeDict["clone"]["parent_snapshot"] = {
                    "name": sourceSnapshot.name,
                    "uuid": sourceSnapshot.uuid
                }
            
            if source_snapshot_name and source_snapshot_name.endswith("*"):
                source_snapshot_prefix = source_snapshot_name[:-1]
                latest_source_snapshot = None 
                latest_source_snapshot_uuid = None 

                # Retrieve all source snapshot from last to 1st 
                for snapshot in NetAppSnapshot.get_collection(sourceVolume.uuid):
                    snapshot.get()
                    if snapshot.name.startswith(source_snapshot_prefix):
                        latest_source_snapshot = snapshot.name
                        latest_source_snapshot_uuid = snapshot.uuid

                if not latest_source_snapshot:
                    if print_output:
                        print("Error: Could not find snapshot prefixed by '"+source_snapshot_prefix+"'.")
                    raise InvalidSnapshotParameterError("name")
                # Append source snapshot details to volume dict
                newVolumeDict["clone"]["parent_snapshot"] = {
                    "name": latest_source_snapshot,
                    "uuid": latest_source_snapshot_uuid
                }
                print("Snapshot '" + latest_source_snapshot+ "' will be used to create the clone.")   

            # set clone volume commnet parameter 
            comment = 'PARENTSVM:'+sourcesvm+',PARENTVOL:'+newVolumeDict["clone"]["parent_volume"]["name"]+',CLONESVM:'+targetsvm+',CLONENAME:'+newVolumeDict["name"]
            if source_snapshot_name: comment += ' SNAP:'+newVolumeDict["clone"]["parent_snapshot"]["name"] 
            comment += " netapp-dataops"
            
            newVolumeDict["comment"] = comment

            # Create new volume clone 
            newVolume = NetAppVolume.from_dict(newVolumeDict)
            newVolume.post(poll=True, poll_timeout=120)
            if print_output:
                print("Clone volume created successfully.")

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        if svm_dr_unprotect:
            try:
                if print_output:
                    print("Disabling svm-dr protection")                 
                response = NetAppCLI().execute("volume modify",vserver=targetsvm,volume=new_volume_name,body={"vserver_dr_protection": "unprotected"})
            except NetAppRestError as err:
                if "volume is not part of a Vserver DR configuration" in str(err):
                    if print_output:
                        print("Warning: could not disable svm-dr-protection since volume is not protected using svm-dr")                    
                else:
                    if print_output:
                        print("Error: ONTAP Rest API Error: ", err)                    
                    raise APIConnectionError(err)                

        #create custom export policy if needed 
        if export_hosts:
            try:            
                if print_output:
                    print("Creating export-policy:"+export_policy)                  
                # Construct dict representing new export policy    
                newExportPolicyDict = {
                    "name" : export_policy,
                    "svm": {"name": targetsvm},
                    "rules": []
                }
                for client in export_hosts.split(":"):
                    newExportPolicyDict['rules'].append({ "clients": [{"match": client }], "ro_rule": ["sys"], "rw_rule": ["sys"], "superuser": ["sys"]})

                # Create new export policy                
                newExportPolicy = NetAppExportPolicy.from_dict(newExportPolicyDict)
                newExportPolicy.post(poll=True, poll_timeout=120)
              
            except NetAppRestError as err:
                if print_output:
                    print("Error: ONTAP Rest API Error: ", err)
                raise APIConnectionError(err)

        #set export policy and snapshot policy 
        try:
            if print_output:
                print("Setting export-policy:"+export_policy+ " snapshot-policy:"+snapshot_policy) 
            volumeDetails = NetAppVolume.find(name=new_volume_name, svm=targetsvm)   
            updatedVolumeDetails = NetAppVolume(uuid=volumeDetails.uuid)
            updatedVolumeDetails.nas = {"export_policy": {"name": export_policy}}
            updatedVolumeDetails.snapshot_policy = {"name": snapshot_policy}
            updatedVolumeDetails.patch(poll=True, poll_timeout=120) 
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)              

        #split clone 
        try:
            if split: 
                if print_output:
                    print("Splitting clone") 
                volumeDetails = NetAppVolume.find(name=new_volume_name, svm=targetsvm)                    
                #get volume details 
                updatedVolumeDetails = NetAppVolume(uuid=volumeDetails.uuid)        
                updatedVolumeDetails.clone = {"split_initiated": True}
                updatedVolumeDetails.patch()   

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)            

        # Optionally mount newly created volume
        if mountpoint:
            try:
                mount_volume(volume_name=new_volume_name, svm_name=targetsvm, mountpoint=mountpoint, readonly=readonly, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                if print_output:
                    print("Error: Error mounting clone volume.")
                raise

    else:
        raise ConnectionTypeError()


def create_snapshot(volume_name: str, cluster_name: str = None, svm_name: str = None, snapshot_name: str = None, retention_count: int = 0, retention_days: bool = False, snapmirror_label: str = None, print_output: bool = False):
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

        if not snapshot_name:
            snapshot_name = "netapp_dataops"

        # Retrieve svm from config file
        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name 
        except:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        snapshot_name_original = snapshot_name
        # Set snapshot name if not passed into function or retention provided 
        if not snapshot_name or int(retention_count) > 0:
            timestamp = '.'+datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S")
            snapshot_name += timestamp

        if print_output:
            print("Creating snapshot '" + snapshot_name + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # create snapshot dict 
            snapshotDict = {
                'name': snapshot_name,
                'volume': volume.to_dict()
            }
            if snapmirror_label:
                if print_output:
                    print("Setting snapmirror label as:"+snapmirror_label)                
                snapshotDict['snapmirror_label'] = snapmirror_label

            # Create snapshot
            snapshot = NetAppSnapshot.from_dict(snapshotDict)
            snapshot.post(poll=True)

            if print_output:
                print("Snapshot created successfully.")

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        #delete snapshots exceeding retention count if provided
        retention_count = int(retention_count)  
        if retention_count > 0:
            try:  
                # Retrieve all source snapshot from last to 1st 
                # Retrieve volume
                volume = NetAppVolume.find(name=volume_name, svm=svm)
                if not volume:
                    if print_output:
                        print("Error: Invalid volume name.")
                    raise InvalidVolumeParameterError("name")    

                if retention_days:
                    retention_date = datetime.datetime.today() - datetime.timedelta(days=retention_count)
                
                last_snapshot_list = []          
                snapshot_list = []
                for snapshot in NetAppSnapshot.get_collection(volume.uuid):
                    snapshot.get()
                    if snapshot.name.startswith(snapshot_name_original+'.'):
                        if not retention_days:
                            snapshot_list.append(snapshot.name)   
                            last_snapshot_list.append(snapshot.name)
                            if len(last_snapshot_list) > retention_count:
                                last_snapshot_list.pop(0)
                        else:
                            rx = r'^{0}\.(.+)$'.format(snapshot_name_original)
                            matchObj = re.match(rx,snapshot.name)
                            if matchObj:
                                snapshot_date = matchObj.group(1)
                                snapshot_date_obj = datetime.datetime.strptime(snapshot_date, "%Y-%m-%d_%H%M%S")
                                snapshot_list.append(snapshot.name)   
                                last_snapshot_list.append(snapshot.name)
                                if snapshot_date_obj < retention_date:
                                    last_snapshot_list.pop(0)
                
                #delete snapshots not in retention 
                for snap in snapshot_list:
                    if snap not in last_snapshot_list:
                        delete_snapshot(volume_name=volume_name, svm_name = svm, snapshot_name=snap, print_output=True)

            except NetAppRestError as err:
                if print_output:
                    print("Error: ONTAP Rest API Error: ", err)
                raise APIConnectionError(err)                                   
    else:
        raise ConnectionTypeError()


def create_volume(volume_name: str, volume_size: str, guarantee_space: bool = False, cluster_name: str = None, svm_name: str = None,
                  volume_type: str = "flexvol", unix_permissions: str = "0777",
                  unix_uid: str = "0", unix_gid: str = "0", export_policy: str = "default",
                  snapshot_policy: str = None, aggregate: str = None, mountpoint: str = None, junction: str = None, readonly: bool = False,
                  print_output: bool = False, tiering_policy=None):
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

        # Retrieve values from config file if not passed into function
        try:
            svm = config["svm"]
            if svm_name: 
                svm = svm_name 
            if not volume_type :
                volume_type = config["defaultVolumeType"]
            if not unix_permissions :
                unix_permissions = config["defaultUnixPermissions"]
            if not unix_uid :
                unix_uid = config["defaultUnixUID"]
            if not unix_gid :
                unix_gid = config["defaultUnixGID"]
            if not export_policy :
                export_policy = config["defaultExportPolicy"]
            if not snapshot_policy :
                snapshot_policy = config["defaultSnapshotPolicy"]
            if not aggregate and volume_type == 'flexvol' :
                aggregate = config["defaultAggregate"]
        except:
            if print_output :
                _print_invalid_config_error()
            raise InvalidConfigError()

        # Check volume type for validity
        if volume_type not in ("flexvol", "flexgroup"):
            if print_output:
                print("Error: Invalid volume type specified. Acceptable values are 'flexvol' and 'flexgroup'.")
            raise InvalidVolumeParameterError("size")

        # Check unix permissions for validity
        if not re.search("^0[0-7]{3}", unix_permissions):
            if print_output:
                print("Error: Invalid unix permissions specified. Acceptable values are '0777', '0755', '0744', etc.")
            raise InvalidVolumeParameterError("unixPermissions")

        # Check unix uid for validity
        try:
            unix_uid = int(unix_uid)
        except:
            if print_output :
                print("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        # Check unix gid for validity
        try:
            unix_gid = int(unix_gid)
        except:
            if print_output:
                print("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        # Convert volume size to Bytes
        if re.search("^[0-9]+MB$", volume_size):
            # Convert from MB to Bytes
            volumeSizeBytes = int(volume_size[:len(volume_size)-2]) * 1024**2
        elif re.search("^[0-9]+GB$", volume_size):
            # Convert from GB to Bytes
            volumeSizeBytes = int(volume_size[:len(volume_size)-2]) * 1024**3
        elif re.search("^[0-9]+TB$", volume_size):
            # Convert from TB to Bytes
            volumeSizeBytes = int(volume_size[:len(volume_size)-2]) * 1024**4
        else :
            if print_output:
                print("Error: Invalid volume size specified. Acceptable values are '1024MB', '100GB', '10TB', etc.")
            raise InvalidVolumeParameterError("size")

        # Create option to choose junction path.
        if junction:
            junction=junction
        else:
            junction = "/"+volume_name


        #check tiering policy        
        if not tiering_policy in ['none','auto','snapshot-only','all', None]:
            if print_output:
                print("Error: tiering policy can be: none,auto,snapshot-only or all")
            raise InvalidVolumeParameterError("tieringPolicy")        

        # Create dict representing volume
        volumeDict = {
            "name": volume_name,
            "comment": "netapp-dataops",
            "svm": {"name": svm},
            "size": volumeSizeBytes,
            "style": volume_type,
            "nas": {
                "path": junction,
                "export_policy": {"name": export_policy},
                "security_style": "unix",
                "unix_permissions": unix_permissions,
                "uid": unix_uid,
                "gid": unix_gid
            },
            "snapshot_policy": {"name": snapshot_policy},          
        }

        # Set space guarantee field
        if guarantee_space:
            volumeDict["guarantee"] = {"type": "volume"}
        else:
            volumeDict["guarantee"] = {"type": "none"}

        # If flexvol -> set aggregate field
        if volume_type == "flexvol":
            volumeDict["aggregates"] = [{'name': aggregate}]
        else:
            if aggregate:
                volumeDict["aggregates"] = []
                for aggr in aggregate.split(','):
                    volumeDict["aggregates"].append({'name': aggr}) 
        #if tiering policy provided 
        if tiering_policy:
            volumeDict['tiering'] = {'policy': tiering_policy}

        # Create volume
        if print_output:
            print("Creating volume '" + volume_name + "' on svm '" + svm + "'")
        try:
            volume = NetAppVolume.from_dict(volumeDict)
            volume.post(poll=True)
            if print_output:
                print("Volume created successfully.")
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Optionally mount newly created volume
        if mountpoint:
            try:
                mount_volume(volume_name=volume_name, svm_name=svm, mountpoint=mountpoint, readonly=readonly, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                if print_output:
                    print("Error: Error mounting volume.")
                raise

    else:
        raise ConnectionTypeError()


def delete_snapshot(volume_name: str, snapshot_name: str, cluster_name: str = None, svm_name: str = None, print_output: bool = False):
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

        # Retrieve svm from config file
        try:
            svm = config["svm"]
            if svm_name: 
                svm = svm_name 
        except:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        if print_output:
            print("Deleting snapshot '" + snapshot_name + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Retrieve snapshot
            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshot_name)
            if not snapshot:
                if print_output:
                    print("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            # Delete snapshot
            snapshot.delete(poll=True)

            if print_output:
                print("Snapshot deleted successfully.")

        except NetAppRestError as err :
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def delete_volume(volume_name: str, cluster_name: str = None, svm_name: str = None, delete_mirror: bool = False, 
                delete_non_clone: bool = False, print_output: bool = False):
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

        # Retrieve svm from config file
        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
        except:
            if print_output :
                _print_invalid_config_error()
            raise InvalidConfigError()

        if print_output:
            print("Deleting volume '" + svm+':'+volume_name + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            if not "CLONENAME:" in volume.comment and not delete_non_clone:
                if print_output:
                    print("Error: volume is not a clone created by this tool. add --delete-non-clone to delete it")
                raise InvalidVolumeParameterError("delete-non-clone")                
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)


        if delete_mirror:
            #check if this volume has snapmirror destination relationship
            uuid = None
            try:
                snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": svm+":"+volume_name})
                for rel in snapmirror_relationship:
                    # Retrieve relationship details
                    rel.get()
                    uuid = rel.uuid
            except NetAppRestError as err:
                if print_output:
                    print("Error: ONTAP Rest API Error: ", err)                

            if uuid: 
                if print_output:
                    print("Deleting snapmirror relationship: "+svm+":"+volume_name)                
                try:
                    deleteRelation = NetAppSnapmirrorRelationship(uuid=uuid)
                    deleteRelation.delete(poll=True, poll_timeout=120)
                except NetAppRestError as err:
                    if print_output:
                        print("Error: ONTAP Rest API Error: ", err)                  

            #check if this volume has snapmirror destination relationship
            uuid = None
            try:
                snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(list_destinations_only=True,**{"source.path": svm+":"+volume_name})
                for rel in snapmirror_relationship:
                    # Retrieve relationship details
                    rel.get(list_destinations_only=True)
                    uuid = rel.uuid
                    if print_output:
                        print("release relationship: "+rel.source.path+" -> "+rel.destination.path)   
                    deleteRelation = NetAppSnapmirrorRelationship(uuid=uuid)
                    deleteRelation.delete(poll=True, poll_timeout=120,source_only=True)
            except NetAppRestError as err:
                if print_output:
                    print("Error: ONTAP Rest API Error: ", err)                         

        try:
            # Delete volume
            volume.delete(poll=True)

            if print_output:
                print("Volume deleted successfully.")

        except NetAppRestError as err:
            if print_output:
                if "You must delete the SnapMirror relationships before" in str(err):
                    print("Error: volume is snapmirror destination. add --delete-mirror to delete snapmirror relationship before deleting the volume")                
                elif "the source endpoint of one or more SnapMirror relationships" in str(err):
                    print("Error: volume is snapmirror source. add --delete-mirror to release snapmirror relationship before deleting the volume")                
                else:
                    print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def list_cloud_sync_relationships(print_output: bool = False) -> list():
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API

    # Retrieve refresh token
    try:
        refreshToken = _retrieve_cloud_central_refresh_token(print_output=print_output)
    except InvalidConfigError:
        raise

    # Obtain access token and account ID
    try:
        accessToken, accountId = _get_cloud_sync_access_parameters(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    # Step 2: Retrieve list of relationships

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/relationships-v2"
    headers = {
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    # Call API to retrieve list of relationships
    response = requests.get(url = url, headers = headers)

    # Check for API response status code of 200; if not 200, raise error
    if response.status_code != 200:
        errorMessage = "Error calling Cloud Sync API to retrieve list of relationships."
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    # Constrict list of relationships
    relationships = json.loads(response.text)
    relationshipsList = list()
    for relationship in relationships:
        relationshipDetails = dict()
        relationshipDetails["id"] = relationship["id"]
        relationshipDetails["source"] = relationship["source"]
        relationshipDetails["target"] = relationship["target"]
        relationshipsList.append(relationshipDetails)

    # Print list of relationships
    if print_output:
        print(yaml.dump(relationshipsList))

    return relationshipsList


def list_snap_mirror_relationships(print_output: bool = False, cluster_name: str = None) -> list():
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

        try:
            # Retrieve all relationships for which destination is on current cluster
            destinationRelationships = NetAppSnapmirrorRelationship.get_collection()

            # Do not retrieve relationships for which source is on current cluster
            # Note: Uncomment below line to retrieve all relationships for which source is on current cluster, then add sourceRelationships to for loop
            # sourceRelationships = NetAppSnapmirrorRelationship.get_collection(list_destinations_only=True)

            # Construct list of relationships
            relationshipsList = list()
            for relationship in destinationRelationships:
                # Retrieve relationship details
                try:
                    relationship.get()
                except NetAppRestError as err:
                    relationship.get(list_destinations_only=True)

                # Set cluster value
                if hasattr(relationship.source, "cluster"):
                    sourceCluster = relationship.source.cluster.name
                else:
                    sourceCluster = "user's cluster"
                if hasattr(relationship.destination, "cluster"):
                    destinationCluster = relationship.destination.cluster.name
                else:
                    destinationCluster = "user's cluster"

                # Set transfer state value
                if hasattr(relationship, "transfer"):
                    transferState = relationship.transfer.state
                else:
                    transferState = None

                # Set healthy value
                if hasattr(relationship, "healthy"):
                    healthy = relationship.healthy
                else:
                    healthy = "unknown"

                # Construct dict containing relationship details
                relationshipDict = {
                    "UUID": relationship.uuid,
                    "Type": relationship.policy.type,
                    "Healthy": healthy,
                    "Current Transfer Status": transferState,
                    "Source Cluster": sourceCluster,
                    "Source SVM": relationship.source.svm.name,
                    "Source Volume": relationship.source.path.split(":")[1],
                    "Dest Cluster": destinationCluster,
                    "Dest SVM": relationship.destination.svm.name,
                    "Dest Volume": relationship.destination.path.split(":")[1]
                }

                # Append dict to list of relationships
                relationshipsList.append(relationshipDict)

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Print list of relationships
        if print_output:
            # Convert relationships array to Pandas DataFrame
            relationshipsDF = pd.DataFrame.from_dict(relationshipsList, dtype="string")
            print(tabulate(relationshipsDF, showindex=False, headers=relationshipsDF.columns))

        return relationshipsList

    else:
        raise ConnectionTypeError()


def list_snapshots(volume_name: str, cluster_name: str = None, svm_name: str = None, print_output: bool = False) -> list():
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

        # Retrieve svm from config file
        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
        except:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        # Retrieve snapshots
        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Construct list of snapshots
            snapshotsList = list()
            for snapshot in NetAppSnapshot.get_collection(volume.uuid):
                # Retrieve snapshot
                snapshot.get()

                # Construct dict of snapshot details
                snapshotDict = {"Snapshot Name": snapshot.name, "Create Time": snapshot.create_time}

                # Append dict to list of snapshots
                snapshotsList.append(snapshotDict)

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Print list of snapshots
        if print_output:
            # Convert snapshots array to Pandas DataFrame
            snapshotsDF = pd.DataFrame.from_dict(snapshotsList, dtype="string")
            print(tabulate(snapshotsDF, showindex=False, headers=snapshotsDF.columns))

        return snapshotsList

    else:
        raise ConnectionTypeError()


def list_volumes(check_local_mounts: bool = False, include_space_usage_details: bool = False, print_output: bool = False, cluster_name: str = None, svm_name: str = None) -> list():
    # Retrieve config details from config file
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if print_output :
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

        try:
            svmname=config["svm"]
            if svm_name:
                svmname = svm_name 

            # Retrieve all volumes for SVM
            volumes = NetAppVolume.get_collection(svm=svmname)

            # Retrieve local mounts if desired
            if check_local_mounts :
                mounts = subprocess.check_output(['mount']).decode()

            # Construct list of volumes; do not include SVM root volume
            volumesList = list()
            for volume in volumes:
                baseVolumeFields = "nas.path,size,style,clone,flexcache_endpoint_type"
                try :
                    volumeFields = baseVolumeFields
                    if include_space_usage_details :
                        volumeFields += ",space,constituents"
                    volume.get(fields=volumeFields)
                except NetAppRestError as err :
                    volumeFields = baseVolumeFields
                    if include_space_usage_details :
                        volumeFields += ",space"
                    volume.get(fields=volumeFields)

                # Retrieve volume export path; handle case where volume is not exported
                if hasattr(volume, "nas"):
                    volumeExportPath = volume.nas.path
                else:
                    volumeExportPath = None

                # Include all vols except for SVM root vol
                if volumeExportPath != "/":
                    # Determine volume type
                    type = volume.style

                    # Construct NFS mount target
                    if not volumeExportPath :
                        nfsMountTarget = None
                    else :
                        nfsMountTarget = config["dataLif"]+":"+volume.nas.path
                        if svmname != config["svm"]:
                            nfsMountTarget = svmname+":"+volume.nas.path


                    # Construct clone source
                    clone = "no"
                    cloneParentSvm = ""
                    cloneParentVolume = ""
                    cloneParentSnapshot = ""

                    try:
                        cloneParentSvm = volume.clone.parent_svm.name 
                        cloneParentVolume = volume.clone.parent_volume.name
                        cloneParentSnapshot = volume.clone.parent_snapshot.name
                        clone = "yes"
                    except:
                        pass

                    # Determine if FlexCache
                    if volume.flexcache_endpoint_type == "cache":
                        flexcache = "yes"
                    else:
                        flexcache = "no"

                    # Convert size in bytes to "pretty" size (size in KB, MB, GB, or TB)
                    prettySize = _convert_bytes_to_pretty_size(size_in_bytes=volume.size)
                    if include_space_usage_details :
                        try :
                            snapshotReserve = str(volume.space.snapshot.reserve_percent) + "%"
                            logicalCapacity = float(volume.space.size) * (1 - float(volume.space.snapshot.reserve_percent)/100)
                            prettyLogicalCapacity = _convert_bytes_to_pretty_size(size_in_bytes=logicalCapacity)
                            logicalUsage = float(volume.space.used)
                            prettyLogicalUsage = _convert_bytes_to_pretty_size(size_in_bytes=logicalUsage)
                        except :
                            snapshotReserve = "Unknown"
                            prettyLogicalCapacity = "Unknown"
                            prettyLogicalUsage = "Unknown"
                        try :
                            if type == "flexgroup" :
                                totalFootprint: float = 0.0
                                for constituentVolume in volume.constituents :
                                    totalFootprint += float(constituentVolume["space"]["total_footprint"])
                            else :
                                totalFootprint = float(volume.space.footprint) + float(volume.space.metadata)
                            prettyFootprint = _convert_bytes_to_pretty_size(size_in_bytes=totalFootprint)
                        except :
                            prettyFootprint = "Unknown"

                    # Construct dict containing volume details; optionally include local mountpoint
                    volumeDict = {
                        "Volume Name": volume.name,
                        "Size": prettySize
                    }
                    if include_space_usage_details :
                        volumeDict["Snap Reserve"] = snapshotReserve
                        volumeDict["Capacity"] = prettyLogicalCapacity
                        volumeDict["Usage"] = prettyLogicalUsage
                        volumeDict["Footprint"] = prettyFootprint
                    volumeDict["Type"] = volume.style
                    volumeDict["NFS Mount Target"] = nfsMountTarget
                    if check_local_mounts:
                        localMountpoint = ""
                        for mount in mounts.split("\n") :
                            mountDetails = mount.split(" ")
                            if mountDetails[0] == nfsMountTarget :
                                localMountpoint = mountDetails[2]
                        volumeDict["Local Mountpoint"] = localMountpoint
                    volumeDict["FlexCache"] = flexcache
                    volumeDict["Clone"] = clone
                    volumeDict["Source SVM"] = cloneParentSvm
                    volumeDict["Source Volume"] = cloneParentVolume
                    volumeDict["Source Snapshot"] = cloneParentSnapshot

                    # Append dict to list of volumes
                    volumesList.append(volumeDict)

        except NetAppRestError as err:
            if print_output :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Print list of volumes
        if print_output:
            # Convert volumes array to Pandas DataFrame
            volumesDF = pd.DataFrame.from_dict(volumesList, dtype="string")
            print(tabulate(volumesDF, showindex=False, headers=volumesDF.columns))

        return volumesList

    else:
        raise ConnectionTypeError()


def mount_volume(volume_name: str, mountpoint: str, cluster_name: str = None, svm_name: str = None, lif_name: str = None, readonly: bool = False, print_output: bool = False):
    nfsMountTarget = None
    
    svm = None
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        svm = config["svm"]
        if svm_name:
            svm = svm_name
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name 

    # Retrieve list of volumes
    try:
        volumes = list_volumes(check_local_mounts=True, svm_name = svm)
    except (InvalidConfigError, APIConnectionError):
        if print_output:
            print("Error: Error retrieving NFS mount target for volume.")
        raise

    # Retrieve NFS mount target for volume, and check that no volume is currently mounted at specified mountpoint
    for volume in volumes:
        # Check mountpoint
        if mountpoint == volume["Local Mountpoint"]:
            if print_output:
                print("Error: Volume '" + volume["Volume Name"] + "' is already mounted at '" + mountpoint + "'.")
            raise MountOperationError("Another volume mounted at mountpoint")

        if volume_name == volume["Volume Name"]:
            # Retrieve NFS mount target
            nfsMountTarget = volume["NFS Mount Target"]

    # Raise error if invalid volume name was entered
    if not nfsMountTarget:
        if print_output:
            print("Error: Invalid volume name specified.")
        raise InvalidVolumeParameterError("name")
    
    try:
        if lif_name:
            nfsMountTarget = lif_name+':'+nfsMountTarget.split(':')[1]
    except:
        if print_output:
            print("Error: Error retrieving NFS mount target for volume.")
        raise

    # Print message describing action to be understaken
    if print_output:
        if readonly:
            print("Mounting volume '" + svm+':'+volume_name + "' as '"+nfsMountTarget+"' at '" + mountpoint + "' as read-only.")
        else:
            print("Mounting volume '" + svm+':'+volume_name + "' as '"+nfsMountTarget+"' at '" + mountpoint + "'.")

    # Create mountpoint if it doesn't already exist
    mountpoint = os.path.expanduser(mountpoint)
    try:
        os.mkdir(mountpoint)
    except FileExistsError:
        pass

    # Mount volume
    if readonly:
        try:
            subprocess.check_call(['mount', '-o', 'ro', nfsMountTarget, mountpoint])
            if print_output:
                print("Volume mounted successfully.")
        except subprocess.CalledProcessError as err:
            if print_output:
                print("Error: Error running mount command: ", err)
            raise MountOperationError(err)
    else:
        try:
            subprocess.check_call(['mount', nfsMountTarget, mountpoint])
            if print_output:
                print("Volume mounted successfully.")
        except subprocess.CalledProcessError as err:
            if print_output:
                print("Error: Error running mount command: ", err)
            raise MountOperationError(err)



# Function to unmount volume
def unmount_volume(mountpoint: str, print_output: bool = False):
    # Print message describing action to be understaken
    if print_output:
        print("Unmounting volume at '" + mountpoint + "'.")

    # Un-mount volume
    try:
        subprocess.check_call(['umount', mountpoint])
        if print_output:
            print("Volume unmounted successfully.")
    except subprocess.CalledProcessError as err:
        if print_output:
            print("Error: Error running unmount command: ", err)
        raise MountOperationError(err)


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


def pull_bucket_from_s3(s3_bucket: str, local_directory: str, s3_object_key_prefix: str = "", print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Add slash to end of local directory path if not present
    if not local_directory.endswith(os.sep):
        local_directory += os.sep

    # Multithread the download operation
    with ThreadPoolExecutor() as executor:
        try:
            # Instantiate S3 session
            s3 = _instantiate_s3_session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, print_output=print_output)

            # Loop through all objects with prefix in bucket and download
            bucket = s3.Bucket(s3_bucket)
            for obj in bucket.objects.filter(Prefix=s3_object_key_prefix):
                executor.submit(_download_from_s3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, s3ObjectKey=obj.key, localFile=local_directory+obj.key, print_output=print_output)

        except APIConnectionError:
            raise

        except Exception as err:
            if print_output:
                print("Error: S3 API error: ", err)
            raise APIConnectionError(err)

    print("Download complete.")


def pull_object_from_s3(s3_bucket: str, s3_object_key: str, local_file: str = None, print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Set S3 object key
    if not local_file:
        local_file = s3_object_key

    # Upload file
    try:
        _download_from_s3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, s3ObjectKey=s3_object_key, localFile=local_file, print_output=print_output)
    except APIConnectionError:
        raise

    print("Download complete.")


def push_directory_to_s3(s3_bucket: str, local_directory: str, s3_object_key_prefix: str = "",
                         s3_extra_args: str = None, print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Multithread the upload operation
    with ThreadPoolExecutor() as executor:
        # Loop through all files in directory
        for dirpath, dirnames, filenames in os.walk(local_directory):
            # Exclude hidden files and directories
            filenames = [filename for filename in filenames if not filename[0] == '.']
            dirnames[:] = [dirname for dirname in dirnames if not dirname[0] == '.']

            for filename in filenames:
                # Build filepath
                if local_directory.endswith(os.sep):
                    dirpathBeginIndex = len(local_directory)
                else:
                    dirpathBeginIndex = len(local_directory) + 1

                subdirpath = dirpath[dirpathBeginIndex:]

                if subdirpath:
                    filepath = subdirpath + os.sep + filename
                else:
                    filepath = filename

                # Set S3 object details
                s3ObjectKey = s3_object_key_prefix + filepath
                localFile = dirpath + os.sep + filename

                # Upload file
                try:
                    executor.submit(_upload_to_s3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, localFile=localFile, s3ObjectKey=s3ObjectKey, s3ExtraArgs=s3_extra_args, print_output=print_output)
                except APIConnectionError:
                    raise

    print("Upload complete.")


def push_file_to_s3(s3_bucket: str, local_file: str, s3_object_key: str = None, s3_extra_args: str = None, print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Set S3 object key
    if not s3_object_key:
        s3_object_key = local_file

    # Upload file
    try:
        _upload_to_s3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, localFile=local_file, s3ObjectKey=s3_object_key, s3ExtraArgs=s3_extra_args, print_output=print_output)
    except APIConnectionError:
        raise

    print("Upload complete.")


def restore_snapshot(volume_name: str, snapshot_name: str, cluster_name: str = None, svm_name : str = None, print_output: bool = False):
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

        # Retrieve svm from config file
        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
        except:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        if print_output:
            print("Restoring snapshot '" + snapshot_name + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Retrieve snapshot
            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshot_name)
            if not snapshot:
                if print_output:
                    print("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            # Restore snapshot
            volume.patch(volume.uuid, **{"restore_to.snapshot.name": snapshot.name, "restore_to.snapshot.uuid": snapshot.uuid}, poll=True)
            if print_output:
                print("Snapshot restored successfully.")

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def sync_cloud_sync_relationship(relationship_id: str, wait_until_complete: bool = False, print_output: bool = False):
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API

    # Retrieve refresh token
    try:
        refreshToken = _retrieve_cloud_central_refresh_token(print_output=print_output)
    except InvalidConfigError:
        raise

    # Obtain access token and account ID
    try:
        accessToken, accountId = _get_cloud_sync_access_parameters(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    # Step 2: Trigger Cloud Sync sync

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/relationships/%s/sync" % relationship_id
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    # Call API to trigger sync
    if print_output:
        print("Triggering sync operation for Cloud Sync relationship (ID = " + relationship_id + ").")
    response = requests.put(url = url, headers = headers)

    # Check for API response status code of 202; if not 202, raise error
    if response.status_code != 202:
        errorMessage = "Error calling Cloud Sync API to trigger sync operation."
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    if print_output:
        print("Sync operation successfully triggered.")

    # Step 3: Obtain status of the sync operation; keep checking until the sync operation has completed

    if wait_until_complete:
        while True:
            # Define parameters for API call
            url = "https://cloudsync.netapp.com/api/relationships-v2/%s" % relationship_id
            headers = {
                "Accept": "application/json",
                "x-account-id": accountId,
                "Authorization": "Bearer " + accessToken
            }

            # Call API to obtain status of sync operation
            response = requests.get(url = url, headers = headers)

            # Parse response to retrieve status of sync operation
            try:
                responseBody = json.loads(response.text)
                latestActivityType = responseBody["activity"]["type"]
                latestActivityStatus = responseBody["activity"]["status"]
            except:
                errorMessage = "Error obtaining status of sync operation from Cloud Sync API."
                if print_output:
                    print("Error:", errorMessage)
                    _print_api_response(response)
                raise APIConnectionError(errorMessage, response)

            # End execution if the latest update is complete
            if latestActivityType == "Sync":
                if latestActivityStatus == "DONE":
                    if print_output:
                        print("Success: Sync operation is complete.")
                    break
                elif latestActivityStatus == "FAILED":
                    if print_output:
                        failureMessage = responseBody["activity"]["failureMessage"]
                        print("Error: Sync operation failed.")
                        print("Message:", failureMessage)
                    raise CloudSyncSyncOperationError(latestActivityStatus, failureMessage)
                elif latestActivityStatus == "RUNNING":
                    # Print message re: progress
                    if print_output:
                        print("Sync operation is not yet complete. Status:", latestActivityStatus)
                        print("Checking again in 60 seconds...")
                else:
                    if print_output:
                        print ("Error: Unknown sync operation status (" + latestActivityStatus + ") returned by Cloud Sync API.")
                    raise CloudSyncSyncOperationError(latestActivityStatus)

            # Sleep for 60 seconds before checking progress again
            time.sleep(60)

def create_snap_mirror_relationship(source_svm: str, source_vol: str, target_vol: str, target_svm: str = None, cluster_name: str = None, 
        schedule: str = '', policy: str = 'MirrorAllSnapshots', action: str = None, print_output: bool = False):
    # Retrieve config details from config file
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if print_output :
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
        if not target_svm: 
            target_svm = svm 

        try: 
            uuid = None
            snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": target_svm+":"+target_vol})
            for rel in snapmirror_relationship:
                # Retrieve relationship details
                try:
                    rel.get()
                    uuid = rel.uuid
                except NetAppRestError as err:
                    if print_output:
                        print("Error: ONTAP Rest API Error: ", err)
            if uuid:
                if print_output:
                    print("Error: relationship alreay exists: "+target_svm+":"+target_vol)
                raise InvalidConfigError()
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)         
        
        try:
            newRelationDict = {
                "source": {
                    "path": source_svm+":"+source_vol
                }, 
                "destination": { 
                    "path": target_svm+":"+target_vol
                }
                #due to bug 1311226 setting the policy wil be done using cli api 
                # "policy":  {
                #     "name": policy,
                # },
            }
            # if schedule != '':
            #     newRelationDict['schedule'] = schedule

            if print_output:
                print("Creating snapmirror relationship: "+source_svm+":"+source_vol+" -> "+target_svm+":"+target_vol)
            newRelationship = NetAppSnapmirrorRelationship.from_dict(newRelationDict)
            newRelationship.post(poll=True, poll_timeout=120)
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        try:
            if print_output:
                print("Setting snapmirror policy as: "+policy+" schedule:"+schedule)
                response = NetAppCLI().execute("snapmirror modify",destination_path=target_svm+":"+target_vol,body={"policy": policy, "schedule":schedule})
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)            

        try: 
            uuid = None
            relation = None
            snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": target_svm+":"+target_vol})
            for relation in snapmirror_relationship:
                # Retrieve relationship details
                try:
                    relation.get()
                    uuid = relation.uuid
                except NetAppRestError as err:
                    if print_output:
                        print("Error: ONTAP Rest API Error: ", err)
                    raise APIConnectionError(err)
            if not uuid:
                if print_output:
                    print("Error: relationship was not created: "+target_svm+":"+target_vol)
                raise InvalidConfigError()
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        if action in ["resync","initialize"]:
            try:
                if print_output:
                    print("Setting state to snapmirrored, action:"+action)
                patchRelation = NetAppSnapmirrorRelationship(uuid=uuid)
                patchRelation.state = "snapmirrored"
                patchRelation.patch(poll=True, poll_timeout=120)
            except NetAppRestError as err:
                if print_output:
                    print("Error: ONTAP Rest API Error: ", err)
                raise APIConnectionError(err)                

def sync_snap_mirror_relationship(uuid: str = None, svm_name: str = None, volume_name: str = None, cluster_name: str = None, wait_until_complete: bool = False, print_output: bool = False):
    # Retrieve config details from config file
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if print_output :
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

        if volume_name:
            svm = config["svm"]
            if svm_name: 
                svm = svm_name

            snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": svm+":"+volume_name})
            for rel in snapmirror_relationship:
                # Retrieve relationship details
                try:
                    rel.get()
                    uuid = rel.uuid
                except NetAppRestError as err:
                    if print_output:
                        print("Error: ONTAP Rest API Error: ", err)
            if not uuid:
                snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": svm+":"})
                for rel in snapmirror_relationship:
                    try:
                        rel.get()
                        uuid = rel.uuid
                    except NetAppRestError as err:
                        if print_output:
                            print("Error: ONTAP Rest API Error: ", err)
                    if uuid: 
                        if print_output:
                            print("volume is part of svm-dr relationshitp: "+svm+":")                    

        if not uuid:
            if print_output:
                print("Error: relationship could not be found.")
            raise SnapMirrorSyncOperationError("not found")

        if print_output:
            print("Triggering sync operation for SnapMirror relationship (UUID = " + uuid + ").")

        try:
            # Trigger sync operation for SnapMirror relationship
            transfer = NetAppSnapmirrorTransfer(uuid)
            transfer.post(poll=True)
        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        if print_output:
            print("Sync operation successfully triggered.")

        if wait_until_complete:
            # Wait to perform initial check
            print("Waiting for sync operation to complete.")
            print("Status check will be performed in 10 seconds...")
            time.sleep(10)

            while True:
                # Retrieve relationship
                relationship = NetAppSnapmirrorRelationship.find(uuid=uuid)
                relationship.get()

                # Check status of sync operation
                if hasattr(relationship, "transfer"):
                    transferState = relationship.transfer.state
                else:
                    transferState = None

                # if transfer is complete, end execution
                if (not transferState) or (transferState == "success"):
                    healthy = relationship.healthy
                    if healthy:
                        if print_output:
                            print("Success: Sync operation is complete.")
                        break
                    else:
                        if print_output:
                            print("Error: Relationship is not healthy. Access ONTAP System Manager for details.")
                        raise SnapMirrorSyncOperationError("not healthy")
                elif transferState != "transferring":
                    if print_output:
                        print ("Error: Unknown sync operation status (" + transferState + ") returned by ONTAP API.")
                    raise SnapMirrorSyncOperationError(transferState)
                else:
                    # Print message re: progress
                    if print_output:
                        print("Sync operation is not yet complete. Status:", transferState)
                        print("Checking again in 10 seconds...")

                # Sleep for 10 seconds before checking progress again
                time.sleep(10)

    else:
        raise ConnectionTypeError()

#
# Deprecated function names
#


@deprecated
def cloneVolume(newVolumeName: str, sourceVolumeName: str, sourceSnapshotName: str = None, unixUID: str = None, unixGID: str = None, mountpoint: str = None, printOutput: bool = False) :
    clone_volume(new_volume_name=newVolumeName, source_volume_name=sourceVolumeName, source_snapshot_name=sourceSnapshotName,
                             mountpoint=mountpoint, unix_uid=unixUID, unix_gid=unixGID, print_output=printOutput)


@deprecated
def createSnapshot(volumeName: str, snapshotName: str = None, printOutput: bool = False) :
    create_snapshot(volume_name=volumeName, snapshot_name=snapshotName, print_output=printOutput)


@deprecated
def createVolume(volumeName: str, volumeSize: str, guaranteeSpace: bool = False, volumeType: str = "flexvol", unixPermissions: str = "0777", unixUID: str = "0", unixGID: str = "0", exportPolicy: str = "default", snapshotPolicy: str = "none", aggregate: str = None, mountpoint: str = None, printOutput: bool = False) :
    create_volume(volume_name=volumeName, volume_size=volumeSize, guarantee_space=guaranteeSpace, volume_type=volumeType, unix_permissions=unixPermissions, unix_uid=unixUID,
                              unix_gid=unixGID, export_policy=exportPolicy, snapshot_policy=snapshotPolicy, aggregate=aggregate, mountpoint=mountpoint, print_output=printOutput)


@deprecated
def deleteSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False) :
    delete_snapshot(volume_name=volumeName, snapshot_name=snapshotName, print_output=printOutput)


@deprecated
def deleteVolume(volumeName: str, printOutput: bool = False) :
    delete_volume(volume_name=volumeName, print_output=printOutput)


@deprecated
def listCloudSyncRelationships(printOutput: bool = False) -> list() :
    return list_cloud_sync_relationships(print_output=printOutput)


@deprecated
def listSnapMirrorRelationships(printOutput: bool = False) -> list() :
    return list_snap_mirror_relationships(print_output=printOutput)


@deprecated
def listSnapshots(volumeName: str, printOutput: bool = False) -> list() :
    return list_snapshots(volume_name=volumeName, print_output=printOutput)


@deprecated
def listVolumes(checkLocalMounts: bool = False, includeSpaceUsageDetails: bool = False, printOutput: bool = False) -> list() :
    return list_volumes(check_local_mounts=checkLocalMounts, include_space_usage_details=includeSpaceUsageDetails, print_output=printOutput)


@deprecated
def mountVolume(volumeName: str, mountpoint: str, printOutput: bool = False) :
    mount_volume(volume_name=volumeName, mountpoint=mountpoint, print_output=printOutput)


@deprecated
def prepopulateFlexCache(volumeName: str, paths: list, printOutput: bool = False) :
    prepopulate_flex_cache(volume_name=volumeName, paths=paths, print_output=printOutput)


@deprecated
def pullBucketFromS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "", printOutput: bool = False) :
    pull_bucket_from_s3(s3_bucket=s3Bucket, local_directory=localDirectory, s3_object_key_prefix=s3ObjectKeyPrefix, print_output=printOutput)


@deprecated
def pullObjectFromS3(s3Bucket: str, s3ObjectKey: str, localFile: str = None, printOutput: bool = False) :
    pull_object_from_s3(s3_bucket=s3Bucket, s3_object_key=s3ObjectKey, local_file=localFile, print_output=printOutput)


@deprecated
def pushDirectoryToS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "", s3ExtraArgs: str = None, printOutput: bool = False) :
    push_directory_to_s3(s3_bucket=s3Bucket, local_directory=localDirectory, s3_object_key_prefix=s3ObjectKeyPrefix, s3_extra_args=s3ExtraArgs, print_output=printOutput)


@deprecated
def pushFileToS3(s3Bucket: str, localFile: str, s3ObjectKey: str = None, s3ExtraArgs: str = None, printOutput: bool = False) :
    push_file_to_s3(s3_bucket=s3Bucket, s3_object_key=s3ObjectKey, local_file=localFile, s3_extra_args=s3ExtraArgs, print_output=printOutput)


@deprecated
def restoreSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False) :
    restore_snapshot(volume_name=volumeName, snapshot_name=snapshotName, print_output=printOutput)


@deprecated
def syncCloudSyncRelationship(relationshipID: str, waitUntilComplete: bool = False, printOutput: bool = False) :
    sync_cloud_sync_relationship(relationship_id=relationshipID, wait_until_complete=waitUntilComplete, print_output=printOutput)


@deprecated
def syncSnapMirrorRelationship(uuid: str, waitUntilComplete: bool = False, printOutput: bool = False) :
    sync_snap_mirror_relationship(uuid=uuid, wait_until_complete=waitUntilComplete, print_output=printOutput)
