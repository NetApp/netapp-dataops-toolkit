"""NetApp Data Science Toolkit for Traditional Environments import module.

This module provides the public functions available to be imported directly
by applications using the import method of utilizing the toolkit.
"""
import base64
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import boto3
from netapp_ontap import config as netappConfig
from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Flexcache as NetAppFlexCache
from netapp_ontap.resources import SnapmirrorRelationship as NetAppSnapmirrorRelationship
from netapp_ontap.resources import Snapshot as NetAppSnapshot
from netapp_ontap.resources import Volume as NetAppVolume
import pandas as pd
import requests
from tabulate import tabulate
import yaml


__version__ = "0.0.1a1"

#
# The following attributes are unique to the traditional package.
#
from netapp_dstk.ntap_dsutil import retrieveCloudCentralRefreshToken, getCloudSyncAccessParameters, printAPIResponse

helpTextStandard = '''
The NetApp Data Science Toolkit is a Python library that makes it simple for data scientists and data engineers to perform various data management tasks, such as provisioning a new data volume, near-instantaneously cloning a data volume, and near-instantaneously snapshotting a data volume for traceability/baselining.

Basic Commands:

\tconfig\t\t\t\tCreate a new config file (a config file is required to perform other commands).
\thelp\t\t\t\tPrint help text.
\tversion\t\t\t\tPrint version details.

Data Volume Management Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tclone volume\t\t\tCreate a new data volume that is an exact copy of an existing volume.
\tcreate volume\t\t\tCreate a new data volume.
\tdelete volume\t\t\tDelete an existing data volume.
\tlist volumes\t\t\tList all data volumes.
\tmount volume\t\t\tMount an existing data volume locally. Note: on Linux hosts - must be run as root.

Snapshot Management Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tcreate snapshot\t\t\tCreate a new snapshot for a data volume.
\tdelete snapshot\t\t\tDelete an existing snapshot for a data volume.
\tlist snapshots\t\t\tList all snapshots for a data volume.
\trestore snapshot\t\tRestore a snapshot for a data volume (restore the volume to its exact state at the time that the snapshot was created).

Data Fabric Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tlist cloud-sync-relationships\tList all existing Cloud Sync relationships.
\tsync cloud-sync-relationship\tTrigger a sync operation for an existing Cloud Sync relationship.
\tpull-from-s3 bucket\t\tPull the contents of a bucket from S3.
\tpull-from-s3 object\t\tPull an object from S3.
\tpush-to-s3 directory\t\tPush the contents of a directory to S3 (multithreaded).
\tpush-to-s3 file\t\t\tPush a file to S3.

Advanced Data Fabric Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tprepopulate flexcache\t\tPrepopulate specific files/directories on a FlexCache volume (ONTAP 9.8 and above ONLY).
\tlist snapmirror-relationships\tList all existing SnapMirror relationships.
\tsync snapmirror-relationship\tTrigger a sync operation for an existing SnapMirror relationship.
'''


class ConnectionTypeError(Exception):
    """Error that will be raised when an invalid connection type is given"""
    pass


# Technically this is common with cloud but the config referenced is different.
# TODO: Consider making this common?
class InvalidConfigError(Exception):
    """Error that will be raised when the config file is invalid or missing"""
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

#
# The following attributes and functions are common with the cloud package.
# TODO: Consider consolidating these in a new third package (common)?
#


class APIConnectionError(Exception) :
    '''Error that will be raised when an API connection cannot be established'''
    pass


def getTarget(args: list) -> str:
    try:
        target = args[2]
    except:
        handleInvalidCommand()
    return target


def handleInvalidCommand(helpText: str = helpTextStandard, invalidOptArg: bool = False):
    if invalidOptArg:
        print("Error: Invalid option/argument.")
    else:
        print("Error: Invalid command.")
    print(helpText)
    sys.exit(1)


#
# The following attributes and functions are unique to the traditional package
#

