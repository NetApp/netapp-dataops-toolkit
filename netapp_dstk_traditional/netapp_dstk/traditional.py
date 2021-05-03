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
from datetime import datetime

from netapp_ontap import config as netappConfig
from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Snapshot as NetAppSnapshot
from netapp_ontap.resources import Volume as NetAppVolume
import pandas as pd


__version__ = "0.0.1a1"

#
# The following attributes are unique to the traditional package.
#

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


