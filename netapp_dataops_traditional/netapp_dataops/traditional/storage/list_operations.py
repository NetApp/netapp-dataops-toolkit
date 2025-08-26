"""
List operations for NetApp DataOps traditional environments.

This module contains list operations for volumes and snapshots.
"""

import functools
import subprocess

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Volume as NetAppVolume
from netapp_ontap.resources import Snapshot as NetAppSnapshot
import pandas as pd
from tabulate import tabulate

from ..exceptions import (
    InvalidConfigError, 
    ConnectionTypeError, 
    APIConnectionError,
    InvalidVolumeParameterError
)
from ..core import (
    _retrieve_config, 
    _instantiate_connection, 
    _print_invalid_config_error,
    _convert_bytes_to_pretty_size
)


def deprecated(func):
    """
    Decorator to mark functions as deprecated.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import warnings
        warnings.warn(f"Function {func.__name__} is deprecated and will be removed in a future version.",
                     DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    return wrapper


def list_snapshots(volume_name: str, cluster_name: str = None, svm_name: str = None, print_output: bool = False) -> list:
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


def list_volumes(check_local_mounts: bool = False, include_space_usage_details: bool = False, print_output: bool = False, cluster_name: str = None, svm_name: str = None) -> list:
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
                        if nfsMountTarget:
                            for mount in mounts.split("\n") :
                                mountDetails = mount.split(" ")
                                if mountDetails[0].strip() == nfsMountTarget.strip() :
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


# Backward compatibility functions (deprecated)
@deprecated
def listSnapshots(volumeName: str, printOutput: bool = False) -> list:
    return list_snapshots(volume_name=volumeName, print_output=printOutput)


@deprecated
def listVolumes(checkLocalMounts: bool = False, includeSpaceUsageDetails: bool = False, printOutput: bool = False) -> list:
    return list_volumes(check_local_mounts=checkLocalMounts, include_space_usage_details=includeSpaceUsageDetails, print_output=printOutput)
