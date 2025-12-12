"""SnapMirror operations for NetApp DataOps traditional environments."""

import time
from typing import List, Dict, Any, Optional

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import SnapmirrorRelationship as NetAppSnapmirrorRelationship
from netapp_ontap.resources import SnapmirrorTransfer as NetAppSnapmirrorTransfer
from netapp_ontap.resources import CLI as NetAppCLI

from netapp_dataops.logging_utils import setup_logger

from ..exceptions import (
    InvalidConfigError,
    ConnectionTypeError,
    APIConnectionError,
    SnapMirrorSyncOperationError
)
from ..core import (
    _retrieve_config,
    _instantiate_connection,
    _print_invalid_config_error,
    deprecated
)

logger = setup_logger(__name__)


def list_snap_mirror_relationships(print_output: bool = False, cluster_name: Optional[str] = None) -> List[Dict[str, Any]]:
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
            # Retrieve all relationships for which destination is on current cluster
            destinationRelationships = NetAppSnapmirrorRelationship.get_collection()

            # Do not retrieve relationships for which source is on current cluster
            # Note: Uncomment below line to retrieve all relationships for which source is on current cluster, then add sourceRelationships to for loop
            # sourceRelationships = NetAppSnapmirrorRelationship.get_collection(list_destinations_only=True)

            # Construct list of relationships
            relationshipsList = list()
            for relationship in destinationRelationships:
                try:
                    relationship.get()
                except NetAppRestError as err:
                    relationship.get(list_destinations_only=True)

                if hasattr(relationship.source, "cluster"):
                    sourceCluster = relationship.source.cluster.name
                else:
                    sourceCluster = "user's cluster"
                if hasattr(relationship.destination, "cluster"):
                    destinationCluster = relationship.destination.cluster.name
                else:
                    destinationCluster = "user's cluster"

                if hasattr(relationship, "transfer"):
                    transferState = relationship.transfer.state
                else:
                    transferState = None

                if hasattr(relationship, "healthy"):
                    healthy = relationship.healthy
                else:
                    healthy = "unknown"

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

                relationshipsList.append(relationshipDict)

        except NetAppRestError as err:
            if print_output:
                print("Error: ONTAP Rest API Error: ", err)
            raise APIConnectionError(err)

        if print_output:
            try:
                import pandas as pd
                from tabulate import tabulate
                relationshipsDF = pd.DataFrame.from_dict(relationshipsList, dtype="string")
                logger.info("\n%s", tabulate(relationshipsDF, showindex=False, headers=relationshipsDF.columns))
            except ImportError:
                logger.info("SnapMirror relationships retrieved successfully")
                for rel in relationshipsList:
                    logger.info(rel)

        return relationshipsList

    else:
        raise ConnectionTypeError()


