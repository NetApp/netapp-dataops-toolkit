"""
SnapMirror operations for NetApp DataOps traditional environments.

This module contains all SnapMirror-related operations including create, sync,
and list functionality for SnapMirror relationships.
"""

import time

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import SnapmirrorRelationship as NetAppSnapmirrorRelationship
from netapp_ontap.resources import SnapmirrorTransfer as NetAppSnapmirrorTransfer
from netapp_ontap.resources import CLI as NetAppCLI
import pandas as pd
from tabulate import tabulate

from ..exceptions import (
    InvalidConfigError, 
    ConnectionTypeError, 
    APIConnectionError,
    InvalidSnapMirrorParameterError,
    SnapMirrorSyncOperationError
)
from ..core import (
    _retrieve_config, 
    _instantiate_connection, 
    _print_invalid_config_error
)
def list_snap_mirror_relationships(print_output: bool = False, cluster_name: str = None) -> list:
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

    else:
        raise ConnectionTypeError()


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


# Deprecated functions for backward compatibility
def listSnapMirrorRelationships(printOutput: bool = False) -> list:
    return list_snap_mirror_relationships(print_output=printOutput)


def syncSnapMirrorRelationship(uuid: str, waitUntilComplete: bool = False, printOutput: bool = False):
    sync_snap_mirror_relationship(uuid=uuid, wait_until_complete=waitUntilComplete, print_output=printOutput)
