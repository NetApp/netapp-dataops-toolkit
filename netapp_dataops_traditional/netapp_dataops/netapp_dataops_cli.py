#!/usr/bin/env python3

import base64
import json
import os
import re
from getpass import getpass

import sys
sys.path.insert(0, "/root/netapp-dataops-toolkit/netapp_dataops_traditional/netapp_dataops")

from netapp_dataops import traditional
from netapp_dataops.help_text import (
    HELP_TEXT_STANDARD,
    HELP_TEXT_CONFIG,
    HELP_TEXT_CLONE_VOLUME,
    HELP_TEXT_CREATE_VOLUME,
    HELP_TEXT_DELETE_VOLUME,
    HELP_TEXT_LIST_VOLUMES,
    HELP_TEXT_MOUNT_VOLUME,
    HELP_TEXT_UNMOUNT_VOLUME,
    HELP_TEXT_CREATE_SNAPSHOT,
    HELP_TEXT_DELETE_SNAPSHOT,
    HELP_TEXT_LIST_SNAPSHOTS,
    HELP_TEXT_RESTORE_SNAPSHOT,
    HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP,
    HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS,
    HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP,
    HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS,
    HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP,
    HELP_TEXT_PULL_FROM_S3_BUCKET,
    HELP_TEXT_PULL_FROM_S3_OBJECT,
    HELP_TEXT_PUSH_TO_S3_DIRECTORY,
    HELP_TEXT_PUSH_TO_S3_FILE,
    HELP_TEXT_PREPOPULATE_FLEXCACHE
)
from netapp_dataops.traditional import (
    clone_volume,
    InvalidConfigError,
    InvalidVolumeParameterError,
    InvalidSnapMirrorParameterError,
    InvalidSnapshotParameterError,
    APIConnectionError,
    mount_volume,
    unmount_volume,
    MountOperationError,
    ConnectionTypeError,
    list_volumes,
    create_snapshot,
    create_volume,
    delete_snapshot,
    delete_volume,
    list_cloud_sync_relationships,
    list_snap_mirror_relationships,
    create_snap_mirror_relationship,
    list_snapshots,
    prepopulate_flex_cache,
    pull_bucket_from_s3,
    pull_object_from_s3,
    push_directory_to_s3,
    push_file_to_s3,
    restore_snapshot,
    CloudSyncSyncOperationError,
    sync_cloud_sync_relationship,
    sync_snap_mirror_relationship,
    SnapMirrorSyncOperationError
)


