"""NetApp DataOps Toolkit for Traditional Environments import module.
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

# Import dataset exceptions
from .datasets.exceptions import (
    DatasetError,
    DatasetNotFoundError,
    DatasetExistsError,
    DatasetConfigError,
    DatasetVolumeError
)

# Import volume operations from ontap package
from .ontap.volume_operations import (
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

# Import snapshot operations from ontap package  
from .ontap.snapshot_operations import (
    create_snapshot,
    delete_snapshot,
    restore_snapshot,
    list_snapshots,
    createSnapshot,
    deleteSnapshot,
    restoreSnapshot,
    listSnapshots
)

# Import SnapMirror operations from ontap package
from .ontap.snapmirror_operations import (
    list_snap_mirror_relationships,
    create_snap_mirror_relationship,
    sync_snap_mirror_relationship,
    listSnapMirrorRelationships,
    syncSnapMirrorRelationship
)

# Import Cloud Sync operations from data_movement package
from .data_movement.cloud_sync_operations import (
    list_cloud_sync_relationships,
    sync_cloud_sync_relationship,
    listCloudSyncRelationships,
    syncCloudSyncRelationship
)

# Import S3 operations from data_movement package
from .data_movement.s3_operations import (
    pull_bucket_from_s3,
    pull_object_from_s3,
    push_directory_to_s3,
    push_file_to_s3,
    pullBucketFromS3,
    pullObjectFromS3,
    pushDirectoryToS3,
    pushFileToS3
)

# Import FlexCache operations from ontap package
from .ontap.flexcache_operations import (
    prepopulate_flex_cache,
    prepopulateFlexCache
)

# Import GCNV operations from gcnv package
from .gcnv.volume_operations import (
    create_volume as gcnv_create_volume,
    clone_volume as gcnv_clone_volume,
    delete_volume as gcnv_delete_volume,
    list_volumes as gcnv_list_volumes
)

from .gcnv.snapshot_operations import (
    create_snapshot as gcnv_create_snapshot,
    delete_snapshot as gcnv_delete_snapshot,
    list_snapshots as gcnv_list_snapshots
)

# Import Dataset operations from datasets package
from .datasets import (
    Dataset,
    get_datasets
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