# TODO: make this private. Is this common with cloud?
def downloadFromS3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool,
                   s3CACertBundle: str, s3Bucket: str, s3ObjectKey: str, localFile: str, printOutput: bool = False):
    # Instantiate S3 session
    try:
        s3 = instantiateS3Session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId,
                                  s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert,
                                  s3CACertBundle=s3CACertBundle, printOutput=printOutput)
    except Exception as err:
        if printOutput:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)

    if printOutput:
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
        if printOutput:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)


# TODO: make this function private
def instantiateConnection(config: dict, connectionType: str = "ONTAP", printOutput: bool = False):
    if connectionType == "ONTAP":
        ## Connection details for ONTAP cluster
        try:
            ontapClusterMgmtHostname = config["hostname"]
            ontapClusterAdminUsername = config["username"]
            ontapClusterAdminPasswordBase64 = config["password"]
            verifySSLCert = config["verifySSLCert"]
        except:
            if printOutput:
                printInvalidConfigError()
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


# TODO: Make private. Is this common with cloud?
def instantiateS3Session(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str, printOutput: bool = False):
    # Instantiate session
    session = boto3.session.Session(aws_access_key_id=s3AccessKeyId, aws_secret_access_key=s3SecretAccessKey)

    if s3VerifySSLCert:
        if s3CACertBundle:
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=s3CACertBundle)
        else:
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint)
    else:
        s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=False)

    return s3


# TODO: Make this function private
def printInvalidConfigError() :
    print("Error: Missing or invalid config file. Run `./ntap_dsutil.py config` to create config file.")


# TODO: Check if this should be made private after all functions moved.
def retrieveConfig(configDirPath: str = "~/.ntap_dsutil", configFilename: str = "config.json",
                   printOutput: bool = False) -> dict:
    configDirPath = os.path.expanduser(configDirPath)
    configFilePath = os.path.join(configDirPath, configFilename)
    try:
        with open(configFilePath, 'r') as configFile:
            # Read connection details from config file; read into dict
            config = json.load(configFile)
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()
    return config


# TODO: Make this function private.
def retrieveS3AccessDetails(printOutput: bool = False) -> (str, str, str, bool, str):
    # Retrieve refresh token from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        s3Endpoint = config["s3Endpoint"]
        s3AccessKeyId = config["s3AccessKeyId"]
        s3SecretAccessKeyBase64 = config["s3SecretAccessKey"]
        s3VerifySSLCert = config["s3VerifySSLCert"]
        s3CACertBundle = config["s3CACertBundle"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Decode base64-encoded refresh token
    s3SecretAccessKeyBase64Bytes = s3SecretAccessKeyBase64.encode("ascii")
    s3SecretAccessKeyBytes = base64.b64decode(s3SecretAccessKeyBase64Bytes)
    s3SecretAccessKey = s3SecretAccessKeyBytes.decode("ascii")

    return s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle


# TODO: make this private. Is this common with cloud?
def uploadToS3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str,
               s3Bucket: str, localFile: str, s3ObjectKey: str, s3ExtraArgs: str = None, printOutput: bool = False):
    # Instantiate S3 session
    try:
        s3 = instantiateS3Session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId,
                                  s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert,
                                  s3CACertBundle=s3CACertBundle, printOutput=printOutput)
    except Exception as err:
        if printOutput:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)

    # Upload file
    if printOutput:
        print("Uploading file '" + localFile + "' to bucket '" + s3Bucket + "' and applying key '" + s3ObjectKey + "'.")

    try:
        if s3ExtraArgs:
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile, ExtraArgs=json.loads(s3ExtraArgs))
        else:
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile)
    except Exception as err:
        if printOutput:
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)

#
# Public importable functions specific to the traditional package
#