def create_snap_mirror_relationship(source_svm: str, source_vol: str, target_vol: str, target_svm: Optional[str] = None, 
                                    cluster_name: Optional[str] = None, schedule: str = '', policy: str = 'MirrorAllSnapshots', 
                                    action: Optional[str] = None, print_output: bool = False) -> None:
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

        svm = config["svm"]
        if not target_svm:
            target_svm = svm

        try:
            uuid = None
            snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": target_svm+":"+target_vol})
            for rel in snapmirror_relationship:
                try:
                    rel.get()
                    uuid = rel.uuid
                except NetAppRestError as err:
                    if print_output:
                        logger.error("Error: ONTAP Rest API Error: %s", err)
            if uuid:
                if print_output:
                    logger.error("Error: relationship already exists: %s:%s", target_svm, target_vol)
                raise InvalidConfigError()
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        try:
            newRelationDict = {
                "source": {
                    "path": source_svm+":"+source_vol
                },
                "destination": {
                    "path": target_svm+":"+target_vol
                }
            }

            if print_output:
                logger.info("Creating snapmirror relationship: %s:%s -> %s:%s", source_svm, source_vol, target_svm, target_vol)
            newRelationship = NetAppSnapmirrorRelationship.from_dict(newRelationDict)
            newRelationship.post(poll=True, poll_timeout=120)
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        try:
            if print_output:
                logger.info("Setting snapmirror policy as: %s schedule: %s", policy, schedule)
                response = NetAppCLI().execute("snapmirror modify",destination_path=target_svm+":"+target_vol,body={"policy": policy, "schedule":schedule})
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        try:
            uuid = None
            relation = None
            snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": target_svm+":"+target_vol})
            for relation in snapmirror_relationship:
                try:
                    relation.get()
                    uuid = relation.uuid
                except NetAppRestError as err:
                    if print_output:
                        logger.error("Error: ONTAP Rest API Error: %s", err)
                    raise APIConnectionError(err)
            if not uuid:
                if print_output:
                    logger.error("Error: relationship was not created: %s:%s", target_svm, target_vol)
                raise InvalidConfigError()
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if action in ["resync","initialize"]:
            try:
                if print_output:
                    logger.info("Setting state to snapmirrored, action: %s", action)
                patchRelation = NetAppSnapmirrorRelationship(uuid=uuid)
                patchRelation.state = "snapmirrored"
                patchRelation.patch(poll=True, poll_timeout=120)
            except NetAppRestError as err:
                if print_output:
                    logger.error("Error: ONTAP Rest API Error: %s", err)
                raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def sync_snap_mirror_relationship(uuid: Optional[str] = None, svm_name: Optional[str] = None, volume_name: Optional[str] = None, 
                                 cluster_name: Optional[str] = None, wait_until_complete: bool = False, print_output: bool = False) -> None:
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

        if volume_name:
            svm = config["svm"]
            if svm_name:
                svm = svm_name

            snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": svm+":"+volume_name})
            for rel in snapmirror_relationship:
                try:
                    rel.get()
                    uuid = rel.uuid
                except NetAppRestError as err:
                    if print_output:
                        logger.error("Error: ONTAP Rest API Error: %s", err)
            if not uuid:
                snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": svm+":"})
                for rel in snapmirror_relationship:
                    try:
                        rel.get()
                        uuid = rel.uuid
                    except NetAppRestError as err:
                        if print_output:
                            logger.error("Error: ONTAP Rest API Error: %s", err)
                    if uuid:
                        if print_output:
                            logger.info("volume is part of svm-dr relationship: %s:", svm)

        if not uuid:
            if print_output:
                logger.error("Error: relationship could not be found.")
            raise SnapMirrorSyncOperationError("not found")

        if print_output:
            logger.info("Triggering sync operation for SnapMirror relationship (UUID = %s).", uuid)

        try:
            transfer = NetAppSnapmirrorTransfer(uuid)
            transfer.post(poll=True)
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if print_output:
            logger.info("Sync operation successfully triggered.")

        if wait_until_complete:
            logger.info("Waiting for sync operation to complete.")
            logger.info("Status check will be performed in 10 seconds...")
            time.sleep(10)

            while True:
                relationship = NetAppSnapmirrorRelationship.find(uuid=uuid)
                relationship.get()

                transferState = relationship.transfer.state if hasattr(relationship, "transfer") else None

                if (not transferState) or (transferState == "success"):
                    healthy = relationship.healthy
                    if healthy:
                        if print_output:
                            logger.info("Success: Sync operation is complete.")
                        break
                    else:
                        if print_output:
                            logger.error("Error: Relationship is not healthy. Access ONTAP System Manager for details.")
                        raise SnapMirrorSyncOperationError("not healthy")
                elif transferState != "transferring":
                    if print_output:
                        logger.error("Error: Unknown sync operation status (%s) returned by ONTAP API.", transferState)
                    raise SnapMirrorSyncOperationError(transferState)
                else:
                    if print_output:
                        logger.info("Sync operation is not yet complete. Status: %s", transferState)
                        logger.info("Checking again in 10 seconds...")

                time.sleep(10)

    else:
        raise ConnectionTypeError()


@deprecated
def listSnapMirrorRelationships(printOutput: bool = False) -> list:
    return list_snap_mirror_relationships(print_output=printOutput)


@deprecated
def syncSnapMirrorRelationship(uuid: str, waitUntilComplete: bool = False, printOutput: bool = False):
    sync_snap_mirror_relationship(uuid=uuid, wait_until_complete=waitUntilComplete, print_output=printOutput)
