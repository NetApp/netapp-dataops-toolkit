"""NetApp DataOps Toolkit for Traditional Environments import module.

This module provides the public functions a# Import FlexCache operations from storage package
from .storage.flexcache_operations import (
    prepopulate_flex_cache,
    prepopulateFlexCache
)


def clone_volume(new_volume_name: str, source_volume_name: str, cluster_name: str = None, source_snapshot_name: str = None,rted directly
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
from netapp_ontap import config as netappConfig
from netapp_ontap.error import NetAppRestError
from netapp_ontap.host_connection import HostConnection as NetAppHostConnection
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


__version__ = "2.5.0"


# Import modular operations
# Import core utilities and exceptions
from .core import (
    _retrieve_config,
    _instantiate_connection,
    _print_invalid_config_error,
    _convert_bytes_to_pretty_size,
    deprecated
)
from .exceptions import (
    InvalidConfigError,
    ConnectionTypeError,
    APIConnectionError,
    InvalidVolumeParameterError,
    InvalidSnapshotParameterError,
    MountOperationError,
    InvalidSnapMirrorParameterError,
    SnapMirrorSyncOperationError,
    CloudSyncSyncOperationError
)

# Import volume operations from storage package
from .storage.volume_operations import (
    clone_volume,
    create_volume,
    delete_volume,
    mount_volume,
    unmount_volume,
    list_volumes,
    cloneVolume,
    createVolume,
    deleteVolume,
    mountVolume,
    unmountVolume,
    listVolumes
)

# Import snapshot operations from storage package  
from .storage.snapshot_operations import (
    create_snapshot,
    delete_snapshot,
    restore_snapshot,
    list_snapshots,
    createSnapshot,
    deleteSnapshot,
    restoreSnapshot,
    listSnapshots
)

# Import SnapMirror operations from storage package
from .storage.snapmirror_operations import (
    list_snap_mirror_relationships,
    create_snap_mirror_relationship,
    sync_snap_mirror_relationship,
    listSnapMirrorRelationships,
    syncSnapMirrorRelationship
)

# Import Cloud Sync operations from cloud package
from .cloud.cloud_sync_operations import (
    list_cloud_sync_relationships,
    sync_cloud_sync_relationship,
    listCloudSyncRelationships,
    syncCloudSyncRelationship
)

# Import S3 operations from cloud package
from .cloud.s3_operations import (
    pull_bucket_from_s3,
    pull_object_from_s3,
    push_directory_to_s3,
    push_file_to_s3,
    pullBucketFromS3,
    pullObjectFromS3,
    pushDirectoryToS3,
    pushFileToS3
)

# Import FlexCache operations from storage package
from .storage.flexcache_operations import (
    prepopulate_flex_cache,
    prepopulateFlexCache
)


@deprecated
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
@deprecated
def mountVolume(volumeName: str, mountpoint: str, printOutput: bool = False) :
    mount_volume(volume_name=volumeName, mountpoint=mountpoint, print_output=printOutput)


@deprecated
@deprecated
def restoreSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False) :
    restore_snapshot(volume_name=volumeName, snapshot_name=snapshotName, print_output=printOutput)


