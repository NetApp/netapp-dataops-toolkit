#!/usr/bin/env python3

## NetApp Data Science Toolkit
version = "1.2"


import base64, json, os, subprocess, re, requests, yaml, time, boto3, boto3.session
from getpass import getpass
import pandas as pd
from tabulate import tabulate
from datetime import datetime
from netapp_ontap.resources import Volume as NetAppVolume
from netapp_ontap.resources import Snapshot as NetAppSnapshot
from netapp_ontap.resources import SnapmirrorRelationship as NetAppSnapmirrorRelationship
from netapp_ontap.resources import SnapmirrorTransfer as NetAppSnapmirrorTransfer
from netapp_ontap.resources import Flexcache as NetAppFlexCache
from netapp_ontap.error import NetAppRestError
from netapp_ontap import config as netappConfig
from netapp_ontap.host_connection import HostConnection as NetAppHostConnection
from concurrent.futures import ThreadPoolExecutor


## API connection error class; objects of this class will be raised when an API connection cannot be established
class APIConnectionError(Exception) :
    '''Error that will be raised when an API connection cannot be established'''
    pass


## Connection type error class; objects of this class will be raised when an invalid connection type is given
class ConnectionTypeError(Exception) :
    '''Error that will be raised when an invalid connection type is given'''
    pass


## Invalid config error class; objects of this class will be raised when the config file is invalid or missing
class InvalidConfigError(Exception) :
    '''Error that will be raised when the config file is invalid or missing'''
    pass


## Invalid snapshot parameter error class; objects of this class will be raised when an invalid snapshot parameter is given
class InvalidSnapshotParameterError(Exception) :
    '''Error that will be raised when an invalid snapshot parameter is given'''
    pass


## Invalid volume parameter error class; objects of this class will be raised when an invalid volume parameter is given
class InvalidVolumeParameterError(Exception) :
    '''Error that will be raised when an invalid volume parameter is given'''
    pass


## Mount operation error class; objects of this class will be raised when a mount operation fails
class MountOperationError(Exception) :
    '''Error that will be raised when a mount operation fails'''
    pass


## Cloud Sync sync operation error class; objects of this class will be raised when a Cloud Sync sync operation fails
class CloudSyncSyncOperationError(Exception) :
    '''Error that will be raised when a Cloud Sync sync operation fails'''
    pass


## Invalid SnapMirror parameter error class; objects of this class will be raised when an invalid SnapMirror parameter is given
class InvalidSnapMirrorParameterError(Exception) :
    '''Error that will be raised when an invalid SnapMirror parameter is given'''
    pass


## SnapMirror sync operation error class; objects of this class will be raised when a SnapMirror sync operation fails
class SnapMirrorSyncOperationError(Exception) :
    '''Error that will be raised when a SnapMirror sync operation fails'''
    pass


## Generic function for printing an API response
def printAPIResponse(response: requests.Response) :
    print("API Response:")
    print("Status Code: ", response.status_code)
    print("Header: ", response.headers)
    if response.text :
        print("Body: ", response.text)


## Function for creating config file
def createConfig(configDirPath: str = "~/.ntap_dsutil", configFilename: str = "config.json", connectionType: str = "ONTAP") :
    # Check to see if user has an existing config file
    configDirPath = os.path.expanduser(configDirPath)
    configFilePath = os.path.join(configDirPath, configFilename)
    if os.path.isfile(configFilePath) :
        print("You already have an existing config file. Creating a new config file will overwrite this existing config.")
        # If existing config file is present, ask user if they want to proceed
        # Verify value entered; prompt user to re-enter if invalid
        while True :
            proceed = input("Are you sure that you want to proceed? (yes/no): ")
            if proceed in ("yes", "Yes", "YES") :
                break
            elif proceed in ("no", "No", "NO") :
                sys.exit(0)
            else :
                print("Invalid value. Must enter 'yes' or 'no'.")
        
    # Instantiate dict for storing connection details
    config = dict()

    if connectionType == "ONTAP" :
        config["connectionType"] = connectionType

        # Prompt user to enter config details
        config["hostname"] = input("Enter ONTAP management interface or IP address (Note: Can be cluster or SVM management interface): ")
        config["svm"] = input("Enter SVM (Storage VM) name: ")
        config["dataLif"] = input("Enter SVM NFS data LIF hostname or IP address: ")

        # Prompt user to enter default volume type
        # Verify value entered; promopt user to re-enter if invalid
        while True :
            config["defaultVolumeType"] = input("Enter default volume type to use when creating new volumes (flexgroup/flexvol) [flexgroup]: ")
            if not config["defaultVolumeType"] :
                config["defaultVolumeType"] = "flexgroup"
                break
            elif config["defaultVolumeType"] in ("flexgroup", "FlexGroup") :
                config["defaultVolumeType"] = "flexgroup"
                break
            elif config["defaultVolumeType"] in ("flexvol", "FlexVol") :
                config["defaultVolumeType"] = "flexvol"
                break
            else :
                print("Invalid value. Must enter 'flexgroup' or 'flexvol'.")

        # prompt user to enter default export policy
        config["defaultExportPolicy"] = input("Enter export policy to use by default when creating new volumes [default]: ")
        if not config["defaultExportPolicy"] :
            config["defaultExportPolicy"] = "default"

        # prompt user to enter default snapshot policy
        config["defaultSnapshotPolicy"] = input("Enter snapshot policy to use by default when creating new volumes [none]: ")
        if not config["defaultSnapshotPolicy"] :
            config["defaultSnapshotPolicy"] = "none"

        # Prompt user to enter default uid, gid, and unix permissions
        # Verify values entered; promopt user to re-enter if invalid
        while True :
            config["defaultUnixUID"] = input("Enter unix filesystem user id (uid) to apply by default when creating new volumes (ex. '0' for root user) [0]: ")
            if not config["defaultUnixUID"] :
                config["defaultUnixUID"] = "0"
                break
            try :
                int(config["defaultUnixUID"])
                break
            except :
                print("Invalid value. Must enter an integer.")
        while True :
            config["defaultUnixGID"] = input("Enter unix filesystem group id (gid) to apply by default when creating new volumes (ex. '0' for root group) [0]: ")
            if not config["defaultUnixGID"] :
                config["defaultUnixGID"] = "0"
                break
            try :
                int(config["defaultUnixGID"])
                break
            except :
                print("Invalid value. Must enter an integer.")
        while True :
            config["defaultUnixPermissions"] = input("Enter unix filesystem permissions to apply by default when creating new volumes (ex. '0777' for full read/write permissions for all users and groups) [0777]: ")
            if not config["defaultUnixPermissions"] :
                config["defaultUnixPermissions"] = "0777"
                break
            elif not re.search("^0[0-7]{3}", config["defaultUnixPermissions"]) :
                print("Invalud value. Must enter a valid unix permissions value. Acceptable values are '0777', '0755', '0744', etc.")
            else :
                break

        # Prompt user to enter additional config details
        config["defaultAggregate"] = input("Enter aggregate to use by default when creating new FlexVol volumes: ")
        config["username"] = input("Enter ONTAP API username (Note: Can be cluster or SVM admin account): ")
        passwordString = getpass("Enter ONTAP API password (Note: Can be cluster or SVM admin account): ")

        # Convert password to base64 enconding
        passwordBytes = passwordString.encode("ascii") 
        passwordBase64Bytes = base64.b64encode(passwordBytes)
        config["password"] = passwordBase64Bytes.decode("ascii")

        # Prompt user to enter value denoting whether or not to verify SSL cert when calling ONTAP API
        # Verify value entered; prompt user to re-enter if invalid
        while True :
            verifySSLCert = input("Verify SSL certificate when calling ONTAP API (true/false): ")
            if verifySSLCert in ("true", "True") :
                config["verifySSLCert"] = True
                break
            elif verifySSLCert in ("false", "False") :
                config["verifySSLCert"] = False
                break
            else :
                print("Invalid value. Must enter 'true' or 'false'.")

    else :
        raise ConnectionTypeError()

    # Ask user if they want to use cloud sync functionality
    # Verify value entered; prompt user to re-enter if invalid
    while True :
        useCloudSync = input("Do you intend to use this toolkit to trigger Cloud Sync operations? (yes/no): ")

        if useCloudSync in ("yes", "Yes", "YES") :
            # Prompt user to enter cloud central refresh token
            print("Note: If you do not have a Cloud Central refresh token, visit https://services.cloud.netapp.com/refresh-token to create one.")
            refreshTokenString = getpass("Enter Cloud Central refresh token: ")

            # Convert refresh token to base64 enconding
            refreshTokenBytes = refreshTokenString.encode("ascii") 
            refreshTokenBase64Bytes = base64.b64encode(refreshTokenBytes)
            config["cloudCentralRefreshToken"] = refreshTokenBase64Bytes.decode("ascii")

            break

        elif useCloudSync in ("no", "No", "NO") :
            break

        else :
            print("Invalid value. Must enter 'yes' or 'no'.")

    # Ask user if they want to use S3 functionality
    # Verify value entered; prompt user to re-enter if invalid
    while True :
        useS3 = input("Do you intend to use this toolkit to push/pull from S3? (yes/no): ")

        if useS3 in ("yes", "Yes", "YES") :
            # Promt user to enter S3 endpoint details
            config["s3Endpoint"] = input("Enter S3 endpoint: ")

            # Prompt user to enter S3 credentials
            config["s3AccessKeyId"] = input("Enter S3 Access Key ID: ")
            s3SecretAccessKeyString = getpass("Enter S3 Secret Access Key: ")

            # Convert refresh token to base64 enconding
            s3SecretAccessKeyBytes = s3SecretAccessKeyString.encode("ascii") 
            s3SecretAccessKeyBase64Bytes = base64.b64encode(s3SecretAccessKeyBytes)
            config["s3SecretAccessKey"] = s3SecretAccessKeyBase64Bytes.decode("ascii")

            # Prompt user to enter value denoting whether or not to verify SSL cert when calling S3 API
            # Verify value entered; prompt user to re-enter if invalid
            while True :
                s3VerifySSLCert = input("Verify SSL certificate when calling S3 API (true/false): ")
                if s3VerifySSLCert in ("true", "True") :
                    config["s3VerifySSLCert"] = True
                    config["s3CACertBundle"] = input("Enter CA cert bundle to use when calling S3 API (optional) []: ")
                    break
                elif s3VerifySSLCert in ("false", "False") :
                    config["s3VerifySSLCert"] = False
                    config["s3CACertBundle"] = ""
                    break
                else :
                    print("Invalid value. Must enter 'true' or 'false'.")

            break

        elif useS3 in ("no", "No", "NO") :
            break

        else :
            print("Invalid value. Must enter 'yes' or 'no'.")

    # Create config dir if it doesn't already exist
    try :
        os.mkdir(configDirPath)
    except FileExistsError :
        pass
    
    # Create config file in config dir
    with open(configFilePath, 'w') as configFile:
        # Write connection details to config file
        json.dump(config, configFile)

    print("Created config file: '" + configFilePath + "'.")