## Function for creating config file
def createConfig(configDirPath: str = "~/.netapp_dataops", configFilename: str = "config.json", connectionType: str = "ONTAP"):
    # Check to see if user has an existing config file
    configDirPath = os.path.expanduser(configDirPath)
    configFilePath = os.path.join(configDirPath, configFilename)
    if os.path.isfile(configFilePath):
        print("You already have an existing config file. Creating a new config file will overwrite this existing config.")
        # If existing config file is present, ask user if they want to proceed
        # Verify value entered; prompt user to re-enter if invalid
        while True:
            proceed = input("Are you sure that you want to proceed? (yes/no): ")
            if proceed in ("yes", "Yes", "YES"):
                break
            elif proceed in ("no", "No", "NO"):
                sys.exit(0)
            else:
                print("Invalid value. Must enter 'yes' or 'no'.")

    # Instantiate dict for storing connection details
    config = dict()

    if connectionType == "ONTAP":
        config["connectionType"] = connectionType

        # Prompt user to enter config details
        config["hostname"] = input("Enter ONTAP management LIF hostname or IP address (Recommendation: Use SVM management interface): ")
        config["svm"] = input("Enter SVM (Storage VM) name: ")
        config["dataLif"] = input("Enter SVM NFS data LIF hostname or IP address: ")

        # Prompt user to enter default volume type
        # Verify value entered; promopt user to re-enter if invalid
        while True:
            config["defaultVolumeType"] = input("Enter default volume type to use when creating new volumes (flexgroup/flexvol) [flexgroup]: ")
            if not config["defaultVolumeType"] :
                config["defaultVolumeType"] = "flexgroup"
                break
            elif config["defaultVolumeType"] in ("flexgroup", "FlexGroup"):
                config["defaultVolumeType"] = "flexgroup"
                break
            elif config["defaultVolumeType"] in ("flexvol", "FlexVol"):
                config["defaultVolumeType"] = "flexvol"
                break
            else:
                print("Invalid value. Must enter 'flexgroup' or 'flexvol'.")

        # prompt user to enter default export policy
        config["defaultExportPolicy"] = input("Enter export policy to use by default when creating new volumes [default]: ")
        if not config["defaultExportPolicy"]:
            config["defaultExportPolicy"] = "default"

        # prompt user to enter default snapshot policy
        config["defaultSnapshotPolicy"] = input("Enter snapshot policy to use by default when creating new volumes [none]: ")
        if not config["defaultSnapshotPolicy"]:
            config["defaultSnapshotPolicy"] = "none"

        # Prompt user to enter default uid, gid, and unix permissions
        # Verify values entered; promopt user to re-enter if invalid
        while True:
            config["defaultUnixUID"] = input("Enter unix filesystem user id (uid) to apply by default when creating new volumes (ex. '0' for root user) [0]: ")
            if not config["defaultUnixUID"]:
                config["defaultUnixUID"] = "0"
                break
            try:
                int(config["defaultUnixUID"])
                break
            except:
                print("Invalid value. Must enter an integer.")
        while True:
            config["defaultUnixGID"] = input("Enter unix filesystem group id (gid) to apply by default when creating new volumes (ex. '0' for root group) [0]: ")
            if not config["defaultUnixGID"]:
                config["defaultUnixGID"] = "0"
                break
            try:
                int(config["defaultUnixGID"])
                break
            except:
                print("Invalid value. Must enter an integer.")
        while True:
            config["defaultUnixPermissions"] = input("Enter unix filesystem permissions to apply by default when creating new volumes (ex. '0777' for full read/write permissions for all users and groups) [0777]: ")
            if not config["defaultUnixPermissions"] :
                config["defaultUnixPermissions"] = "0777"
                break
            elif not re.search("^0[0-7]{3}", config["defaultUnixPermissions"]):
                print("Invalud value. Must enter a valid unix permissions value. Acceptable values are '0777', '0755', '0744', etc.")
            else:
                break

        # Prompt user to enter additional config details
        config["defaultAggregate"] = input("Enter aggregate to use by default when creating new FlexVol volumes: ")
        config["username"] = input("Enter ONTAP API username (Recommendation: Use SVM account): ")
        passwordString = getpass("Enter ONTAP API password (Recommendation: Use SVM account): ")

        # Convert password to base64 enconding
        passwordBytes = passwordString.encode("ascii")
        passwordBase64Bytes = base64.b64encode(passwordBytes)
        config["password"] = passwordBase64Bytes.decode("ascii")

        # Prompt user to enter value denoting whether or not to verify SSL cert when calling ONTAP API
        # Verify value entered; prompt user to re-enter if invalid
        while True:
            verifySSLCert = input("Verify SSL certificate when calling ONTAP API (true/false): ")
            if verifySSLCert in ("true", "True") :
                config["verifySSLCert"] = True
                break
            elif verifySSLCert in ("false", "False") :
                config["verifySSLCert"] = False
                break
            else:
                print("Invalid value. Must enter 'true' or 'false'.")

    else:
        raise ConnectionTypeError()

    # Ask user if they want to use cloud sync functionality
    # Verify value entered; prompt user to re-enter if invalid
    while True:
        useCloudSync = input("Do you intend to use this toolkit to trigger Cloud Sync operations? (yes/no): ")

        if useCloudSync in ("yes", "Yes", "YES"):
            # Prompt user to enter cloud central refresh token
            print("Note: If you do not have a Cloud Central refresh token, visit https://services.cloud.netapp.com/refresh-token to create one.")
            refreshTokenString = getpass("Enter Cloud Central refresh token: ")

            # Convert refresh token to base64 enconding
            refreshTokenBytes = refreshTokenString.encode("ascii")
            refreshTokenBase64Bytes = base64.b64encode(refreshTokenBytes)
            config["cloudCentralRefreshToken"] = refreshTokenBase64Bytes.decode("ascii")

            break

        elif useCloudSync in ("no", "No", "NO"):
            break

        else:
            print("Invalid value. Must enter 'yes' or 'no'.")

    # Ask user if they want to use S3 functionality
    # Verify value entered; prompt user to re-enter if invalid
    while True:
        useS3 = input("Do you intend to use this toolkit to push/pull from S3? (yes/no): ")

        if useS3 in ("yes", "Yes", "YES"):
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
            while True:
                s3VerifySSLCert = input("Verify SSL certificate when calling S3 API (true/false): ")
                if s3VerifySSLCert in ("true", "True"):
                    config["s3VerifySSLCert"] = True
                    config["s3CACertBundle"] = input("Enter CA cert bundle to use when calling S3 API (optional) []: ")
                    break
                elif s3VerifySSLCert in ("false", "False"):
                    config["s3VerifySSLCert"] = False
                    config["s3CACertBundle"] = ""
                    break
                else:
                    print("Invalid value. Must enter 'true' or 'false'.")

            break

        elif useS3 in ("no", "No", "NO"):
            break

        else:
            print("Invalid value. Must enter 'yes' or 'no'.")

    # Create config dir if it doesn't already exist
    try:
        os.mkdir(configDirPath)
    except FileExistsError :
        pass

    # Create config file in config dir
    with open(configFilePath, 'w') as configFile:
        # Write connection details to config file
        json.dump(config, configFile)

    print("Created config file: '" + configFilePath + "'.")