def cloneVolume(newVolumeName: str, sourceVolumeName: str, sourceSnapshotName: str = None,
                unixUID: str = None, unixGID: str = None, mountpoint: str = None,
                printOutput: bool = False):
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve values from config file if not passed into function
        try:
            svm = config["svm"]
            if not unixUID:
                unixUID = config["defaultUnixUID"]
            if not unixGID:
                unixGID = config["defaultUnixGID"]
        except:
            if printOutput:
                printInvalidConfigError()
            raise InvalidConfigError()

        # Check unix uid for validity
        try:
            unixUID = int(unixUID)
        except:
            if printOutput:
                print("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        # Check unix gid for validity
        try:
            unixGID = int(unixGID)
        except:
            if printOutput:
                print("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        # Create volume
        if printOutput:
            print("Creating clone volume '" + newVolumeName + "' from source volume '" + sourceVolumeName + "'.")

        try:
            # Retrieve source volume
            sourceVolume = NetAppVolume.find(name=sourceVolumeName, svm=svm)
            if not sourceVolume:
                if printOutput:
                    print("Error: Invalid source volume name.")
                raise InvalidVolumeParameterError("name")

            # Construct dict representing new volume
            newVolumeDict = {
                "name": newVolumeName,
                "svm": {"name": svm},
                "nas": {
                    "path": "/" + newVolumeName
                },
                "clone": {
                    "is_flexclone": True,
                    "parent_svm": {
                        "name": sourceVolume.svm.name,
                        "uuid": sourceVolume.svm.uuid
                    },
                    "parent_volume": {
                        "name": sourceVolume.name,
                        "uuid": sourceVolume.uuid
                    }
                }
            }
            if unixUID != 0:
                newVolumeDict["nas"]["uid"] = unixUID
            else:
                if printOutput:
                    print("Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.")
            if unixGID != 0:
                newVolumeDict["nas"]["gid"] = unixGID
            else:
                if printOutput:
                    print("Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.")

            # Add source snapshot details to volume dict if specified
            if sourceSnapshotName:
                # Retrieve source snapshot
                sourceSnapshot = NetAppSnapshot.find(sourceVolume.uuid, name=sourceSnapshotName)
                if not sourceSnapshot:
                    if printOutput:
                        print("Error: Invalid source snapshot name.")
                    raise InvalidSnapshotParameterError("name")

                # Append source snapshot details to volume dict
                newVolumeDict["clone"]["parent_snapshot"] = {
                    "name": sourceSnapshot.name,
                    "uuid": sourceSnapshot.uuid
                }

            # Create new volume
            newVolume = NetAppVolume.from_dict(newVolumeDict)
            newVolume.post(poll=True, poll_timeout=120)
            if printOutput:
                print("Clone volume created successfully.")

        except NetAppRestError as err:
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Optionally mount newly created volume
        if mountpoint:
            try:
                mountVolume(volumeName=newVolumeName, mountpoint=mountpoint, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                if printOutput:
                    print("Error: Error mounting clone volume.")
                raise

    else:
        raise ConnectionTypeError()


def createSnapshot(volumeName: str, snapshotName: str = None, printOutput: bool = False):
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve svm from config file
        try:
            svm = config["svm"]
        except:
            if printOutput:
                printInvalidConfigError()
            raise InvalidConfigError()

        # Set snapshot name if not passed into function
        if not snapshotName:
            timestamp = datetime.today().strftime("%Y%m%d_%H%M%S")
            snapshotName = "ntap_dsutil_" + timestamp

        if printOutput:
            print("Creating snapshot '" + snapshotName + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume:
                if printOutput:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Create snapshot
            snapshot = NetAppSnapshot.from_dict({
                'name': snapshotName,
                'volume': volume.to_dict()
            })
            snapshot.post(poll=True)

            if printOutput:
                print("Snapshot created successfully.")

        except NetAppRestError as err:
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def createVolume(volumeName: str, volumeSize: str, guaranteeSpace: bool = False,
                 volumeType: str = "flexvol", unixPermissions: str = "0777",
                 unixUID: str = "0", unixGID: str = "0", exportPolicy: str = "default",
                 snapshotPolicy: str = "none", aggregate: str = None, mountpoint: str = None,
                 printOutput: bool = False):
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve values from config file if not passed into function
        try:
            svm = config["svm"]
            if not volumeType :
                volumeType = config["defaultVolumeType"]
            if not unixPermissions :
                unixPermissions = config["defaultUnixPermissions"]
            if not unixUID :
                unixUID = config["defaultUnixUID"]
            if not unixGID :
                unixGID = config["defaultUnixGID"]
            if not exportPolicy :
                exportPolicy = config["defaultExportPolicy"]
            if not snapshotPolicy :
                snapshotPolicy = config["defaultSnapshotPolicy"]
            if not aggregate :
                aggregate = config["defaultAggregate"]
        except:
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        # Check volume type for validity
        if volumeType not in ("flexvol", "flexgroup"):
            if printOutput:
                print("Error: Invalid volume type specified. Acceptable values are 'flexvol' and 'flexgroup'.")
            raise InvalidVolumeParameterError("size")

        # Check unix permissions for validity
        if not re.search("^0[0-7]{3}", unixPermissions):
            if printOutput:
                print("Error: Invalid unix permissions specified. Acceptable values are '0777', '0755', '0744', etc.")
            raise InvalidVolumeParameterError("unixPermissions")

        # Check unix uid for validity
        try:
            unixUID = int(unixUID)
        except:
            if printOutput :
                print("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        # Check unix gid for validity
        try:
            unixGID = int(unixGID)
        except:
            if printOutput:
                print("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        # Convert volume size to Bytes
        if re.search("^[0-9]+MB$", volumeSize):
            # Convert from MB to Bytes
            volumeSizeBytes = int(volumeSize[:len(volumeSize)-2]) * 1024**2
        elif re.search("^[0-9]+GB$", volumeSize):
            # Convert from GB to Bytes
            volumeSizeBytes = int(volumeSize[:len(volumeSize)-2]) * 1024**3
        elif re.search("^[0-9]+TB$", volumeSize):
            # Convert from TB to Bytes
            volumeSizeBytes = int(volumeSize[:len(volumeSize)-2]) * 1024**4
        else :
            if printOutput:
                print("Error: Invalid volume size specified. Acceptable values are '1024MB', '100GB', '10TB', etc.")
            raise InvalidVolumeParameterError("size")

        # Create dict representing volume
        volumeDict = {
            "name": volumeName,
            "svm": {"name": svm},
            "size": volumeSizeBytes,
            "style": volumeType,
            "nas": {
                "path": "/" + volumeName,
                "export_policy": {"name": exportPolicy},
                "security_style": "unix",
                "unix_permissions": unixPermissions,
                "uid": unixUID,
                "gid": unixGID
            },
            "snapshot_policy": {"name": snapshotPolicy}
        }

        # Set space guarantee field
        if guaranteeSpace:
            volumeDict["guarantee"] = {"type": "volume"}
        else:
            volumeDict["guarantee"] = {"type": "none"}

        # If flexvol -> set aggregate field
        if volumeType == "flexvol":
            volumeDict["aggregates"] = [{'name': aggregate}]

        # Create volume
        if printOutput:
            print("Creating volume '" + volumeName + "'.")
        try:
            volume = NetAppVolume.from_dict(volumeDict)
            volume.post(poll=True)
            if printOutput:
                print("Volume created successfully.")
        except NetAppRestError as err:
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Optionally mount newly created volume
        if mountpoint:
            try:
                mountVolume(volumeName=volumeName, mountpoint=mountpoint, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                if printOutput:
                    print("Error: Error mounting volume.")
                raise

    else:
        raise ConnectionTypeError()


def deleteSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False):
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve svm from config file
        try:
            svm = config["svm"]
        except:
            if printOutput:
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput:
            print("Deleting snapshot '" + snapshotName + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume:
                if printOutput:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Retrieve snapshot
            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshotName)
            if not snapshot:
                if printOutput:
                    print("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            # Delete snapshot
            snapshot.delete(poll=True)

            if printOutput:
                print("Snapshot deleted successfully.")

        except NetAppRestError as err :
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def deleteVolume(volumeName: str, printOutput: bool = False):
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve svm from config file
        try:
            svm = config["svm"]
        except:
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput:
            print("Deleting volume '" + volumeName + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume:
                if printOutput:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Delete volume
            volume.delete(poll=True)

            if printOutput:
                print("Volume deleted successfully.")

        except NetAppRestError as err:
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def listCloudSyncRelationships(printOutput: bool = False) -> list():
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API

    # Retrieve refresh token
    try:
        refreshToken = retrieveCloudCentralRefreshToken(printOutput=printOutput)
    except InvalidConfigError:
        raise

    # Obtain access token and account ID
    try:
        accessToken, accountId = getCloudSyncAccessParameters(refreshToken=refreshToken, printOutput=printOutput)
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
        if printOutput:
            print("Error:", errorMessage)
            printAPIResponse(response)
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
    if printOutput:
        print(yaml.dump(relationshipsList))

    return relationshipsList


def listSnapMirrorRelationships(printOutput: bool = False) -> list():
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
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
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Print list of relationships
        if printOutput:
            # Convert relationships array to Pandas DataFrame
            relationshipsDF = pd.DataFrame.from_dict(relationshipsList, dtype="string")
            print(tabulate(relationshipsDF, showindex=False, headers=relationshipsDF.columns))

        return relationshipsList

    else:
        raise ConnectionTypeError()


def listSnapshots(volumeName: str, printOutput: bool = False) -> list():
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve svm from config file
        try:
            svm = config["svm"]
        except:
            if printOutput:
                printInvalidConfigError()
            raise InvalidConfigError()

        # Retrieve snapshots
        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume:
                if printOutput:
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
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Print list of snapshots
        if printOutput:
            # Convert snapshots array to Pandas DataFrame
            snapshotsDF = pd.DataFrame.from_dict(snapshotsList, dtype="string")
            print(tabulate(snapshotsDF, showindex=False, headers=snapshotsDF.columns))

        return snapshotsList

    else:
        raise ConnectionTypeError()


def listVolumes(checkLocalMounts: bool = False, printOutput: bool = False) -> list():
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        try:
            # Retrieve all volumes for SVM
            volumes = NetAppVolume.get_collection(svm=config["svm"])

            # Retrieve local mounts if desired
            if checkLocalMounts :
                mounts = subprocess.check_output(['mount']).decode()

            # Construct list of volumes; do not include SVM root volume
            volumesList = list()
            for volume in volumes:
                volume.get(fields="nas.path,size,style,clone,flexcache_endpoint_type")

                # Retrieve volume export path; handle case where volume is not exported
                if hasattr(volume, "nas"):
                    volumeExportPath = volume.nas.path
                else:
                    volumeExportPath = None

                # Include all vols except for SVM root vol
                if volumeExportPath != "/":
                    # Construct NFS mount target
                    if not volumeExportPath :
                        nfsMountTarget = None
                    else :
                        nfsMountTarget = config["dataLif"]+":"+volume.nas.path

                    # Construct clone source
                    clone = "no"
                    cloneParentVolume = ""
                    cloneParentSnapshot = ""
                    try:
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
                    prettySize = float(volume.size) / 1024
                    if prettySize >= 1024:
                        prettySize = float(prettySize) / 1024
                        if prettySize >= 1024:
                            prettySize = float(prettySize) / 1024
                            if prettySize >= 1024:
                                prettySize = float(prettySize) / 1024
                                prettySize = str(prettySize) + "TB"
                            else:
                                prettySize = str(prettySize) + "GB"
                        else:
                            prettySize = str(prettySize) + "MB"
                    else:
                        prettySize = str(prettySize) + "KB"

                    # Construct dict containing volume details; optionally include local mountpoint
                    volumeDict = {
                        "Volume Name": volume.name,
                        "Size": prettySize,
                        "Type": volume.style,
                        "NFS Mount Target": nfsMountTarget
                    }
                    if checkLocalMounts:
                        localMountpoint = ""
                        for mount in mounts.split("\n") :
                            mountDetails = mount.split(" ")
                            if mountDetails[0] == nfsMountTarget :
                                localMountpoint = mountDetails[2]
                        volumeDict["Local Mountpoint"] = localMountpoint
                    volumeDict["FlexCache"] = flexcache
                    volumeDict["Clone"] = clone
                    volumeDict["Source Volume"] = cloneParentVolume
                    volumeDict["Source Snapshot"] = cloneParentSnapshot

                    # Append dict to list of volumes
                    volumesList.append(volumeDict)

        except NetAppRestError as err:
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Print list of volumes
        if printOutput:
            # Convert volumes array to Pandas DataFrame
            volumesDF = pd.DataFrame.from_dict(volumesList, dtype="string")
            print(tabulate(volumesDF, showindex=False, headers=volumesDF.columns))

        return volumesList

    else:
        raise ConnectionTypeError()


def mountVolume(volumeName: str, mountpoint: str, printOutput: bool = False):
    # Confirm that mountpoint value was passed in
    if not mountpoint:
        if printOutput:
            print("Error: No mountpoint specified.")
        raise MountOperationError("No mountpoint")

    # Confirm that volume name value was passed in
    if not volumeName:
        if printOutput:
            print("Error: No volume name specified.")
        raise InvalidVolumeParameterError("name")

    nfsMountTarget = None

    # Retrieve list of volumes
    try:
        volumes = listVolumes(checkLocalMounts=True)
    except (InvalidConfigError, APIConnectionError):
        if printOutput:
            print("Error: Error retrieving NFS mount target for volume.")
        raise

    # Retrieve NFS mount target for volume, and check that no volume is currently mounted at specified mountpoint
    for volume in volumes:
        # Check mountpoint
        if mountpoint == volume["Local Mountpoint"]:
            if printOutput:
                print("Error: Volume '" + volume["Volume Name"] + "' is already mounted at '" + mountpoint + "'.")
            raise MountOperationError("Another volume mounted at mountpoint")

        if volumeName == volume["Volume Name"]:
            # Retrieve NFS mount target
            nfsMountTarget = volume["NFS Mount Target"]

    # Raise error if invalid volume name was entered
    if not nfsMountTarget:
        if printOutput:
            print("Error: Invalid volume name specified.")
        raise InvalidVolumeParameterError("name")

    # Print message describing action to be understaken
    if printOutput:
        print("Mounting volume '" + volumeName + "' at '" + mountpoint + "'.")

    # Create mountpoint if it doesn't already exist
    mountpoint = os.path.expanduser(mountpoint)
    try:
        os.mkdir(mountpoint)
    except FileExistsError:
        pass

    # Mount volume
    try:
        subprocess.check_call(['mount', nfsMountTarget, mountpoint])
        if printOutput:
            print("Volume mounted successfully.")
    except subprocess.CalledProcessError as err:
        if printOutput:
            print("Error: Error running mount command: ", err)
        raise MountOperationError(err)


def prepopulateFlexCache(volumeName: str, paths: list, printOutput: bool = False):
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve svm from config file
        try:
            svm = config["svm"]
        except:
            if printOutput:
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput:
            print("FlexCache '" + volumeName + "' - Prepopulating paths: ", paths)

        try:
            # Retrieve FlexCache
            flexcache = NetAppFlexCache.find(name=volumeName, svm=svm)
            if not flexcache:
                if printOutput:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Prepopulate FlexCache
            flexcache.prepopulate = {"dir_paths": paths}
            flexcache.patch()

            if printOutput:
                print("FlexCache prepopulated successfully.")

        except NetAppRestError as err:
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def pullBucketFromS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "", printOutput: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError:
        raise

    # Add slash to end of local directory path if not present
    if not localDirectory.endswith(os.sep):
        localDirectory += os.sep

    # Multithread the download operation
    with ThreadPoolExecutor() as executor:
        try:
            # Instantiate S3 session
            s3 = instantiateS3Session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, printOutput=printOutput)

            # Loop through all objects with prefix in bucket and download
            bucket = s3.Bucket(s3Bucket)
            for obj in bucket.objects.filter(Prefix=s3ObjectKeyPrefix):
                executor.submit(downloadFromS3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, s3ObjectKey=obj.key, localFile=localDirectory+obj.key, printOutput=printOutput)

        except APIConnectionError:
            raise

        except Exception as err:
            if printOutput:
                print("Error: S3 API error: ", err)
            raise APIConnectionError(err)

    print("Download complete.")


def pullObjectFromS3(s3Bucket: str, s3ObjectKey: str, localFile: str = None, printOutput: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError:
        raise

    # Set S3 object key
    if not localFile:
        localFile = s3ObjectKey

    # Upload file
    try:
        downloadFromS3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, s3ObjectKey=s3ObjectKey, localFile=localFile, printOutput=printOutput)
    except APIConnectionError:
        raise

    print("Download complete.")


def pushDirectoryToS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "",
                      s3ExtraArgs: str = None, printOutput: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError:
        raise

    # Multithread the upload operation
    with ThreadPoolExecutor() as executor:
        # Loop through all files in directory
        for dirpath, dirnames, filenames in os.walk(localDirectory):
            # Exclude hidden files and directories
            filenames = [filename for filename in filenames if not filename[0] == '.']
            dirnames[:] = [dirname for dirname in dirnames if not dirname[0] == '.']

            for filename in filenames:
                # Build filepath
                if localDirectory.endswith(os.sep):
                    dirpathBeginIndex = len(localDirectory)
                else:
                    dirpathBeginIndex = len(localDirectory) + 1

                subdirpath = dirpath[dirpathBeginIndex:]

                if subdirpath:
                    filepath = subdirpath + os.sep + filename
                else:
                    filepath = filename

                # Set S3 object details
                s3ObjectKey = s3ObjectKeyPrefix + filepath
                localFile = dirpath + os.sep + filename

                # Upload file
                try:
                    executor.submit(uploadToS3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, localFile=localFile, s3ObjectKey=s3ObjectKey, s3ExtraArgs=s3ExtraArgs, printOutput=printOutput)
                except APIConnectionError:
                    raise

    print("Upload complete.")


def pushFileToS3(s3Bucket: str, localFile: str, s3ObjectKey: str = None, s3ExtraArgs: str = None, printOutput: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError:
        raise

    # Set S3 object key
    if not s3ObjectKey:
        s3ObjectKey = localFile

    # Upload file
    try:
        uploadToS3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, localFile=localFile, s3ObjectKey=s3ObjectKey, s3ExtraArgs=s3ExtraArgs, printOutput=printOutput)
    except APIConnectionError:
        raise

    print("Upload complete.")


def restoreSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False):
    # Retrieve config details from config file
    try:
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP":
        # Instantiate connection to ONTAP cluster
        try:
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError:
            raise

        # Retrieve svm from config file
        try:
            svm = config["svm"]
        except:
            if printOutput:
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput:
            print("Restoring snapshot '" + snapshotName + "'.")

        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume:
                if printOutput:
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Retrieve snapshot
            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshotName)
            if not snapshot:
                if printOutput:
                    print("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            # Restore snapshot
            volume.patch(volume.uuid, **{"restore_to.snapshot.name": snapshot.name, "restore_to.snapshot.uuid": snapshot.uuid}, poll=True)
            if printOutput:
                print("Snapshot restored successfully.")

        except NetAppRestError as err:
            if printOutput:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()