## Function for printing appropriate error message when config file is missing or invalid
def printInvalidConfigError() :
    print("Error: Missing or invalid config file. Run `./ntap_dsutil.py config` to create config file.")


## Function for retrieving config details from existing config file
def retrieveConfig(configDirPath: str = "~/.ntap_dsutil", configFilename: str = "config.json", printOutput: bool = False) -> dict :
    configDirPath = os.path.expanduser(configDirPath)
    configFilePath = os.path.join(configDirPath, configFilename)
    try :
        with open(configFilePath, 'r') as configFile:
            # Read connection details from config file; read into dict
            config = json.load(configFile) 
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()
    return config


# Function for retrieving Cloud Central refresh token from existing config file
def retrieveCloudCentralRefreshToken(printOutput: bool = False) -> str :
    # Retrieve refresh token from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        refreshTokenBase64 = config["cloudCentralRefreshToken"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Decode base64-encoded refresh token
    refreshTokenBase64Bytes = refreshTokenBase64.encode("ascii")
    refreshTokenBytes = base64.b64decode(refreshTokenBase64Bytes)
    refreshToken = refreshTokenBytes.decode("ascii")

    return refreshToken


# Function for retrieving S3 access details from existing config file
def retrieveS3AccessDetails(printOutput: bool = False) -> (str, str, str, bool, str) :
    # Retrieve refresh token from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        s3Endpoint = config["s3Endpoint"]
        s3AccessKeyId = config["s3AccessKeyId"]
        s3SecretAccessKeyBase64 = config["s3SecretAccessKey"]
        s3VerifySSLCert = config["s3VerifySSLCert"]
        s3CACertBundle = config["s3CACertBundle"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Decode base64-encoded refresh token
    s3SecretAccessKeyBase64Bytes = s3SecretAccessKeyBase64.encode("ascii")
    s3SecretAccessKeyBytes = base64.b64decode(s3SecretAccessKeyBase64Bytes)
    s3SecretAccessKey = s3SecretAccessKeyBytes.decode("ascii")

    return s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle


## Function for obtaining access token for calling Cloud Central API
def getCloudCentralAccessToken(refreshToken: str, printOutput: bool = False) -> str :
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
    try :
        responseBody = json.loads(response.text)
        accessToken = responseBody["access_token"]
    except :
        errorMessage = "Error obtaining access token from Cloud Sync API"
        if printOutput :
            print("Error:", errorMessage)
            printAPIResponse(response)
        raise APIConnectionError(errorMessage, response)

    return accessToken


##  Function for instantiating an S3 session
def instantiateS3Session(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str, printOutput: bool = False) :
    # Instantiate session
    session = boto3.session.Session(aws_access_key_id=s3AccessKeyId, aws_secret_access_key=s3SecretAccessKey)

    if s3VerifySSLCert :
        if s3CACertBundle :
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=s3CACertBundle)
        else :
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint)
    else :
        s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=False)

    return s3


## Function for instantiating connection to NetApp storage instance
def instantiateConnection(config: dict, connectionType: str = "ONTAP", printOutput: bool = False) :
    if connectionType == "ONTAP" :
        ## Connection details for ONTAP cluster
        try :
            ontapClusterMgmtHostname = config["hostname"]
            ontapClusterAdminUsername = config["username"]
            ontapClusterAdminPasswordBase64 = config["password"]
            verifySSLCert = config["verifySSLCert"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        # Decode base64-encoded password
        ontapClusterAdminPasswordBase64Bytes = ontapClusterAdminPasswordBase64.encode("ascii")
        ontapClusterAdminPasswordBytes = base64.b64decode(ontapClusterAdminPasswordBase64Bytes)
        ontapClusterAdminPassword = ontapClusterAdminPasswordBytes.decode("ascii")

        # Instantiate connection to ONTAP cluster
        netappConfig.CONNECTION = NetAppHostConnection(
            host = ontapClusterMgmtHostname,
            username = ontapClusterAdminUsername,
            password = ontapClusterAdminPassword,
            verify = verifySSLCert
        )
        
    else :
        raise ConnectionTypeError()


## Function for listing all volumes
def listVolumes(checkLocalMounts: bool = False, printOutput: bool = False) -> list() :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        try :
            # Retrieve all volumes for SVM
            volumes = NetAppVolume.get_collection(svm=config["svm"])

            # Retrieve local mounts if desired
            if checkLocalMounts :
                mounts = subprocess.check_output(['mount']).decode()

            # Construct list of volumes; do not include SVM root volume
            volumesList = list()
            for volume in volumes :
                volume.get(fields="nas.path,size,style,clone,flexcache_endpoint_type")
                
                # Retrieve volume export path; handle case where volume is not exported
                if hasattr(volume, "nas") :
                    volumeExportPath = volume.nas.path
                else :
                    volumeExportPath = None
                
                # Include all vols except for SVM root vol
                if volumeExportPath != "/" :
                    # Construct NFS mount target
                    if not volumeExportPath :
                        nfsMountTarget = None
                    else :
                        nfsMountTarget = config["dataLif"]+":"+volume.nas.path

                    # Construct clone source
                    clone = "no"
                    cloneParentVolume = ""
                    cloneParentSnapshot = ""
                    try :
                        cloneParentVolume = volume.clone.parent_volume.name
                        cloneParentSnapshot = volume.clone.parent_snapshot.name
                        clone = "yes"
                    except :
                        pass

                    # Determine if FlexCache
                    if volume.flexcache_endpoint_type == "cache" :
                        flexcache = "yes"
                    else :
                        flexcache = "no"

                    # Convert size in bytes to "pretty" size (size in KB, MB, GB, or TB)
                    prettySize = float(volume.size) / 1024
                    if prettySize >= 1024 :
                        prettySize = float(prettySize) / 1024
                        if prettySize >= 1024 :
                            prettySize = float(prettySize) / 1024
                            if prettySize >= 1024 :
                                prettySize = float(prettySize) / 1024
                                prettySize = str(prettySize) + "TB"
                            else :
                                prettySize = str(prettySize) + "GB"
                        else :
                            prettySize = str(prettySize) + "MB"
                    else :
                        prettySize = str(prettySize) + "KB"

                    # Construct dict containing volume details; optionally include local mountpoint
                    volumeDict = {
                        "Volume Name": volume.name, 
                        "Size": prettySize, 
                        "Type": volume.style,
                        "NFS Mount Target": nfsMountTarget
                    }
                    if checkLocalMounts :
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

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)
        
        # Print list of volumes
        if printOutput :
            # Convert volumes array to Pandas DataFrame
            volumesDF = pd.DataFrame.from_dict(volumesList, dtype="string")
            print(tabulate(volumesDF, showindex=False, headers=volumesDF.columns))

        return volumesList

    else :
        raise ConnectionTypeError()


