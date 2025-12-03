"""Snapshot operations for NetApp DataOps traditional environments."""

import datetime
import re
from typing import List, Dict, Any, Optional

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Volume as NetAppVolume
from netapp_ontap.resources import Snapshot as NetAppSnapshot

from netapp_dataops.logging_utils import setup_logger
from ..exceptions import (
    InvalidConfigError, 
    ConnectionTypeError, 
    APIConnectionError,
    InvalidVolumeParameterError,
    InvalidSnapshotParameterError
)
from ..core import (
    _retrieve_config, 
    _instantiate_connection, 
    _print_invalid_config_error,
    deprecated
)

logger = setup_logger(__name__)


def create_snapshot(volume_name: str, cluster_name: Optional[str] = None, svm_name: Optional[str] = None, 
                   snapshot_name: Optional[str] = None, retention_count: int = 0, retention_days: bool = False, 
                   snapmirror_label: Optional[str] = None, print_output: bool = False) -> None:
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except KeyError:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        if not snapshot_name:
            snapshot_name = "netapp_dataops"

        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
        except KeyError:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        snapshot_name_original = snapshot_name
        if not snapshot_name or int(retention_count) > 0:
            timestamp = '.'+datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S")
            snapshot_name += timestamp

        if print_output:
            logger.info("Creating snapshot '%s'.", snapshot_name)

        try:
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    logger.error("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            snapshotDict = {
                'name': snapshot_name,
                'volume': volume.to_dict()
            }
            if snapmirror_label:
                if print_output:
                    logger.info("Setting snapmirror label as: %s", snapmirror_label)
                snapshotDict['snapmirror_label'] = snapmirror_label

            snapshot = NetAppSnapshot.from_dict(snapshotDict)
            snapshot.post(poll=True)

            if print_output:
                logger.info("Snapshot created successfully.")

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
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
                        logger.error("Error: Invalid volume name.")
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
                        delete_snapshot(volume_name=volume_name, svm_name = svm, snapshot_name=snap, skip_owned=True, print_output=True)

            except NetAppRestError as err:
                if print_output:
                    logger.error("Error: ONTAP Rest API Error: %s", err)
                raise APIConnectionError(err)
    else:
        raise ConnectionTypeError()


def delete_snapshot(volume_name: str, snapshot_name: str, cluster_name: Optional[str] = None, svm_name: Optional[str] = None, 
                   skip_owned: bool = False, print_output: bool = False) -> None:
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except KeyError:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
        except KeyError:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        if print_output:
            logger.info("Deleting snapshot '%s'.", snapshot_name)

        try:
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    logger.error("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshot_name)

            if not snapshot:
                if print_output:
                    logger.error("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            if hasattr(snapshot,'owners'):
                if not skip_owned:
                    if print_output:
                        logger.error('Error: Snapshot cannot be deleted since it has owners: %s', ','.join(snapshot.owners))
                    raise InvalidSnapshotParameterError("name")
                else:
                    if print_output:
                        logger.warning('Warning: Snapshot cannot be deleted since it has owners: %s', ','.join(snapshot.owners))
                    return

            snapshot.delete(poll=True)

            if print_output:
                logger.info("Snapshot deleted successfully.")

        except NetAppRestError as err :
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def list_snapshots(volume_name: str, cluster_name: Optional[str] = None, svm_name: Optional[str] = None, print_output: bool = False) -> List[Dict[str, Any]]:
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except KeyError:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
        except KeyError:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        try:
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    logger.error("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            snapshotsList = list()
            for snapshot in NetAppSnapshot.get_collection(volume.uuid):
                snapshot.get()
                snapshotDict = {"Snapshot Name": snapshot.name, "Create Time": snapshot.create_time}
                snapshotsList.append(snapshotDict)

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if print_output:
            try:
                import pandas as pd
                from tabulate import tabulate
                snapshotsDF = pd.DataFrame.from_dict(snapshotsList, dtype="string")
                logger.info("\n%s", tabulate(snapshotsDF, showindex=False, headers=snapshotsDF.columns))
            except ImportError:
                logger.info("Snapshots retrieved successfully")
                for snap in snapshotsList:
                    logger.info(snap)

        return snapshotsList

    else:
        raise ConnectionTypeError()


def restore_snapshot(volume_name: str, snapshot_name: str, cluster_name: Optional[str] = None, svm_name: Optional[str] = None, print_output: bool = False) -> None:
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except KeyError:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    if cluster_name:
        config["hostname"] = cluster_name

    if connectionType == "ONTAP":
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
        except KeyError:
            if print_output:
                _print_invalid_config_error()
            raise InvalidConfigError()

        if print_output:
            logger.info("Restoring snapshot '%s'.", snapshot_name)

        try:
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    logger.error("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            snapshot = NetAppSnapshot.find(volume.uuid, name=snapshot_name)
            if not snapshot:
                if print_output:
                    logger.error("Error: Invalid snapshot name.")
                raise InvalidSnapshotParameterError("name")

            volume.patch(volume.uuid, **{"restore_to.snapshot.name": snapshot.name, "restore_to.snapshot.uuid": snapshot.uuid}, poll=True)
            if print_output:
                logger.info("Snapshot restored successfully.")

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


@deprecated
def createSnapshot(volumeName: str, snapshotName: str = None, printOutput: bool = False):
    """Deprecated: Use create_snapshot() instead"""
    create_snapshot(volume_name=volumeName, snapshot_name=snapshotName, print_output=printOutput)


@deprecated  
def deleteSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False):
    """Deprecated: Use delete_snapshot() instead"""
    delete_snapshot(volume_name=volumeName, snapshot_name=snapshotName, print_output=printOutput)


@deprecated
def restoreSnapshot(volumeName: str, snapshotName: str, printOutput: bool = False):
    """Deprecated: Use restore_snapshot() instead"""
    restore_snapshot(volume_name=volumeName, snapshot_name=snapshotName, print_output=printOutput)


@deprecated
def listSnapshots(volumeName: str, printOutput: bool = False) -> list:
    """Deprecated: Use list_snapshots() instead"""
    return list_snapshots(volume_name=volumeName, print_output=printOutput)