def getTarget(args: list) -> str:
    try:
        target = args[2]
    except:
        handleInvalidCommand()
    return target


def handleInvalidCommand(helpText: str = HELP_TEXT_STANDARD, invalidOptArg: bool = False):
    if invalidOptArg:
        print("Error: Invalid option/argument.")
    else:
        print("Error: Invalid command.")
    print(helpText)
    sys.exit(1)


## Main function
if __name__ == '__main__':
    import sys, getopt

    # Get desired action from command line args
    try:
        action = sys.argv[1]
    except:
        handleInvalidCommand()

    # Invoke desired action
    if action == "clone":
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("volume", "vol"):
            newVolumeName = None
            clusterName = None
            sourceSVM = None
            targetSVM = None
            sourceVolumeName = None
            sourceSnapshotName = None
            mountpoint = None
            unixUID = None
            unixGID = None
            junction = None
            readonly = False
            split = False
            refresh = False
            exportPolicy = None
            snapshotPolicy = None
            exportHosts = None
            svmDrUnprotect = False

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hl:c:t:n:v:s:m:u:g:j:xe:p:i:srd", ["help", "cluster-name=", "source-svm=","target-svm=","name=", "source-volume=", "source-snapshot=", "mountpoint=", "uid=", "gid=", "junction=", "readonly","export-hosts=","export-policy=","snapshot-policy=","split","refresh","svm-dr-unprotect"])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_CLONE_VOLUME, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_CLONE_VOLUME)
                    sys.exit(0)
                elif opt in ("-l", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-n", "--name"):
                    newVolumeName = arg
                elif opt in ("-c", "--source-svm"):
                    sourceSVM = arg
                elif opt in ("-t", "--target-svm"):
                    targetSVM = arg
                elif opt in ("-v", "--source-volume"):
                    sourceVolumeName = arg
                elif opt in ("-s", "--source-snapshot"):
                    sourceSnapshotName = arg
                elif opt in ("-m", "--mountpoint"):
                    mountpoint = arg
                elif opt in ("-u", "--uid"):
                    unixUID = arg
                elif opt in ("-g", "--gid"):
                    unixGID = arg
                elif opt in ("-j", "--junction"):
                    junction = arg
                elif opt in ("-x", "--readonly"):
                    readonly = True
                elif opt in ("-s", "--split"):
                    split = True
                elif opt in ("-r", "--refresh"):
                    refresh = True
                elif opt in ("-d", "--svm-dr-unprotect"):
                    svmDrUnprotect = True
                elif opt in ("-p", "--export-policy"):
                    exportPolicy = arg
                elif opt in ("-i", "--snapshot-policy"):
                    snapshotPolicy = arg
                elif opt in ("-e", "--export-hosts"):
                    exportHosts = arg

            # Check for required options
            if not newVolumeName or not sourceVolumeName:
                handleInvalidCommand(helpText=HELP_TEXT_CLONE_VOLUME, invalidOptArg=True)
            if (unixUID and not unixGID) or (unixGID and not unixUID):
                print("Error: if either one of -u/--uid or -g/--gid is spefied, then both must be specified.")
                handleInvalidCommand(helpText=HELP_TEXT_CLONE_VOLUME, invalidOptArg=True)
            if exportHosts and exportPolicy:
                print("Error: cannot use both --export-policy and --export-hosts. only one of them can be specified.")
                handleInvalidCommand(helpText=HELP_TEXT_CLONE_VOLUME, invalidOptArg=True)

            # Clone volume
            try:
                clone_volume(new_volume_name=newVolumeName, source_volume_name=sourceVolumeName, source_snapshot_name=sourceSnapshotName,
                             cluster_name=clusterName, source_svm=sourceSVM, target_svm=targetSVM, export_policy=exportPolicy, export_hosts=exportHosts,
                             snapshot_policy=snapshotPolicy, split=split, refresh=refresh, mountpoint=mountpoint, unix_uid=unixUID, unix_gid=unixGID,
                             junction=junction, svm_dr_unprotect=svmDrUnprotect, readonly=readonly, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError,
                    MountOperationError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action in ("config", "setup"):
        if len(sys.argv) > 2 :
            if sys.argv[2] in ("-h", "--help"):
                print(HELP_TEXT_CONFIG)
                sys.exit(0)
            else:
                handleInvalidCommand(HELP_TEXT_CONFIG, invalidOptArg=True)

        #connectionType = input("Enter connection type (ONTAP): ")
        connectionType = "ONTAP"

        # Create config file
        createConfig(connectionType=connectionType)

    elif action == "create":
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("snapshot", "snap"):
            volumeName = None
            snapshotName = None
            clusterName = None
            svmName = None
            retentionCount = 0
            retentionDays = False
            snapmirrorLabel = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hn:v:s:r:u:l:", ["cluster-name=","help", "svm=", "name=", "volume=", "retention=", "snapmirror-label="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_SNAPSHOT, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help") :
                    print(HELP_TEXT_CREATE_SNAPSHOT)
                    sys.exit(0)
                elif opt in ("-n", "--name"):
                    snapshotName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-s", "--svm"):
                    svmName = arg
                elif opt in ("-r", "--retention"):
                    retentionCount = arg
                elif opt in ("-v", "--volume"):
                    volumeName = arg
                elif opt in ("-l", "--snapmirror-label"):
                    snapmirrorLabel = arg

            # Check for required options
            if not volumeName:
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_SNAPSHOT, invalidOptArg=True)

            if retentionCount:
                if not retentionCount.isnumeric():
                    matchObj = re.match(r"^(\d+)d$",retentionCount)
                    if not matchObj:
                        handleInvalidCommand(helpText=HELP_TEXT_CREATE_SNAPSHOT, invalidOptArg=True)
                    else:
                        retentionCount = matchObj.group(1)
                        retentionDays = True

            # Create snapshot
            try:
                create_snapshot(volume_name=volumeName, snapshot_name=snapshotName, retention_count=retentionCount, retention_days=retentionDays, cluster_name=clusterName, svm_name=svmName, snapmirror_label=snapmirrorLabel, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
                sys.exit(1)

        elif target in ("volume", "vol"):
            clusterName = None
            svmName = None
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
            snaplock_type = None
            aggregate = None
            junction = None
            readonly = False
            tieringPolicy = None
            volDP = False

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "l:hv:t:n:s:rt:p:u:g:e:d:m:a:j:xu:yw:", ["cluster-name=","help", "svm=", "name=", "size=", "guarantee-space", "type=", "permissions=", "uid=", "gid=", "export-policy=", "snapshot-policy=", "mountpoint=", "aggregate=", "junction=" ,"readonly","tiering-policy=","dp","snaplock-type="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_VOLUME, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_CREATE_VOLUME)
                    sys.exit(0)
                elif opt in ("-v", "--svm"):
                    svmName = arg
                elif opt in ("-l", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-n", "--name"):
                    volumeName = arg
                elif opt in ("-s", "--size"):
                    volumeSize = arg
                elif opt in ("-r", "--guarantee-space"):
                    guaranteeSpace = True
                elif opt in ("-t", "--type"):
                    volumeType = arg
                elif opt in ("-p", "--permissions"):
                    unixPermissions = arg
                elif opt in ("-u", "--uid"):
                    unixUID = arg
                elif opt in ("-g", "--gid"):
                    unixGID = arg
                elif opt in ("-e", "--export-policy"):
                    exportPolicy = arg
                elif opt in ("-d", "--snapshot-policy"):
                    snapshotPolicy = arg
                elif opt in ("-m", "--mountpoint"):
                    mountpoint = arg
                elif opt in ("-a", "--aggregate"):
                    aggregate = arg
                elif opt in ("-j", "--junction"):
                    junction = arg
                elif opt in ("-x", "--readonly"):
                    readonly = True
                elif opt in ("-f", "--tiering-policy"):
                    tieringPolicy = arg
                elif opt in ("-y", "--dp"):
                    volDP = True
                elif opt in ("-w", "--snaplock-type"):
                    snaplock_type = arg

            # Check for required options
            if not volumeName or not volumeSize:
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_VOLUME, invalidOptArg=True)
            if (unixUID and not unixGID) or (unixGID and not unixUID):
                print("Error: if either one of -u/--uid or -g/--gid is spefied, then both must be specified.")
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_VOLUME, invalidOptArg=True)
            if (volDP and (junction or mountpoint or snapshotPolicy or exportPolicy)):
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_VOLUME, invalidOptArg=True)

            # Create volume
            try:
                create_volume(svm_name=svmName, volume_name=volumeName,  cluster_name=clusterName, volume_size=volumeSize, guarantee_space=guaranteeSpace, volume_type=volumeType, unix_permissions=unixPermissions, unix_uid=unixUID,
                              unix_gid=unixGID, export_policy=exportPolicy, snapshot_policy=snapshotPolicy, aggregate=aggregate, mountpoint=mountpoint, junction=junction, readonly=readonly,
                              print_output=True, tiering_policy=tieringPolicy, vol_dp=volDP, snaplock_type = snaplock_type)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                sys.exit(1)

        elif target in ("snapmirror-relationship", "sm","snapmirror"):
            clusterName = None
            sourceSvm = None
            targetSvm = None
            sourceVol = None
            targetVol = None
            policy = 'MirrorAllSnapshots'
            schedule = "hourly"
            volumeSize = None
            action = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hn:t:s:v:u:y:c:p:a:h", ["cluster-name=","help", "target-vol=", "target-svm=", "source-svm=", "source-vol=", "schedule=", "policy=", "action="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP)
                    sys.exit(0)
                elif opt in ("-t", "--target-svm"):
                    targetSvm = arg
                elif opt in ("-n", "--target-vol"):
                    targetVol = arg
                elif opt in ("-s", "--source-svm"):
                    sourceSvm = arg
                elif opt in ("-v", "--source-vol"):
                    sourceVol = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-c", "--schedule"):
                    schedule = arg
                elif opt in ("-p", "--policy"):
                    policy = arg
                elif opt in ("-a", "--action"):
                    action = arg

            # Check for required options
            if not targetVol or not sourceSvm or not sourceVol:
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP, invalidOptArg=True)

            if action not in [None,'resync','initialize']:
                handleInvalidCommand(helpText=HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP, invalidOptArg=True)

            # Create snapmirror
            try:
                create_snap_mirror_relationship(source_svm=sourceSvm, target_svm=targetSvm, source_vol=sourceVol, target_vol=targetVol, schedule=schedule, policy=policy,
                        cluster_name=clusterName, action=action, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action in ("delete", "del", "rm"):
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("snapshot", "snap"):
            volumeName = None
            snapshotName = None
            svmName = None
            clusterName = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hn:v:s:u:", ["cluster-name=","help", "svm=", "name=", "volume="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_DELETE_SNAPSHOT, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_DELETE_SNAPSHOT)
                    sys.exit(0)
                elif opt in ("-n", "--name"):
                    snapshotName = arg
                elif opt in ("-s", "--svm"):
                    svmName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-v", "--volume"):
                    volumeName = arg

            # Check for required options
            if not volumeName or not snapshotName:
                handleInvalidCommand(helpText=HELP_TEXT_DELETE_SNAPSHOT, invalidOptArg=True)

            # Delete snapshot
            try:
                delete_snapshot(volume_name=volumeName, svm_name = svmName, cluster_name=clusterName, snapshot_name=snapshotName, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError):
                sys.exit(1)

        elif target in ("volume", "vol"):
            volumeName = None
            svmName = None
            clusterName = None
            force = False
            deleteMirror = False
            deleteNonClone = False

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hfv:n:u:m", ["cluster-name=","help", "svm=", "name=", "force", "delete-non-clone", "delete-mirror"])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_DELETE_VOLUME, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_DELETE_VOLUME)
                    sys.exit(0)
                elif opt in ("-v", "--svm"):
                    svmName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-n", "--name"):
                    volumeName = arg
                elif opt in ("-f", "--force"):
                    force = True
                elif opt in ("-m", "--delete-mirror"):
                    deleteMirror = True
                elif opt in ("--delete-non-clone"):
                    deleteNonClone = True

            # Check for required options
            if not volumeName:
                handleInvalidCommand(helpText=HELP_TEXT_DELETE_VOLUME, invalidOptArg=True)

            # Confirm delete operation
            if not force:
                print("Warning: All data and snapshots associated with the volume will be permanently deleted.")
                while True:
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES"):
                        break
                    elif proceed in ("no", "No", "NO"):
                        sys.exit(0)
                    else:
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Delete volume
            try:
                delete_volume(volume_name=volumeName, svm_name=svmName, cluster_name=clusterName, delete_mirror=deleteMirror, delete_non_clone=deleteNonClone, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action in ("help", "h", "-h", "--help"):
        print(HELP_TEXT_STANDARD)

    elif action in ("list", "ls"):
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("cloud-sync-relationship", "cloud-sync", "cloud-sync-relationships", "cloud-syncs") :
            # Check command line options
            if len(sys.argv) > 3:
                if sys.argv[3] in ("-h", "--help"):
                    print(HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS)
                    sys.exit(0)
                else:
                    handleInvalidCommand(HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS, invalidOptArg=True)

            # List cloud sync relationships
            try:
                list_cloud_sync_relationships(print_output=True)
            except (InvalidConfigError, APIConnectionError):
                sys.exit(1)

        elif target in ("snapmirror-relationship", "snapmirror", "snapmirror-relationships", "snapmirrors","sm"):
            svmName = None
            clusterName = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hv:u:", ["cluster-name=","help", "svm="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS)
                    sys.exit(0)
                elif opt in ("-v", "--svm"):
                    svmName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg

            # List snapmirror relationships
            try:
                list_snap_mirror_relationships(print_output=True, cluster_name=clusterName)
            except (InvalidConfigError, APIConnectionError):
                sys.exit(1)

        elif target in ("snapshot", "snap", "snapshots", "snaps"):
            volumeName = None
            clusterName = None
            svmName = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hv:s:u:", ["cluster-name=","help", "volume=","svm="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_LIST_SNAPSHOTS, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help") :
                    print(HELP_TEXT_LIST_SNAPSHOTS)
                    sys.exit(0)
                elif opt in ("-v", "--volume"):
                    volumeName = arg
                elif opt in ("-s", "--svm"):
                    svmName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg

            # Check for required options
            if not volumeName:
                handleInvalidCommand(helpText=HELP_TEXT_LIST_SNAPSHOTS, invalidOptArg=True)

            # List snapsots
            try:
                list_snapshots(volume_name=volumeName, cluster_name=clusterName, svm_name=svmName, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
                sys.exit(1)

        elif target in ("volume", "vol", "volumes", "vols"):
            includeSpaceUsageDetails = False
            svmName = None
            clusterName = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hsv:u:", ["cluster-name=","help", "include-space-usage-details","svm="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_LIST_VOLUMES, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help") :
                    print(HELP_TEXT_LIST_VOLUMES)
                    sys.exit(0)
                elif opt in ("-v", "--svm") :
                    svmName = arg
                elif opt in ("-s", "--include-space-usage-details"):
                    includeSpaceUsageDetails = True
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg

            # List volumes
            try:
                list_volumes(check_local_mounts=True, include_space_usage_details=includeSpaceUsageDetails, print_output=True, svm_name=svmName, cluster_name=clusterName)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action == "mount":
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("volume", "vol"):
            volumeName = None
            svmName = None
            clusterName = None
            lifName = None
            mountpoint = None
            mount_options = None
            readonly = False

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hv:n:l:m:u:o:x", ["cluster-name=","help", "lif=","svm=", "name=", "mountpoint=", "readonly", "options="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_MOUNT_VOLUME, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_MOUNT_VOLUME)
                    sys.exit(0)
                elif opt in ("-v", "--svm"):
                    svmName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-l", "--lif"):
                    lifName = arg
                elif opt in ("-n", "--name"):
                    volumeName = arg
                elif opt in ("-m", "--mountpoint"):
                    mountpoint = arg
                elif opt in ("-o", "--options"):
                    mount_options = arg
                elif opt in ("-x", "--readonly"):
                    readonly = True

            # Check for required options
            if not volumeName:
                handleInvalidCommand(helpText=HELP_TEXT_MOUNT_VOLUME, invalidOptArg=True)

            if not mountpoint:
                handleInvalidCommand(helpText=HELP_TEXT_MOUNT_VOLUME, invalidOptArg=True)
                
            # Mount volume
            try:
                mount_volume(svm_name = svmName, cluster_name=clusterName, lif_name = lifName, volume_name=volumeName, mountpoint=mountpoint, mount_options=mount_options, readonly=readonly, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action == "unmount":
    # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("volume", "vol"):
            mountpoint = None
            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hm:", ["help", "mountpoint="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_UNMOUNT_VOLUME, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_UNMOUNT_VOLUME)
                    sys.exit(0)
                elif opt in ("-m", "--mountpoint"):
                    mountpoint = arg

            # Check for required options
            if not mountpoint:
                handleInvalidCommand(helpText=HELP_TEXT_UNMOUNT_VOLUME, invalidOptArg=True)

            # Unmount volume
            try:
                unmount_volume(mountpoint=mountpoint, print_output= True)
            except (MountOperationError):
                sys.exit(1)
        else:
            handleInvalidCommand()

    elif action in ("prepopulate"):
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("flexcache", "cache"):
            volumeName = None
            paths = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hn:p:", ["help", "name=", "paths="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_PREPOPULATE_FLEXCACHE, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_PREPOPULATE_FLEXCACHE)
                    sys.exit(0)
                elif opt in ("-n", "--name"):
                    volumeName = arg
                elif opt in ("-p", "--paths"):
                    paths = arg

            # Check for required options
            if not volumeName or not paths :
                handleInvalidCommand(helpText=HELP_TEXT_PREPOPULATE_FLEXCACHE, invalidOptArg=True)

            # Convert paths string to list
            pathsList = paths.split(",")

            # Prepopulate FlexCache
            try:
                prepopulate_flex_cache(volume_name=volumeName, paths=pathsList, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action in ("pull-from-s3", "pull-s3", "s3-pull"):
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("bucket"):
            s3Bucket = None
            s3ObjectKeyPrefix = ""
            localDirectory = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hb:p:d:e:", ["help", "bucket=", "key-prefix=", "directory="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_PULL_FROM_S3_BUCKET, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help") :
                    print(HELP_TEXT_PULL_FROM_S3_BUCKET)
                    sys.exit(0)
                elif opt in ("-b", "--bucket"):
                    s3Bucket = arg
                elif opt in ("-p", "--key-prefix"):
                    s3ObjectKeyPrefix = arg
                elif opt in ("-d", "--directory"):
                    localDirectory = arg

            # Check for required options
            if not s3Bucket or not localDirectory:
                handleInvalidCommand(helpText=HELP_TEXT_PULL_FROM_S3_BUCKET, invalidOptArg=True)

            # Push file to S3
            try:
                pull_bucket_from_s3(s3_bucket=s3Bucket, local_directory=localDirectory, s3_object_key_prefix=s3ObjectKeyPrefix, print_output=True)
            except (InvalidConfigError, APIConnectionError):
                sys.exit(1)

        elif target in ("object", "file"):
            s3Bucket = None
            s3ObjectKey = None
            localFile = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hb:k:f:", ["help", "bucket=", "key=", "file=", "extra-args="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_PULL_FROM_S3_OBJECT, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_PULL_FROM_S3_OBJECT)
                    sys.exit(0)
                elif opt in ("-b", "--bucket"):
                    s3Bucket = arg
                elif opt in ("-k", "--key"):
                    s3ObjectKey = arg
                elif opt in ("-f", "--file"):
                    localFile = arg

            # Check for required options
            if not s3Bucket or not s3ObjectKey:
                handleInvalidCommand(helpText=HELP_TEXT_PULL_FROM_S3_OBJECT, invalidOptArg=True)

            # Push file to S3
            try:
                pull_object_from_s3(s3_bucket=s3Bucket, s3_object_key=s3ObjectKey, local_file=localFile, print_output=True)
            except (InvalidConfigError, APIConnectionError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action in ("push-to-s3", "push-s3", "s3-push"):
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("directory", "dir"):
            s3Bucket = None
            s3ObjectKeyPrefix = ""
            localDirectory = None
            s3ExtraArgs = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hb:p:d:e:", ["help", "bucket=", "key-prefix=", "directory=", "extra-args="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_PUSH_TO_S3_DIRECTORY, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help") :
                    print(HELP_TEXT_PUSH_TO_S3_DIRECTORY)
                    sys.exit(0)
                elif opt in ("-b", "--bucket"):
                    s3Bucket = arg
                elif opt in ("-p", "--key-prefix"):
                    s3ObjectKeyPrefix = arg
                elif opt in ("-d", "--directory"):
                    localDirectory = arg
                elif opt in ("-e", "--extra-args"):
                    s3ExtraArgs = arg

            # Check for required options
            if not s3Bucket or not localDirectory:
                handleInvalidCommand(helpText=HELP_TEXT_PUSH_TO_S3_DIRECTORY, invalidOptArg=True)

            # Push file to S3
            try:
                push_directory_to_s3(s3_bucket=s3Bucket, local_directory=localDirectory, s3_object_key_prefix=s3ObjectKeyPrefix, s3_extra_args=s3ExtraArgs, print_output=True)
            except (InvalidConfigError, APIConnectionError):
                sys.exit(1)

        elif target in ("file"):
            s3Bucket = None
            s3ObjectKey = None
            localFile = None
            s3ExtraArgs = None

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hb:k:f:e:", ["help", "bucket=", "key=", "file=", "extra-args="])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_PUSH_TO_S3_FILE, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_PUSH_TO_S3_FILE)
                    sys.exit(0)
                elif opt in ("-b", "--bucket"):
                    s3Bucket = arg
                elif opt in ("-k", "--key"):
                    s3ObjectKey = arg
                elif opt in ("-f", "--file"):
                    localFile = arg
                elif opt in ("-e", "--extra-args"):
                    s3ExtraArgs = arg

            # Check for required options
            if not s3Bucket or not localFile:
                handleInvalidCommand(helpText=HELP_TEXT_PUSH_TO_S3_FILE, invalidOptArg=True)

            # Push file to S3
            try:
                push_file_to_s3(s3_bucket=s3Bucket, s3_object_key=s3ObjectKey, local_file=localFile, s3_extra_args=s3ExtraArgs, print_output=True)
            except (InvalidConfigError, APIConnectionError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action in ("restore"):
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("snapshot", "snap"):
            volumeName = None
            snapshotName = None
            svmName = None
            clusterName = None
            force = False

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hs:n:v:fu:", ["cluster-name=","help", "svm=", "name=", "volume=", "force"])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_RESTORE_SNAPSHOT, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_RESTORE_SNAPSHOT)
                    sys.exit(0)
                elif opt in ("-n", "--name"):
                    snapshotName = arg
                elif opt in ("-s", "--svm"):
                    svmName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-v", "--volume"):
                    volumeName = arg
                elif opt in ("-f", "--force"):
                    force = True

            # Check for required options
            if not volumeName or not snapshotName:
                handleInvalidCommand(helpText=HELP_TEXT_RESTORE_SNAPSHOT, invalidOptArg=True)

            # Confirm restore operation
            if not force:
                print("Warning: When you restore a snapshot, all subsequent snapshots are deleted.")
                while True:
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES"):
                        break
                    elif proceed in ("no", "No", "NO"):
                        sys.exit(0)
                    else:
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Restore snapshot
            try:
                restore_snapshot(volume_name=volumeName, snapshot_name=snapshotName, svm_name=svmName, cluster_name=clusterName, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError):
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action == "sync":
        # Get desired target from command line args
        target = getTarget(sys.argv)

        # Invoke desired action based on target
        if target in ("cloud-sync-relationship", "cloud-sync"):
            relationshipID = None
            waitUntilComplete = False

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hi:w", ["help", "id=", "wait"])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP)
                    sys.exit(0)
                elif opt in ("-i", "--id"):
                    relationshipID = arg
                elif opt in ("-w", "--wait"):
                    waitUntilComplete = True

            # Check for required options
            if not relationshipID:
                handleInvalidCommand(helpText=HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP, invalidOptArg=True)

            # Update cloud sync relationship
            try:
                sync_cloud_sync_relationship(relationship_id=relationshipID, wait_until_complete=waitUntilComplete, print_output=True)
            except (InvalidConfigError, APIConnectionError, CloudSyncSyncOperationError):
                sys.exit(1)

        elif target in ("snapmirror-relationship", "snapmirror"):
            uuid = None
            volumeName = None
            svmName = None
            clusterName = None
            waitUntilComplete = False

            # Get command line options
            try:
                opts, args = getopt.getopt(sys.argv[3:], "hi:wn:u:v:", ["help", "cluster-name=","svm=","name=","uuid=", "wait"])
            except Exception as err:
                print(err)
                handleInvalidCommand(helpText=HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts:
                if opt in ("-h", "--help"):
                    print(HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP)
                    sys.exit(0)
                elif opt in ("-v", "--svm"):
                    svmName = arg
                elif opt in ("-u", "--cluster-name"):
                    clusterName = arg
                elif opt in ("-n", "--name"):
                    volumeName = arg
                elif opt in ("-i", "--uuid"):
                    uuid = arg
                elif opt in ("-w", "--wait"):
                    waitUntilComplete = True

            # Check for required options
            if not uuid and not volumeName:
                handleInvalidCommand(helpText=HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP, invalidOptArg=True)

            if uuid and volumeName:
                handleInvalidCommand(helpText=HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP, invalidOptArg=True)

            # Update SnapMirror relationship
            try:
                sync_snap_mirror_relationship(uuid=uuid, svm_name=svmName, volume_name=volumeName, cluster_name=clusterName, wait_until_complete=waitUntilComplete, print_output=True)
            except (
                    InvalidConfigError, APIConnectionError, InvalidSnapMirrorParameterError,
                    SnapMirrorSyncOperationError) :
                sys.exit(1)

        else:
            handleInvalidCommand()

    elif action in ("version", "v", "-v", "--version"):
        print("NetApp DataOps Toolkit for Traditional Environments - version "
              + traditional.__version__)

    else:
        handleInvalidCommand()