## Function for mounting an existing volume
def mountVolume(volumeName: str, mountpoint: str, printOutput: bool = False) :
    # Confirm that mountpoint value was passed in
    if not mountpoint :
        if printOutput :
            print("Error: No mountpoint specified.")
        raise MountOperationError("No mountpoint")

    # Confirm that volume name value was passed in
    if not volumeName :
        if printOutput :
            print("Error: No volume name specified.")
        raise InvalidVolumeParameterError("name")

    nfsMountTarget = None

    # Retrieve list of volumes
    try :
        volumes = listVolumes(checkLocalMounts=True)
    except (InvalidConfigError, APIConnectionError) :
        if printOutput :
            print("Error: Error retrieving NFS mount target for volume.")
        raise

    # Retrieve NFS mount target for volume, and check that no volume is currently mounted at specified mountpoint
    for volume in volumes :
        # Check mountpoint
        if mountpoint == volume["Local Mountpoint"] :
            if printOutput :
                print("Error: Volume '" + volume["Volume Name"] + "' is already mounted at '" + mountpoint + "'.")
            raise MountOperationError("Another volume mounted at mountpoint")

        if volumeName == volume["Volume Name"] :
            # Retrieve NFS mount target
            nfsMountTarget = volume["NFS Mount Target"]

    # Raise error if invalid volume name was entered
    if not nfsMountTarget :
        if printOutput :
            print("Error: Invalid volume name specified.")
        raise InvalidVolumeParameterError("name")

    # Print message describing action to be understaken
    if printOutput :
        print("Mounting volume '" + volumeName + "' at '" + mountpoint + "'.")

    # Create mountpoint if it doesn't already exist
    mountpoint = os.path.expanduser(mountpoint)
    try :
        os.mkdir(mountpoint)
    except FileExistsError :
        pass

    # Mount volume
    try :
        subprocess.check_call(['mount', nfsMountTarget, mountpoint])
        if printOutput :
            print("Volume mounted successfully.")
    except subprocess.CalledProcessError as err :
        if printOutput :
            print("Error: Error running mount command: ", err)
        raise MountOperationError(err)


## Function for creating a new volume
def createVolume(volumeName: str, volumeSize: str, guaranteeSpace: bool = False, volumeType: str = "flexvol", unixPermissions: str = "0777", unixUID: str = "0", unixGID: str = "0", exportPolicy: str = "default", snapshotPolicy: str = "none", aggregate: str = None, mountpoint: str = None, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve values from config file if not passed into function
        try :
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
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        # Check volume type for validity
        if volumeType not in ("flexvol", "flexgroup") :
            if printOutput :
                print("Error: Invalid volume type specified. Acceptable values are 'flexvol' and 'flexgroup'.")
            raise InvalidVolumeParameterError("size")

        # Check unix permissions for validity
        if not re.search("^0[0-7]{3}", unixPermissions) :
            if printOutput :
                print("Error: Invalid unix permissions specified. Acceptable values are '0777', '0755', '0744', etc.")
            raise InvalidVolumeParameterError("unixPermissions")

        # Check unix uid for validity
        try :
            unixUID = int(unixUID)
        except :
            if printOutput :
                print("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        # Check unix gid for validity
        try :
            unixGID = int(unixGID)
        except :
            if printOutput :
                print("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        # Convert volume size to Bytes
        if re.search("^[0-9]+MB$", volumeSize) :
            # Convert from MB to Bytes
            volumeSizeBytes = int(volumeSize[:len(volumeSize)-2]) * 1024**2
        elif re.search("^[0-9]+GB$", volumeSize) :
            # Convert from GB to Bytes
            volumeSizeBytes = int(volumeSize[:len(volumeSize)-2]) * 1024**3
        elif re.search("^[0-9]+TB$", volumeSize) :
            # Convert from TB to Bytes
            volumeSizeBytes = int(volumeSize[:len(volumeSize)-2]) * 1024**4
        else :
            if printOutput :
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
        if guaranteeSpace :
            volumeDict["guarantee"] = {"type": "volume"}
        else :
            volumeDict["guarantee"] = {"type": "none"}

        # If flexvol -> set aggregate field
        if volumeType == "flexvol" :
            volumeDict["aggregates"] = [{'name': aggregate}]

        # Create volume
        if printOutput :
            print("Creating volume '" + volumeName + "'.")
        try :
            volume = NetAppVolume.from_dict(volumeDict)
            volume.post(poll=True)
            if printOutput :
                print("Volume created successfully.")
        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Optionally mount newly created volume
        if mountpoint :
            try :
                mountVolume(volumeName=volumeName, mountpoint=mountpoint, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError) :
                if printOutput :
                    print("Error: Error mounting volume.")
                raise

    else :
        raise ConnectionTypeError()


# Function for creating a snapshot
def createSnapshot(volumeName: str, snapshotName: str = None, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve svm from config file
        try :
            svm = config["svm"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        # Set snapshot name if not passed into function
        if not snapshotName :
            timestamp = datetime.today().strftime("%Y%m%d_%H%M%S")
            snapshotName = "ntap_dsutil_" + timestamp

        if printOutput :
            print("Creating snapshot '" + snapshotName + "'.")

        try :
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume :
                if printOutput :
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Create snapshot
            snapshot = NetAppSnapshot.from_dict({
                'name': snapshotName,
                'volume': volume.to_dict()
            })
            snapshot.post(poll=True)

            if printOutput :
                print("Snapshot created successfully.")

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else :
        raise ConnectionTypeError()


# Function for listing all snapshots
def listSnapshots(volumeName: str, printOutput: bool = False) -> list() :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve svm from config file
        try :
            svm = config["svm"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        # Retrieve snapshots
        try :
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume :
                if printOutput :
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Construct list of snapshots
            snapshotsList = list()
            for snapshot in NetAppSnapshot.get_collection(volume.uuid) :
                # Retrieve snapshot
                snapshot.get()

                # Construct dict of snapshot details
                snapshotDict = {"Snapshot Name": snapshot.name, "Create Time": snapshot.create_time}

                # Append dict to list of snapshots
                snapshotsList.append(snapshotDict)
            
        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Print list of snapshots
        if printOutput :
            # Convert snapshots array to Pandas DataFrame
            snapshotsDF = pd.DataFrame.from_dict(snapshotsList, dtype="string")
            print(tabulate(snapshotsDF, showindex=False, headers=snapshotsDF.columns))

        return snapshotsList

    else :
        raise ConnectionTypeError()


# Function for deleting a snapshot
def deleteSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve svm from config file
        try :
            svm = config["svm"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput :
            print("Deleting snapshot '" + snapshotName + "'.")

        try :
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume :
                if printOutput :
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Retrieve snapshot
            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshotName)
            if not snapshot :
                if printOutput :
                    print("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            # Delete snapshot
            snapshot.delete(poll=True)

            if printOutput :
                print("Snapshot deleted successfully.")

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else :
        raise ConnectionTypeError()


# Function for deleting a volume
def deleteVolume(volumeName: str, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve svm from config file
        try :
            svm = config["svm"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput :
            print("Deleting volume '" + volumeName + "'.")

        try :
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume :
                if printOutput :
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Delete volume
            volume.delete(poll=True)

            if printOutput :
                print("Volume deleted successfully.")

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else :
        raise ConnectionTypeError()


# Function for restoring a snapshot
def restoreSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve svm from config file
        try :
            svm = config["svm"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput :
            print("Restoring snapshot '" + snapshotName + "'.")

        try :
            # Retrieve volume
            volume = NetAppVolume.find(name=volumeName, svm=svm)
            if not volume :
                if printOutput :
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Retrieve snapshot
            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshotName)
            if not snapshot :
                if printOutput :
                    print("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            # Restore snapshot
            volume.patch(volume.uuid, **{"restore_to.snapshot.name": snapshot.name, "restore_to.snapshot.uuid": snapshot.uuid}, poll=True)
            if printOutput :
                print("Snapshot restored successfully.")

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else :
        raise ConnectionTypeError()


## Function for cloning a volume
def cloneVolume(newVolumeName: str, sourceVolumeName: str, sourceSnapshotName: str = None, unixUID: str = None, unixGID: str = None, mountpoint: str = None, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve values from config file if not passed into function
        try :
            svm = config["svm"]
            if not unixUID :
                unixUID = config["defaultUnixUID"]
            if not unixGID :
                unixGID = config["defaultUnixGID"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        # Check unix uid for validity
        try :
            unixUID = int(unixUID)
        except :
            if printOutput :
                print("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        # Check unix gid for validity
        try :
            unixGID = int(unixGID)
        except :
            if printOutput :
                print("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        # Create volume
        if printOutput :
            print("Creating clone volume '" + newVolumeName + "' from source volume '" + sourceVolumeName + "'.")

        try :
            # Retrieve source volume
            sourceVolume = NetAppVolume.find(name=sourceVolumeName, svm=svm)
            if not sourceVolume :
                if printOutput :
                    print("Error: Invalid source volume name.")
                raise InvalidVolumeParameterError("name")

            # Construct dict representing new volume
            newVolumeDict = {
                "name": newVolumeName,
                "svm": {"name": svm},
                "nas": {
                    "path": "/" + newVolumeName
                },
                "clone" : {
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
            if unixUID != 0 :
                newVolumeDict["nas"]["uid"] = unixUID
            else :
                if printOutput :
                    print("Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.")
            if unixGID != 0 :
                newVolumeDict["nas"]["gid"] = unixGID
            else :
                if printOutput :
                    print("Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.")

            # Add source snapshot details to volume dict if specified
            if sourceSnapshotName :
                # Retrieve source snapshot
                sourceSnapshot = NetAppSnapshot.find(sourceVolume.uuid, name=sourceSnapshotName)
                if not sourceSnapshot :
                    if printOutput :
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
            if printOutput :
                print("Clone volume created successfully.")

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        # Optionally mount newly created volume
        if mountpoint :
            try :
                mountVolume(volumeName=newVolumeName, mountpoint=mountpoint, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError) :
                if printOutput :
                    print("Error: Error mounting clone volume.")
                raise

    else :
        raise ConnectionTypeError()


## Function for obtaining access paremeters for calling Cloud Sync API
def getCloudSyncAccessParameters(refreshToken: str, printOutput: bool = False) -> (str, str) :
    try :
        accessToken = getCloudCentralAccessToken(refreshToken=refreshToken, printOutput=printOutput)
    except APIConnectionError :
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
    try :
        responseBody = json.loads(response.text)
        accountId = responseBody[0]["accountId"]
    except :
        errorMessage = "Error obtaining account ID from Cloud Sync API"
        if printOutput :
            print("Error:", errorMessage)
            printAPIResponse(response)
        raise APIConnectionError(errorMessage, response)

    # Return access token and account ID
    return accessToken, accountId


## Function for listing cloud sync relationships
def listCloudSyncRelationships(printOutput: bool = False) -> list() :
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API

    # Retrieve refresh token
    try :
        refreshToken = retrieveCloudCentralRefreshToken(printOutput=printOutput)
    except InvalidConfigError :
        raise

    # Obtain access token and account ID
    try :
        accessToken, accountId = getCloudSyncAccessParameters(refreshToken=refreshToken, printOutput=printOutput)
    except APIConnectionError :
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
    if response.status_code != 200 :
        errorMessage = "Error calling Cloud Sync API to retrieve list of relationships."
        if printOutput :
            print("Error:", errorMessage)
            printAPIResponse(response)
        raise APIConnectionError(errorMessage, response)

    # Constrict list of relationships
    relationships = json.loads(response.text)
    relationshipsList = list()
    for relationship in relationships :
        relationshipDetails = dict()
        relationshipDetails["id"] = relationship["id"]
        relationshipDetails["source"] = relationship["source"]
        relationshipDetails["target"] = relationship["target"]
        relationshipsList.append(relationshipDetails)

    # Print list of relationships
    if printOutput :
        print(yaml.dump(relationshipsList))

    return relationshipsList


## Function for triggering a sync operation for an existing cloud sync relationships
def syncCloudSyncRelationship(relationshipID: str, waitUntilComplete: bool = False, printOutput: bool = False) :
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API

    # Retrieve refresh token
    try :
        refreshToken = retrieveCloudCentralRefreshToken(printOutput=printOutput)
    except InvalidConfigError :
        raise

    # Obtain access token and account ID
    try :
        accessToken, accountId = getCloudSyncAccessParameters(refreshToken=refreshToken, printOutput=printOutput)
    except APIConnectionError :
        raise

    # Step 2: Trigger Cloud Sync sync

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/relationships/%s/sync" % (relationshipID)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    # Call API to trigger sync
    if printOutput :
        print("Triggering sync operation for Cloud Sync relationship (ID = " + relationshipID + ").")
    response = requests.put(url = url, headers = headers)

    # Check for API response status code of 202; if not 202, raise error
    if response.status_code != 202 :
        errorMessage = "Error calling Cloud Sync API to trigger sync operation."
        if printOutput :
            print("Error:", errorMessage)
            printAPIResponse(response)
        raise APIConnectionError(errorMessage, response)
    
    if printOutput :
        print("Sync operation successfully triggered.")

    # Step 3: Obtain status of the sync operation; keep checking until the sync operation has completed

    if waitUntilComplete :
        while True :
            # Define parameters for API call
            url = "https://cloudsync.netapp.com/api/relationships-v2/%s" % (relationshipID)
            headers = {
                "Accept": "application/json",
                "x-account-id": accountId,
                "Authorization": "Bearer " + accessToken
            }

            # Call API to obtain status of sync operation
            response = requests.get(url = url, headers = headers)

            # Parse response to retrieve status of sync operation
            try :
                responseBody = json.loads(response.text)
                latestActivityType = responseBody["activity"]["type"]
                latestActivityStatus = responseBody["activity"]["status"]
            except :
                errorMessage = "Error obtaining status of sync operation from Cloud Sync API."
                if printOutput :
                    print("Error:", errorMessage)
                    printAPIResponse(response)
                raise APIConnectionError(errorMessage, response)
            
            # End execution if the latest update is complete
            if latestActivityType == "Sync" :
                if latestActivityStatus == "DONE" :
                    if printOutput :
                        print("Success: Sync operation is complete.")
                    break
                elif latestActivityStatus == "FAILED" :
                    if printOutput :
                        failureMessage = responseBody["activity"]["failureMessage"]
                        print("Error: Sync operation failed.")
                        print("Message:", failureMessage)
                    raise CloudSyncSyncOperationError(latestActivityStatus, failureMessage)
                elif latestActivityStatus == "RUNNING" :
                    # Print message re: progress
                    if printOutput : 
                        print("Sync operation is not yet complete. Status:", latestActivityStatus)
                        print("Checking again in 60 seconds...")
                else :
                    if printOutput :
                        print ("Error: Unknown sync operation status (" + latestActivityStatus + ") returned by Cloud Sync API.")
                    raise CloudSyncSyncOperationError(latestActivityStatus)

            # Sleep for 60 seconds before checking progress again
            time.sleep(60)


## Function for listing all SnapMirror relationships
def listSnapMirrorRelationships(printOutput: bool = False) -> list() :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        try :
            # Retrieve all relationships for which destination is on current cluster
            destinationRelationships = NetAppSnapmirrorRelationship.get_collection()

            # Do not retrieve relationships for which source is on current cluster
            # Note: Uncomment below line to retrieve all relationships for which source is on current cluster, then add sourceRelationships to for loop
            #sourceRelationships = NetAppSnapmirrorRelationship.get_collection(list_destinations_only=True)

            # Construct list of relationships
            relationshipsList = list()
            for relationship in destinationRelationships :
                # Retrieve relationship details
                try :
                    relationship.get()
                except NetAppRestError as err :
                    relationship.get(list_destinations_only=True)

                # Set cluster value
                if hasattr(relationship.source, "cluster") :
                    sourceCluster = relationship.source.cluster.name
                else :
                    sourceCluster = "user's cluster"
                if hasattr(relationship.destination, "cluster") :
                    destinationCluster = relationship.destination.cluster.name
                else :
                    destinationCluster = "user's cluster"

                # Set transfer state value
                if hasattr(relationship, "transfer") :
                    transferState = relationship.transfer.state
                else :
                    transferState = None

                # Set healthy value
                if hasattr(relationship, "healthy") :
                    healthy = relationship.healthy
                else :
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

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)
        
        # Print list of relationships
        if printOutput :
            # Convert relationships array to Pandas DataFrame
            relationshipsDF = pd.DataFrame.from_dict(relationshipsList, dtype="string")
            print(tabulate(relationshipsDF, showindex=False, headers=relationshipsDF.columns))

        return relationshipsList

    else :
        raise ConnectionTypeError()


## Function for triggering a sync operation for a SnapMirror relationship
def syncSnapMirrorRelationship(uuid: str, waitUntilComplete: bool = False, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise
    
        if printOutput :
            print("Triggering sync operation for SnapMirror relationship (UUID = " + uuid + ").")

        try :
            # Trigger sync operation for SnapMirror relationship
            transfer = NetAppSnapmirrorTransfer(uuid)
            transfer.post(poll=True)
        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        if printOutput :
            print("Sync operation successfully triggered.")

        if waitUntilComplete :
            # Wait to perform initial check
            print("Waiting for sync operation to complete.")
            print("Status check will be performed in 10 seconds...")
            time.sleep(10)

            while True :
                # Retrieve relationship
                relationship = NetAppSnapmirrorRelationship.find(uuid=uuid)
                relationship.get()

                # Check status of sync operation
                if hasattr(relationship, "transfer") :
                    transferState = relationship.transfer.state
                else :
                    transferState = None

                # if transfer is complete, end execution
                if not transferState :
                    healthy = relationship.healthy
                    if healthy :
                        if printOutput :
                            print("Success: Sync operation is complete.")
                        break
                    else :
                        if printOutput :
                            print("Error: Relationship is not healthy. Access ONTAP System Manager for details.")
                        raise SnapMirrorSyncOperationError("not healthy")
                elif transferState != "transferring" :
                    if printOutput :
                        print ("Error: Unknown sync operation status (" + transferState + ") returned by ONTAP API.")
                    raise SnapMirrorSyncOperationError(transferState)
                else :
                    # Print message re: progress
                    if printOutput : 
                        print("Sync operation is not yet complete. Status:", transferState)
                        print("Checking again in 60 seconds...")

                # Sleep for 60 seconds before checking progress again
                time.sleep(60)

    else :
        raise ConnectionTypeError()


# Function for prepopulating a FlexCache
def prepopulateFlexCache(volumeName: str, paths: list, printOutput: bool = False) :
    # Retrieve config details from config file
    try :
        config = retrieveConfig(printOutput=printOutput)
    except InvalidConfigError :
        raise
    try :
        connectionType = config["connectionType"]
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    if connectionType == "ONTAP" :
        # Instantiate connection to ONTAP cluster
        try :
            instantiateConnection(config=config, connectionType=connectionType, printOutput=printOutput)
        except InvalidConfigError :
            raise

        # Retrieve svm from config file
        try :
            svm = config["svm"]
        except :
            if printOutput :
                printInvalidConfigError()
            raise InvalidConfigError()

        if printOutput :
            print("FlexCache '" + volumeName + "' - Prepopulating paths: ", paths)

        try :
            # Retrieve FlexCache
            flexcache = NetAppFlexCache.find(name=volumeName, svm=svm)
            if not flexcache :
                if printOutput :
                    print("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            # Prepopulate FlexCache
            flexcache.prepopulate = {"dir_paths": paths}
            flexcache.patch()

            if printOutput :
                print("FlexCache prepopulated successfully.")

        except NetAppRestError as err :
            if printOutput :
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

    else :
        raise ConnectionTypeError()


## Function for uploading a file to S3
def uploadToS3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str, s3Bucket: str, localFile: str, s3ObjectKey: str, s3ExtraArgs: str = None, printOutput: bool = False) :
    # Instantiate S3 session
    try :
        s3 = instantiateS3Session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, printOutput=printOutput)
    except Exception as err :
        if printOutput :
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)

    # Upload file
    if printOutput :
        print("Uploading file '" + localFile + "' to bucket '" + s3Bucket + "' and applying key '" + s3ObjectKey + "'.")
    
    try :
        if s3ExtraArgs :
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile, ExtraArgs=json.loads(s3ExtraArgs))
        else :
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile)
    except Exception as err :
        if printOutput :
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)


## Function for downloading a file from S3
def downloadFromS3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str, s3Bucket: str, s3ObjectKey: str, localFile: str, printOutput: bool = False) :
    # Instantiate S3 session
    try :
        s3 = instantiateS3Session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, printOutput=printOutput)
    except Exception as err :
        if printOutput :
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)

    if printOutput :
        print("Downloading object '" + s3ObjectKey + "' from bucket '" + s3Bucket + "' and saving as '" + localFile + "'.")

    # Create directories that don't exist
    if localFile.find(os.sep) != -1 :
        dirs = localFile.split(os.sep)
        dirpath = os.sep.join(dirs[:len(dirs)-1])
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
    
    # Download the file
    try :
        s3.Object(s3Bucket, s3ObjectKey).download_file(localFile)
    except Exception as err :
        if printOutput :
            print("Error: S3 API error: ", err)
        raise APIConnectionError(err)


##  Function for pushing a file to S3
def pushFileToS3(s3Bucket: str, localFile: str, s3ObjectKey: str = None, s3ExtraArgs: str = None, printOutput: bool = False) :
    # Retrieve S3 access details from existing config file
    try :
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError :
        raise
    
    # Set S3 object key
    if not s3ObjectKey :
        s3ObjectKey = localFile

    # Upload file
    try :
        uploadToS3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, localFile=localFile, s3ObjectKey=s3ObjectKey, s3ExtraArgs=s3ExtraArgs, printOutput=printOutput)
    except APIConnectionError :
        raise

    print("Upload complete.")


##  Function for pushing a directory to S3
def pushDirectoryToS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "", s3ExtraArgs: str = None, printOutput: bool = False) :
    # Retrieve S3 access details from existing config file
    try :
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError :
        raise
    
    # Multithread the upload operation
    with ThreadPoolExecutor() as executor :
        # Loop through all files in directory
        for dirpath, dirnames, filenames in os.walk(localDirectory) :
            # Exclude hidden files and directories
            filenames = [filename for filename in filenames if not filename[0] == '.']
            dirnames[:] = [dirname for dirname in dirnames if not dirname[0] == '.']

            for filename in filenames:
                # Build filepath
                if localDirectory.endswith(os.sep) :
                    dirpathBeginIndex = len(localDirectory)
                else :
                    dirpathBeginIndex = len(localDirectory) + 1

                subdirpath = dirpath[dirpathBeginIndex:] 

                if subdirpath :
                    filepath = subdirpath + os.sep + filename
                else :
                    filepath = filename

                # Set S3 object details
                s3ObjectKey = s3ObjectKeyPrefix + filepath
                localFile = dirpath + os.sep + filename

                # Upload file
                try :
                    executor.submit(uploadToS3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, localFile=localFile, s3ObjectKey=s3ObjectKey, s3ExtraArgs=s3ExtraArgs, printOutput=printOutput)
                except APIConnectionError :
                    raise
    
    print("Upload complete.")


##  Function for pull an object from S3
def pullObjectFromS3(s3Bucket: str, s3ObjectKey: str, localFile: str = None, printOutput: bool = False) :
    # Retrieve S3 access details from existing config file
    try :
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError :
        raise
    
    # Set S3 object key
    if not localFile :
        localFile = s3ObjectKey

    # Upload file
    try :
        downloadFromS3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, s3ObjectKey=s3ObjectKey, localFile=localFile, printOutput=printOutput)
    except APIConnectionError :
        raise

    print("Download complete.")


##  Function for pushing a directory to S3
def pullBucketFromS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "", printOutput: bool = False) :
    # Retrieve S3 access details from existing config file
    try :
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = retrieveS3AccessDetails(printOutput=printOutput)
    except InvalidConfigError :
        raise

    # Add slash to end of local directory path if not present
    if not localDirectory.endswith(os.sep) :
        localDirectory+=os.sep
    
    # Multithread the download operation
    with ThreadPoolExecutor() as executor :
        try :
            # Instantiate S3 session
            s3 = instantiateS3Session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, printOutput=printOutput)
        
            # Loop through all objects with prefix in bucket and download
            bucket = s3.Bucket(s3Bucket)
            for obj in bucket.objects.filter(Prefix=s3ObjectKeyPrefix) :
                executor.submit(downloadFromS3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3Bucket, s3ObjectKey=obj.key, localFile=localDirectory+obj.key, printOutput=printOutput)

        except APIConnectionError :
            raise

        except Exception as err :
            if printOutput :
                print("Error: S3 API error: ", err)
            raise APIConnectionError(err)
    
    print("Download complete.")


## Define contents of help text
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
helpTextCloneVolume = '''
Command: clone volume

Create a new data volume that is an exact copy of an existing volume.

Required Options/Arguments:
\t-n, --name=\t\tName of new volume..
\t-v, --source-volume=\tName of volume to be cloned.

Optional Options/Arguments:
\t-g, --gid=\t\tUnix filesystem group id (gid) to apply when creating new volume (if not specified, gid of source volume will be retained) (Note: cannot apply gid of '0' when creating clone).
\t-h, --help\t\tPrint help text.
\t-m, --mountpoint=\tLocal mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
\t-s, --source-snapshot=\tName of the snapshot to be cloned (if specified, the clone will be created from a specific snapshot on the source volume as opposed to the current state of the volume).
\t-u, --uid=\t\tUnix filesystem user id (uid) to apply when creating new volume (if not specified, uid of source volume will be retained) (Note: cannot apply uid of '0' when creating clone).

Examples (basic usage):
\t./ntap_dsutil.py clone volume --name=project1 --source-volume=gold_dataset
\t./ntap_dsutil.py clone volume -n project2 -v gold_dataset -s snap1
\tsudo -E ./ntap_dsutil.py clone volume --name=project1 --source-volume=gold_dataset --mountpoint=~/project1

Examples (advanced usage):
\t./ntap_dsutil.py clone volume -n testvol -v gold_dataset -u 1000 -g 1000
'''
helpTextConfig = '''
Command: config

Create a new config file (a config file is required to perform other commands).

No additional options/arguments required.
'''
helpTextCreateSnapshot = '''
Command: create snapshot

Create a new snapshot for a data volume.

Required Options/Arguments:
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-h, --help\tPrint help text.
\t-n, --name=\tName of new snapshot. If not specified, will be set to 'ntap_dsutil_<timestamp>'.

Examples:
\t./ntap_dsutil.py create snapshot --volume=project1 --name=snap1
\t./ntap_dsutil.py create snapshot -v project2 -n final_dataset
\t./ntap_dsutil.py create snapshot --volume=test1
'''
helpTextCreateVolume = '''
Command: create volume

Create a new data volume.

Required Options/Arguments:
\t-n, --name=\t\tName of new volume.
\t-s, --size=\t\tSize of new volume. Format: '1024MB', '100GB', '10TB', etc.

Optional Options/Arguments:
\t-a, --aggregate=\tAggregate to use when creating new volume (flexvol volumes only).
\t-d, --snapshot-policy=\tSnapshot policy to apply for new volume.
\t-e, --export-policy=\tNFS export policy to use when exporting new volume.
\t-g, --gid=\t\tUnix filesystem group id (gid) to apply when creating new volume (ex. '0' for root group).
\t-h, --help\t\tPrint help text.
\t-m, --mountpoint=\tLocal mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
\t-p, --permissions=\tUnix filesystem permissions to apply when creating new volume (ex. '0777' for full read/write permissions for all users and groups).
\t-r, --guarantee-space\tGuarantee sufficient storage space for full capacity of the volume (i.e. do not use thin provisioning).
\t-t, --type=\t\tVolume type to use when creating new volume (flexgroup/flexvol).
\t-u, --uid=\t\tUnix filesystem user id (uid) to apply when creating new volume (ex. '0' for root user).

Examples (basic usage):
\t./ntap_dsutil.py create volume --name=project1 --size=10GB
\t./ntap_dsutil.py create volume -n datasets -s 10TB
\tsudo -E ./ntap_dsutil.py create volume --name=project2 --size=2TB --mountpoint=~/project2

Examples (advanced usage):
\tsudo -E ./ntap_dsutil.py create volume --name=project1 --size=10GB --permissions=0755 --type=flexvol --mountpoint=~/project1
\tsudo -E ./ntap_dsutil.py create volume --name=project2_flexgroup --size=2TB --type=flexgroup --mountpoint=/mnt/project2
\t./ntap_dsutil.py create volume --name=testvol --size=10GB --type=flexvol --aggregate=n2_data
\t./ntap_dsutil.py create volume -n testvol -s 10GB -t flexvol -p 0755 -u 1000 -g 1000
\tsudo -E ./ntap_dsutil.py create volume -n vol1 -s 5GB -t flexvol --export-policy=team1 -m /mnt/vol1
\t./ntap_dsutil.py create vol -n test2 -s 10GB -t flexvol --snapshot-policy=default
'''
helpTextDeleteSnapshot = '''
Command: delete snapshot

Delete an existing snapshot for a data volume.

Required Options/Arguments:
\t-n, --name=\tName of snapshot to be deleted.
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-h, --help\tPrint help text.

Examples:
\t./ntap_dsutil.py delete snapshot --volume=project1 --name=snap1
\t./ntap_dsutil.py delete snapshot -v project2 -n ntap_dsutil_20201113_221917
'''
helpTextDeleteVolume = '''
Command: delete volume

Delete an existing data volume.

Required Options/Arguments:
\t-n, --name=\tName of volume to be deleted.

Optional Options/Arguments:
\t-f, --force\tDo not prompt user to confirm operation.
\t-h, --help\tPrint help text.

Examples:
\t./ntap_dsutil.py delete volume --name=project1
\t./ntap_dsutil.py delete volume -n project2
'''
helpTextListCloudSyncRelationships = '''
Command: list cloud-sync-relationships

List all existing Cloud Sync relationships.

No additional options/arguments required.
'''
helpTextListSnapMirrorRelationships = '''
Command: list snapmirror-relationships

List all SnapMirror relationships.

No additional options/arguments required.
'''
helpTextListSnapshots = '''
Command: list snapshots

List all snapshots for a data volume.

Required Options/Arguments:
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-h, --help\tPrint help text.

Examples:
\t./ntap_dsutil.py list snapshots --volume=project1
\t./ntap_dsutil.py list snapshots -v test1
'''
helpTextListVolumes = '''
Command: list volumes

List all data volumes.

No additional options/arguments required.
'''
helpTextMountVolume = '''
Command: mount volume

Mount an existing data volume locally.

Requirement: On Linux hosts, must be run as root.

Required Options/Arguments:
\t-m, --mountpoint=\tLocal mountpoint to mount volume at.
\t-n, --name=\t\tName of volume.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.

Examples:
\tsudo -E ./ntap_dsutil.py mount volume --name=project1 --mountpoint=/mnt/project1
\tsudo -E ./ntap_dsutil.py mount volume -m ~/testvol -n testvol
'''
helpTextPullFromS3Bucket = '''
Command: pull-from-s3 bucket

Pull the contents of a bucket from S3 (multithreaded).

Note: To pull to a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to pull from.
\t-d, --directory=\tLocal directory to save contents of bucket to.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.
\t-p, --key-prefix=\tObject key prefix (pull will be limited to objects with key that starts with this prefix).

Examples:
\t./ntap_dsutil.py pull-from-s3 bucket --bucket=project1 --directory=/mnt/project1
\t./ntap_dsutil.py pull-from-s3 bucket -b project1 -p project1/ -d ./project1/
'''
helpTextPullFromS3Object = '''
Command: pull-from-s3 object

Pull an object from S3.

Note: To pull to a data volume, the volume must be mounted locally.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to pull from.
\t-k, --key=\t\tKey of S3 object to pull.

Optional Options/Arguments:
\t-f, --file=\t\tLocal filepath (including filename) to save object to (if not specified, value of -k/--key argument will be used)
\t-h, --help\t\tPrint help text.

Examples:
\t./ntap_dsutil.py pull-from-s3 object --bucket=project1 --key=data.csv --file=./project1/data.csv
\t./ntap_dsutil.py pull-from-s3 object -b project1 -k data.csv
'''
helpTextPushToS3Directory = '''
Command: push-to-s3 directory

Push the contents of a directory to S3 (multithreaded).

Note: To push from a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to push to.
\t-d, --directory=\tLocal directory to push contents of.

Optional Options/Arguments:
\t-e, --extra-args=\tExtra args to apply to newly-pushed S3 objects (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
\t-h, --help\t\tPrint help text.
\t-p, --key-prefix=\tPrefix to add to key for newly-pushed S3 objects (Note: by default, key will be local filepath relative to directory being pushed).

Examples:
\t./ntap_dsutil.py push-to-s3 directory --bucket=project1 --directory=/mnt/project1
\t./ntap_dsutil.py push-to-s3 directory -b project1 -d /mnt/project1 -p project1/ -e '{"Metadata": {"mykey": "myvalue"}}'
'''
helpTextPushToS3File = '''
Command: push-to-s3 file

Push a file to S3.

Note: To push from a data volume, the volume must be mounted locally.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to push to.
\t-f, --file=\t\tLocal file to push.

Optional Options/Arguments:
\t-e, --extra-args=\tExtra args to apply to newly-pushed S3 object (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
\t-h, --help\t\tPrint help text.
\t-k, --key=\t\tKey to assign to newly-pushed S3 object (if not specified, key will be set to value of -f/--file argument).

Examples:
\t./ntap_dsutil.py push-to-s3 file --bucket=project1 --file=data.csv
\t./ntap_dsutil.py push-to-s3 file -b project1 -k data.csv -f /mnt/project1/data.csv -e '{"Metadata": {"mykey": "myvalue"}}'
'''
helpTextPrepopulateFlexCache = '''
Command: prepopulate flexcache

Prepopulate specific files/directories on a FlexCache volume.

Compatibility: ONTAP 9.8 and above ONLY

Required Options/Arguments:
\t-n, --name=\tName of FlexCache volume.
\t-p, --paths=\tComma-separated list of dirpaths/filepaths to prepopulate.

Optional Options/Arguments:
\t-h, --help\tPrint help text.

Examples:
\t./ntap_dsutil.py prepopulate flexcache --name=project1 --paths=/datasets/project1,/datasets/project2
\t./ntap_dsutil.py prepopulate flexcache -n test1 -p /datasets/project1,/datasets/project2
'''
helpTextRestoreSnapshot = '''
Command: restore snapshot

Restore a snapshot for a data volume (restore the volume to its exact state at the time that the snapshot was created).

Required Options/Arguments:
\t-n, --name=\tName of snapshot to be restored.
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-f, --force\tDo not prompt user to confirm operation.
\t-h, --help\tPrint help text.

Examples:
\t./ntap_dsutil.py restore snapshot --volume=project1 --name=snap1
\t./ntap_dsutil.py restore snapshot -v project2 -n ntap_dsutil_20201113_221917
'''
helpTextSyncCloudSyncRelationship = '''
Command: sync cloud-sync-relationship

Trigger a sync operation for an existing Cloud Sync relationship.

Tip: Run `./ntap_dsutil.py list cloud-sync-relationships` to obtain relationship ID.

Required Options/Arguments:
\t-i, --id=\tID of the relationship for which the sync operation is to be triggered.

Optional Options/Arguments:
\t-h, --help\tPrint help text.
\t-w, --wait\tWait for sync operation to complete before exiting.

Examples:
\t./ntap_dsutil.py sync cloud-sync-relationship --id=5ed00996ca85650009a83db2
\t./ntap_dsutil.py sync cloud-sync-relationship -i 5ed00996ca85650009a83db2 -w
'''
helpTextSyncSnapMirrorRelationship = '''
Command: sync snapmirror-relationship

Trigger a sync operation for an existing SnapMirror relationship.

Tip: Run `./ntap_dsutil.py list snapmirror-relationships` to obtain relationship UUID.

Required Options/Arguments:
\t-i, --uuid=\tUUID of the relationship for which the sync operation is to be triggered.

Optional Options/Arguments:
\t-h, --help\tPrint help text.
\t-w, --wait\tWait for sync operation to complete before exiting.

Examples:
\t./ntap_dsutil.py sync snapmirror-relationship --uuid=132aab2c-4557-11eb-b542-005056932373
\t./ntap_dsutil.py sync snapmirror-relationship -i 132aab2c-4557-11eb-b542-005056932373 -w
'''


## Function for handling situation in which user enters invalid command
def handleInvalidCommand(helpText: str = helpTextStandard, invalidOptArg: bool = False) :
    if invalidOptArg :
        print("Error: Invalid option/argument.")
    else :
        print("Error: Invalid command.")
    print(helpText)
    sys.exit(1)


## Function for getting desired target from command line args
def getTarget(args: list) -> str:
    try :
        target = args[2]
    except :
        handleInvalidCommand()
    return target


## Main function
if __name__ == '__main__' :
    import sys, getopt

    # Get desired action from command line args
    try :
        action = sys.argv[1]
    except :
        handleInvalidCommand()

    # Invoke desired action
    if action == "clone" :
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("volume", "vol") :
            newVolumeName = None
            sourceVolumeName = None
            sourceSnapshotName = None
            mountpoint = None
            unixUID = None
            unixGID = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:v:s:m:u:g:", ["help", "name=", "source-volume=", "source-snapshot=", "mountpoint=", "uid=", "gid="])
            except :
                handleInvalidCommand(helpText=helpTextCloneVolume, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCloneVolume)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    newVolumeName = arg
                elif opt in ("-v", "--source-volume") :
                    sourceVolumeName = arg
                elif opt in ("-s", "--source-snapshot") :
                    sourceSnapshotName = arg
                elif opt in ("-m", "--mountpoint") :
                    mountpoint = arg
                elif opt in ("-u", "--uid") :
                    unixUID = arg
                elif opt in ("-g", "--gid") :
                    unixGID = arg
            
            # Check for required options
            if not newVolumeName or not sourceVolumeName  :
                handleInvalidCommand(helpText=helpTextCloneVolume, invalidOptArg=True)
            if (unixUID and not unixGID) or (unixGID and not unixUID) :
                print("Error: if either one of -u/--uid or -g/--gid is spefied, then both must be specified.")
                handleInvalidCommand(helpText=helpTextCloneVolume, invalidOptArg=True)

            # Clone volume
            try :
                cloneVolume(newVolumeName=newVolumeName, sourceVolumeName=sourceVolumeName, sourceSnapshotName=sourceSnapshotName, 
                    mountpoint=mountpoint, unixUID=unixUID, unixGID=unixGID, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError, MountOperationError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("config", "setup") :
        if len(sys.argv) > 2 :
            if sys.argv[2] in ("-h", "--help") :
                print(helpTextConfig)
                sys.exit(0)
            else :
                handleInvalidCommand(helpTextConfig, invalidOptArg=True)

        #connectionType = input("Enter connection type (ONTAP): ")
        connectionType = "ONTAP"

        # Create config file
        createConfig(connectionType=connectionType)

    elif action == "create" :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("snapshot", "snap") :
            volumeName = None
            snapshotName = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:v:", ["help", "name=", "volume="])
            except :
                handleInvalidCommand(helpText=helpTextCreateSnapshot, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCreateSnapshot)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    snapshotName = arg
                elif opt in ("-v", "--volume") :
                    volumeName = arg
            
            # Check for required options
            if not volumeName  :
                handleInvalidCommand(helpText=helpTextCreateSnapshot, invalidOptArg=True)

            # Create snapshot
            try :
                createSnapshot(volumeName=volumeName, snapshotName=snapshotName, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError) :
                sys.exit(1)

        elif target in ("volume", "vol") :
            volumeName = None
            volumeSize = None
            guaranteeSpace = False
            volumeType = None
            unixPermissions = None
            unixUID = None
            unixGID = None
            exportPolicy = None
            snapshotPolicy = None
            mountpoint = None
            aggregate = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:s:rt:p:u:g:e:d:m:a:", ["help", "name=", "size=", "guarantee-space", "type=", "permissions=", "uid=", "gid=", "export-policy=", "snapshot-policy=", "mountpoint=", "aggregate="])
            except :
                handleInvalidCommand(helpText=helpTextCreateVolume, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCreateVolume)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    volumeName = arg
                elif opt in ("-s", "--size") :
                    volumeSize = arg
                elif opt in ("-r", "--guarantee-space") :
                    guaranteeSpace = True
                elif opt in ("-t", "--type") :
                    volumeType = arg
                elif opt in ("-p", "--permissions") :
                    unixPermissions = arg
                elif opt in ("-u", "--uid") :
                    unixUID = arg
                elif opt in ("-g", "--gid") :
                    unixGID = arg
                elif opt in ("-e", "--export-policy") :
                    exportPolicy = arg
                elif opt in ("-d", "--snapshot-policy") :
                    snapshotPolicy = arg
                elif opt in ("-m", "--mountpoint") :
                    mountpoint = arg
                elif opt in ("-a", "--aggregate") :
                    aggregate = arg
            
            # Check for required options
            if not volumeName or not volumeSize :
                handleInvalidCommand(helpText=helpTextCreateVolume, invalidOptArg=True)
            if (unixUID and not unixGID) or (unixGID and not unixUID) :
                print("Error: if either one of -u/--uid or -g/--gid is spefied, then both must be specified.")
                handleInvalidCommand(helpText=helpTextCreateVolume, invalidOptArg=True)

            # Create volume
            try :
                createVolume(volumeName=volumeName, volumeSize=volumeSize, guaranteeSpace=guaranteeSpace, volumeType=volumeType, unixPermissions=unixPermissions, unixUID=unixUID, 
                    unixGID=unixGID, exportPolicy=exportPolicy, snapshotPolicy=snapshotPolicy, aggregate=aggregate, mountpoint=mountpoint, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("delete", "del", "rm") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("snapshot", "snap") :
            volumeName = None
            snapshotName = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:v:", ["help", "name=", "volume="])
            except :
                handleInvalidCommand(helpText=helpTextDeleteSnapshot, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextDeleteSnapshot)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    snapshotName = arg
                elif opt in ("-v", "--volume") :
                    volumeName = arg
            
            # Check for required options
            if not volumeName or not snapshotName  :
                handleInvalidCommand(helpText=helpTextDeleteSnapshot, invalidOptArg=True)

            # Delete snapshot
            try :
                deleteSnapshot(volumeName=volumeName, snapshotName=snapshotName, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError) :
                sys.exit(1)

        elif target in ("volume", "vol") :
            volumeName = None
            force = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:f", ["help", "name=", "force"])
            except :
                handleInvalidCommand(helpText=helpTextDeleteVolume, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextDeleteVolume)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    volumeName = arg
                elif opt in ("-f", "--force") :
                    force = True
            
            # Check for required options
            if not volumeName :
                handleInvalidCommand(helpText=helpTextDeleteVolume, invalidOptArg=True)

            # Confirm delete operation
            if not force :
                print("Warning: All data and snapshots associated with the volume will be permanently deleted.")
                while True :
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES") :
                        break
                    elif proceed in ("no", "No", "NO") :
                        sys.exit(0)
                    else :
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Delete volume
            try :
                deleteVolume(volumeName=volumeName, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("help", "h", "-h", "--help") :
        print(helpTextStandard)
        
    elif action in ("list", "ls") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("cloud-sync-relationship", "cloud-sync", "cloud-sync-relationships", "cloud-syncs") :
            # Check command line options
            if len(sys.argv) > 3 :
                if sys.argv[3] in ("-h", "--help") :
                    print(helpTextListCloudSyncRelationships)
                    sys.exit(0)
                else :
                    handleInvalidCommand(helpTextListCloudSyncRelationships, invalidOptArg=True)

            # List cloud sync relationships
            try :
                listCloudSyncRelationships(printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)
        
        elif target in ("snapmirror-relationship", "snapmirror", "snapmirror-relationships", "snapmirrors") :
            # Check command line options
            if len(sys.argv) > 3 :
                if sys.argv[3] in ("-h", "--help") :
                    print(helpTextListSnapMirrorRelationships)
                    sys.exit(0)
                else :
                    handleInvalidCommand(helpTextListSnapMirrorRelationships, invalidOptArg=True)

            # List cloud sync relationships
            try :
                listSnapMirrorRelationships(printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)
        
        elif target in ("snapshot", "snap", "snapshots", "snaps") :
            volumeName = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hv:", ["help", "volume="])
            except :
                handleInvalidCommand(helpText=helpTextListSnapshots, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextListSnapshots)
                    sys.exit(0)
                elif opt in ("-v", "--volume") :
                    volumeName = arg
            
            # Check for required options
            if not volumeName  :
                handleInvalidCommand(helpText=helpTextListSnapshots, invalidOptArg=True)

            # List volumes
            try :
                listSnapshots(volumeName=volumeName, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError) :
                sys.exit(1)
        
        elif target in ("volume", "vol", "volumes", "vols") :
            # Check command line options
            if len(sys.argv) > 3 :
                if sys.argv[3] in ("-h", "--help") :
                    print(helpTextListVolumes)
                    sys.exit(0)
                else :
                    handleInvalidCommand(helpTextListVolumes, invalidOptArg=True)

            # List volumes
            try :
                listVolumes(checkLocalMounts=True, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action == "mount" :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("volume", "vol") :
            volumeName = None
            mountpoint = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:m:", ["help", "name=", "mountpoint="])
            except :
                handleInvalidCommand(helpText=helpTextMountVolume, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextMountVolume)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    volumeName = arg
                elif opt in ("-m", "--mountpoint") :
                    mountpoint = arg

            # Mount volume
            try :
                mountVolume(volumeName=volumeName, mountpoint=mountpoint, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError) :
                sys.exit(1)

        else :
            handleInvalidCommand()
        
    elif action in ("prepopulate") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("flexcache", "cache") :
            volumeName = None
            paths = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:p:", ["help", "name=", "paths="])
            except :
                handleInvalidCommand(helpText=helpTextPrepopulateFlexCache, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextPrepopulateFlexCache)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    volumeName = arg
                elif opt in ("-p", "--paths") :
                    paths = arg

            # Check for required options
            if not volumeName or not paths :
                handleInvalidCommand(helpText=helpTextPrepopulateFlexCache, invalidOptArg=True)

            # Convert paths string to list
            pathsList = paths.split(",")

            # Prepopulate FlexCache
            try :
                prepopulateFlexCache(volumeName=volumeName, paths=pathsList, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError) :
                sys.exit(1)
        
        else :
            handleInvalidCommand()

    elif action in ("pull-from-s3", "pull-s3", "s3-pull") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("bucket") :
            s3Bucket = None
            s3ObjectKeyPrefix = ""
            localDirectory = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hb:p:d:e:", ["help", "bucket=", "key-prefix=", "directory="])
            except :
                handleInvalidCommand(helpText=helpTextPullFromS3Bucket, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextPullFromS3Bucket)
                    sys.exit(0)
                elif opt in ("-b", "--bucket") :
                    s3Bucket = arg
                elif opt in ("-p", "--key-prefix") :
                    s3ObjectKeyPrefix = arg
                elif opt in ("-d", "--directory") :
                    localDirectory = arg
            
            # Check for required options
            if not s3Bucket or not localDirectory  :
                handleInvalidCommand(helpText=helpTextPullFromS3Bucket, invalidOptArg=True)

            # Push file to S3
            try :
                pullBucketFromS3(s3Bucket=s3Bucket, localDirectory=localDirectory, s3ObjectKeyPrefix=s3ObjectKeyPrefix, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("object", "file") :
            s3Bucket = None
            s3ObjectKey = None
            localFile = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hb:k:f:", ["help", "bucket=", "key=", "file=", "extra-args="])
            except :
                handleInvalidCommand(helpText=helpTextPullFromS3Object, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextPullFromS3Object)
                    sys.exit(0)
                elif opt in ("-b", "--bucket") :
                    s3Bucket = arg
                elif opt in ("-k", "--key") :
                    s3ObjectKey = arg
                elif opt in ("-f", "--file") :
                    localFile = arg
            
            # Check for required options
            if not s3Bucket or not s3ObjectKey  :
                handleInvalidCommand(helpText=helpTextPullFromS3Object, invalidOptArg=True)

            # Push file to S3
            try :
                pullObjectFromS3(s3Bucket=s3Bucket, s3ObjectKey=s3ObjectKey, localFile=localFile, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("push-to-s3", "push-s3", "s3-push") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("directory", "dir") :
            s3Bucket = None
            s3ObjectKeyPrefix = ""
            localDirectory = None
            s3ExtraArgs = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hb:p:d:e:", ["help", "bucket=", "key-prefix=", "directory=", "extra-args="])
            except :
                handleInvalidCommand(helpText=helpTextPushToS3Directory, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextPushToS3Directory)
                    sys.exit(0)
                elif opt in ("-b", "--bucket") :
                    s3Bucket = arg
                elif opt in ("-p", "--key-prefix") :
                    s3ObjectKeyPrefix = arg
                elif opt in ("-d", "--directory") :
                    localDirectory = arg
                elif opt in ("-e", "--extra-args") :
                    s3ExtraArgs = arg
            
            # Check for required options
            if not s3Bucket or not localDirectory  :
                handleInvalidCommand(helpText=helpTextPushToS3Directory, invalidOptArg=True)

            # Push file to S3
            try :
                pushDirectoryToS3(s3Bucket=s3Bucket, localDirectory=localDirectory, s3ObjectKeyPrefix=s3ObjectKeyPrefix, s3ExtraArgs=s3ExtraArgs, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("file") :
            s3Bucket = None
            s3ObjectKey = None
            localFile = None
            s3ExtraArgs = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hb:k:f:e:", ["help", "bucket=", "key=", "file=", "extra-args="])
            except :
                handleInvalidCommand(helpText=helpTextPushToS3File, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextPushToS3File)
                    sys.exit(0)
                elif opt in ("-b", "--bucket") :
                    s3Bucket = arg
                elif opt in ("-k", "--key") :
                    s3ObjectKey = arg
                elif opt in ("-f", "--file") :
                    localFile = arg
                elif opt in ("-e", "--extra-args") :
                    s3ExtraArgs = arg
            
            # Check for required options
            if not s3Bucket or not localFile  :
                handleInvalidCommand(helpText=helpTextPushToS3File, invalidOptArg=True)

            # Push file to S3
            try :
                pushFileToS3(s3Bucket=s3Bucket, s3ObjectKey=s3ObjectKey, localFile=localFile, s3ExtraArgs=s3ExtraArgs, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("restore") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("snapshot", "snap") :
            volumeName = None
            snapshotName = None
            force = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:v:f", ["help", "name=", "volume=", "force"])
            except :
                handleInvalidCommand(helpText=helpTextRestoreSnapshot, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextRestoreSnapshot)
                    sys.exit(0)
                elif opt in ("-n", "--name") :
                    snapshotName = arg
                elif opt in ("-v", "--volume") :
                    volumeName = arg
                elif opt in ("-f", "--force") :
                    force = True
            
            # Check for required options
            if not volumeName or not snapshotName  :
                handleInvalidCommand(helpText=helpTextRestoreSnapshot, invalidOptArg=True)

            # Confirm restore operation
            if not force :
                print("Warning: When you restore a snapshot, all subsequent snapshots are deleted.")
                while True :
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES") :
                        break
                    elif proceed in ("no", "No", "NO") :
                        sys.exit(0)
                    else :
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Restore snapshot
            try :
                restoreSnapshot(volumeName=volumeName, snapshotName=snapshotName, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action == "sync" :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("cloud-sync-relationship", "cloud-sync") :
            relationshipID = None
            waitUntilComplete = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hi:w", ["help", "id=", "wait"])
            except :
                handleInvalidCommand(helpText=helpTextSyncCloudSyncRelationship, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextSyncCloudSyncRelationship)
                    sys.exit(0)
                elif opt in ("-i", "--id") :
                    relationshipID = arg
                elif opt in ("-w", "--wait") :
                    waitUntilComplete = True

            # Check for required options
            if not relationshipID :
                handleInvalidCommand(helpText=helpTextSyncCloudSyncRelationship, invalidOptArg=True)

            # Update cloud sync relationship
            try :
                syncCloudSyncRelationship(relationshipID=relationshipID, waitUntilComplete=waitUntilComplete, printOutput=True)
            except (InvalidConfigError, APIConnectionError, CloudSyncSyncOperationError) :
                sys.exit(1)

        elif target in ("snapmirror-relationship", "snapmirror") :
            uuid = None
            waitUntilComplete = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hi:w", ["help", "uuid=", "wait"])
            except :
                handleInvalidCommand(helpText=helpTextSyncSnapMirrorRelationship, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextSyncSnapMirrorRelationship)
                    sys.exit(0)
                elif opt in ("-i", "--uuid") :
                    uuid = arg
                elif opt in ("-w", "--wait") :
                    waitUntilComplete = True

            # Check for required options
            if not uuid :
                handleInvalidCommand(helpText=helpTextSyncSnapMirrorRelationship, invalidOptArg=True)

            # Update SnapMirror relationship
            try :
                syncSnapMirrorRelationship(uuid=uuid, waitUntilComplete=waitUntilComplete, printOutput=True)
            except (InvalidConfigError, APIConnectionError, InvalidSnapMirrorParameterError, SnapMirrorSyncOperationError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("version", "v", "-v", "--version") :
        print("NetApp Data Science Toolkit for Traditional Environments - version " + version)
        
    else :
        handleInvalidCommand()