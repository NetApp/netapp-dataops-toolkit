"""Volume operations for NetApp DataOps traditional environments."""

import os
import re
import subprocess

from netapp_ontap.error import NetAppRestError
from netapp_ontap.resources import Volume as NetAppVolume
from netapp_ontap.resources import Snapshot as NetAppSnapshot
from netapp_ontap.resources import ExportPolicy as NetAppExportPolicy
from netapp_ontap.resources import SnapshotPolicy as NetAppSnapshotPolicy
from netapp_ontap.resources import CLI as NetAppCLI

from netapp_dataops.logging_utils import setup_logger
from ..exceptions import (
    InvalidConfigError, 
    ConnectionTypeError, 
    APIConnectionError,
    InvalidVolumeParameterError,
    InvalidSnapshotParameterError,
    MountOperationError
)
from ..core import (
    _retrieve_config, 
    _instantiate_connection, 
    _print_invalid_config_error,
    _convert_bytes_to_pretty_size,
    deprecated
)

logger = setup_logger(__name__)


def clone_volume(new_volume_name: str, source_volume_name: str, cluster_name: str = None, source_snapshot_name: str = None,
                 source_svm: str = None, target_svm: str = None, export_hosts: str = None, export_policy: str = None, split: bool = False,
                 unix_uid: str = None, unix_gid: str = None, mountpoint: str = None, junction: str= None, readonly: bool = False,
                 snapshot_policy: str = None, refresh: bool = False, svm_dr_unprotect: bool = False, print_output: bool = False):
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
            sourcesvm = config["svm"]
            if source_svm:
                sourcesvm = source_svm

            targetsvm = sourcesvm
            if target_svm:
                targetsvm = target_svm

            if not unix_uid:
                unix_uid = config["defaultUnixUID"]
            if not unix_gid:
                unix_gid = config["defaultUnixGID"]

        except Exception as e:
            if print_output:
                logger.info(e)
                _print_invalid_config_error()
            raise InvalidConfigError()

        try:
            unix_uid = int(unix_uid)
        except KeyError:
            if print_output:
                logger.error("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        try:
            unix_gid = int(unix_gid)
        except KeyError:
            if print_output:
                logger.error("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        #check if clone volume already exists
        try:
            currentVolume = NetAppVolume.find(name=new_volume_name, svm=targetsvm)
            if currentVolume and not refresh:
                if print_output:
                    logger.error("Error: clone:"+new_volume_name+" already exists.")
                raise InvalidVolumeParameterError("name")

            #for refresh we want to keep the existing policy
            if currentVolume and refresh and not export_policy and not export_hosts:
                export_policy = currentVolume.nas.export_policy.name

            # if refresh and not provided new snapshot_policy
            if currentVolume and refresh and not snapshot_policy:
                snapshot_policy = currentVolume.snapshot_policy.name

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        #delete existing clone when refresh
        try:
            if currentVolume and refresh:
                if "CLONENAME:" in currentVolume.comment:
                    delete_volume(volume_name=new_volume_name, cluster_name=cluster_name, svm_name=target_svm, delete_mirror=True, print_output=True)
                else:
                    if print_output:
                        logger.error("Error: refresh clone is only supported when existing clone created using the tool (based on volume comment)")
                    raise InvalidVolumeParameterError("name")
        except KeyError:
            logger.error("Error: could not delete previous clone")
            raise InvalidVolumeParameterError("name")

        try:
            if not snapshot_policy :
                snapshot_policy = config["defaultSnapshotPolicy"]
        except KeyError:
            logger.error("Error: default snapshot policy could not be found in config file")
            raise InvalidVolumeParameterError("name")

        # check export policies
        try:
            if not export_policy and not export_hosts:
                export_policy = config["defaultExportPolicy"]
            elif export_policy:
                currentExportPolicy = NetAppExportPolicy.find(name=export_policy, svm=targetsvm)
                if not currentExportPolicy:
                    if print_output:
                        logger.error("Error: export policy:"+export_policy+" dones not exists.")
                    raise InvalidVolumeParameterError("name")
            elif export_hosts:
                export_policy = "netapp_dataops_"+new_volume_name
                currentExportPolicy = NetAppExportPolicy.find(name=export_policy, svm=targetsvm)
                if currentExportPolicy:
                    currentExportPolicy.delete()
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        #exists check if snapshot-policy
        try:
            snapshotPoliciesDetails  = NetAppSnapshotPolicy.get_collection(**{"name":snapshot_policy})
            clusterSnapshotPolicy = False
            svmSnapshotPolicy = False
            for snapshotPolicyDetails in snapshotPoliciesDetails:
                if str(snapshotPolicyDetails.name) == snapshot_policy:
                    try:
                        if str(snapshotPolicyDetails.svm.name) == targetsvm:
                            svmSnapshotPolicy = True
                    except KeyError:
                        clusterSnapshotPolicy = True

            if not clusterSnapshotPolicy and not svmSnapshotPolicy:
                if print_output:
                    logger.error("Error: snapshot-policy:"+snapshot_policy+" could not be found")
                raise InvalidVolumeParameterError("snapshot_policy")
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        # Create volume
        if print_output:
            logger.info("Creating clone volume '" + targetsvm+':'+new_volume_name + "' from source volume '" + sourcesvm+':'+source_volume_name + "'.")

        try:
            # Retrieve source volume
            sourceVolume = NetAppVolume.find(name=source_volume_name, svm=sourcesvm)
            if not sourceVolume:
                if print_output:
                    logger.error("Error: Invalid source volume name.")
                raise InvalidVolumeParameterError("name")

            # Create option to choose junction path.
            if junction:
                junction=junction
            else:
                junction = "/"+new_volume_name

            # Construct dict representing new volume
            newVolumeDict = {
                "name": new_volume_name,
                "svm": {"name": targetsvm},
                "nas": {
                    "path": junction
                },
                "clone": {
                    "is_flexclone": True,
                    "parent_svm": {
                        #"name": sourceVolume.svm.name,
                        "name": sourcesvm,
                        #"uuid": sourceVolume.svm.uuid
                    },
                    "parent_volume": {
                        "name": sourceVolume.name,
                        "uuid": sourceVolume.uuid
                    }
                }
            }

            if unix_uid != 0:
                newVolumeDict["nas"]["uid"] = unix_uid
            else:
                if print_output:
                    logger.warning("Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.")
            if unix_gid != 0:
                newVolumeDict["nas"]["gid"] = unix_gid
            else:
                if print_output:
                    logger.warning("Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.")

            # Add source snapshot details to volume dict if specified
            if source_snapshot_name and not source_snapshot_name.endswith("*"):
                # Retrieve source snapshot
                sourceSnapshot = NetAppSnapshot.find(sourceVolume.uuid, name=source_snapshot_name)
                if not sourceSnapshot:
                    if print_output:
                        logger.error("Error: Invalid source snapshot name.")
                    raise InvalidSnapshotParameterError("name")


                # Append source snapshot details to volume dict
                newVolumeDict["clone"]["parent_snapshot"] = {
                    "name": sourceSnapshot.name,
                    "uuid": sourceSnapshot.uuid
                }

            if source_snapshot_name and source_snapshot_name.endswith("*"):
                source_snapshot_prefix = source_snapshot_name[:-1]
                latest_source_snapshot = None
                latest_source_snapshot_uuid = None

                # Retrieve all source snapshot from last to 1st
                for snapshot in NetAppSnapshot.get_collection(sourceVolume.uuid):
                    snapshot.get()
                    if snapshot.name.startswith(source_snapshot_prefix):
                        latest_source_snapshot = snapshot.name
                        latest_source_snapshot_uuid = snapshot.uuid

                if not latest_source_snapshot:
                    if print_output:
                        logger.error("Error: Could not find snapshot prefixed by '"+source_snapshot_prefix+"'.")
                    raise InvalidSnapshotParameterError("name")
                # Append source snapshot details to volume dict
                newVolumeDict["clone"]["parent_snapshot"] = {
                    "name": latest_source_snapshot,
                    "uuid": latest_source_snapshot_uuid
                }
                logger.info("Snapshot '" + latest_source_snapshot+ "' will be used to create the clone.")

            # set clone volume commnet parameter
            comment = 'PARENTSVM:'+sourcesvm+',PARENTVOL:'+newVolumeDict["clone"]["parent_volume"]["name"]+',CLONESVM:'+targetsvm+',CLONENAME:'+newVolumeDict["name"]
            if source_snapshot_name: comment += ' SNAP:'+newVolumeDict["clone"]["parent_snapshot"]["name"]
            comment += " netapp-dataops"

            newVolumeDict["comment"] = comment

            # Create new volume clone
            newVolume = NetAppVolume.from_dict(newVolumeDict)
            newVolume.post(poll=True, poll_timeout=120)
            if print_output:
                logger.info("Clone volume created successfully.")

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if svm_dr_unprotect:
            try:
                if print_output:
                    logger.info("Disabling svm-dr protection")
                response = NetAppCLI().execute("volume modify",vserver=targetsvm,volume=new_volume_name,body={"vserver_dr_protection": "unprotected"})
            except NetAppRestError as err:
                if "volume is not part of a Vserver DR configuration" in str(err):
                    if print_output:
                        logger.warning("Warning: could not disable svm-dr-protection since volume is not protected using svm-dr")
                else:
                    if print_output:
                        logger.error("Error: ONTAP Rest API Error: %s", err)
                    raise APIConnectionError(err)

        #create custom export policy if needed
        if export_hosts:
            try:
                if print_output:
                    logger.info("Creating export-policy:"+export_policy)
                # Construct dict representing new export policy
                newExportPolicyDict = {
                    "name" : export_policy,
                    "svm": {"name": targetsvm},
                    "rules": []
                }
                for client in export_hosts.split(":"):
                    newExportPolicyDict['rules'].append({ "clients": [{"match": client }], "ro_rule": ["sys"], "rw_rule": ["sys"], "superuser": ["sys"]})

                # Create new export policy
                newExportPolicy = NetAppExportPolicy.from_dict(newExportPolicyDict)
                newExportPolicy.post(poll=True, poll_timeout=120)

            except NetAppRestError as err:
                if print_output:
                    logger.error("Error: ONTAP Rest API Error: %s", err)
                raise APIConnectionError(err)

        #set export policy and snapshot policy
        try:
            if print_output:
                logger.info("Setting export-policy:"+export_policy+ " snapshot-policy:"+snapshot_policy)
            volumeDetails = NetAppVolume.find(name=new_volume_name, svm=targetsvm)
            updatedVolumeDetails = NetAppVolume(uuid=volumeDetails.uuid)
            updatedVolumeDetails.nas = {"export_policy": {"name": export_policy}}
            updatedVolumeDetails.snapshot_policy = {"name": snapshot_policy}
            updatedVolumeDetails.patch(poll=True, poll_timeout=120)
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        #split clone
        try:
            if split:
                if print_output:
                    logger.info("Splitting clone")
                volumeDetails = NetAppVolume.find(name=new_volume_name, svm=targetsvm)
                #get volume details
                updatedVolumeDetails = NetAppVolume(uuid=volumeDetails.uuid)
                updatedVolumeDetails.clone = {"split_initiated": True}
                updatedVolumeDetails.patch()

        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        # Optionally mount newly created volume
        if mountpoint:
            try:
                mount_volume(volume_name=new_volume_name, svm_name=targetsvm, mountpoint=mountpoint, readonly=readonly, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                if print_output:
                    logger.error("Error: Error mounting clone volume.")
                raise

    else:
        raise ConnectionTypeError()


def create_volume(volume_name: str, volume_size: str, guarantee_space: bool = False, cluster_name: str = None, svm_name: str = None,
                  volume_type: str = None, unix_permissions: str = None,
                  unix_uid: str = None, unix_gid: str = None, export_policy: str = None, snaplock_type: str = None,
                  snapshot_policy: str = None, aggregate: str = None, mountpoint: str = None, junction: str = None, readonly: bool = False,
                  print_output: bool = False, tiering_policy: str = None, vol_dp: bool = False):
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
        # Instantiate connection to ONTAP cluster
        try:
            _instantiate_connection(config=config, connectionType=connectionType, print_output=print_output)
        except InvalidConfigError:
            raise

        # Retrieve values from config file if not passed into function
        try:
            svm = config["svm"]
            if svm_name:
                svm = svm_name
            if not volume_type :
                volume_type = config["defaultVolumeType"]
            if not unix_permissions :
                unix_permissions = config["defaultUnixPermissions"]
            if not unix_uid :
                unix_uid = config["defaultUnixUID"]
            if not unix_gid :
                unix_gid = config["defaultUnixGID"]
            if not export_policy :
                export_policy = config["defaultExportPolicy"]
            if not snapshot_policy :
                snapshot_policy = config["defaultSnapshotPolicy"]
            if not aggregate and volume_type == 'flexvol' :
                aggregate = config["defaultAggregate"]
        except KeyError:
            if print_output :
                _print_invalid_config_error()
            raise InvalidConfigError()

        # Check volume type for validity
        if volume_type not in ("flexvol", "flexgroup"):
            if print_output:
                logger.error("Error: Invalid volume type specified. Acceptable values are 'flexvol' and 'flexgroup'.")
            raise InvalidVolumeParameterError("size")

        # Check unix permissions for validity
        if not re.search("^0[0-7]{3}", unix_permissions):
            if print_output:
                logger.error("Error: Invalid unix permissions specified. Acceptable values are '0777', '0755', '0744', etc.")
            raise InvalidVolumeParameterError("unixPermissions")

        # Check unix uid for validity
        try:
            unix_uid = int(unix_uid)
        except KeyError:
            if print_output :
                logger.error("Error: Invalid unix uid specified. Value be an integer. Example: '0' for root user.")
            raise InvalidVolumeParameterError("unixUID")

        # Check unix gid for validity
        try:
            unix_gid = int(unix_gid)
        except KeyError:
            if print_output:
                logger.error("Error: Invalid unix gid specified. Value must be an integer. Example: '0' for root group.")
            raise InvalidVolumeParameterError("unixGID")

        # Convert volume size to Bytes
        if re.search("^[0-9]+MB$", volume_size):
            # Convert from MB to Bytes
            volumeSizeBytes = int(volume_size[:len(volume_size)-2]) * 1024**2
        elif re.search("^[0-9]+GB$", volume_size):
            # Convert from GB to Bytes
            volumeSizeBytes = int(volume_size[:len(volume_size)-2]) * 1024**3
        elif re.search("^[0-9]+TB$", volume_size):
            # Convert from TB to Bytes
            volumeSizeBytes = int(volume_size[:len(volume_size)-2]) * 1024**4
        else :
            if print_output:
                logger.error("Error: Invalid volume size specified. Acceptable values are '1024MB', '100GB', '10TB', etc.")
            raise InvalidVolumeParameterError("size")
		
        # Create option to choose snaplock type
        if snaplock_type not in ['compliance', 'enterprise', None]:
            if print_output:
                logger.error("Error: Invalid snaplock volume type specified. Value must be either 'compliance' or 'enterprise'")
            raise InvalidVolumeParameterError("snaplockVolume")
            
        # Create option to choose junction path.
        if junction:
            junction=junction
        else:
            junction = "/"+volume_name


        #check tiering policy
        if not tiering_policy in ['none','auto','snapshot-only','all', None]:
            if print_output:
                logger.error("Error: tiering policy can be: none,auto,snapshot-only or all")
            raise InvalidVolumeParameterError("tieringPolicy")

        #vol dp type
        if vol_dp:
            # Create dict representing volume of type dp
            volumeDict = {
                "name": volume_name,
                "comment": "netapp-dataops",
                "svm": {"name": svm},
                "size": volumeSizeBytes,
                "style": volume_type,
                "type": 'dp'
            }
        else:
            # Create dict representing volume
            volumeDict = {
                "name": volume_name,
                "comment": "netapp-dataops",
                "svm": {"name": svm},
                "size": volumeSizeBytes,
                "style": volume_type,
                "nas": {
                    "path": junction,
                    "export_policy": {"name": export_policy},
                    "security_style": "unix",
                    "unix_permissions": unix_permissions,
                    "uid": unix_uid,
                    "gid": unix_gid
                },
                "snapshot_policy": {"name": snapshot_policy},
            }

        # Set space guarantee field
        if guarantee_space:
            volumeDict["guarantee"] = {"type": "volume"}
        else:
            volumeDict["guarantee"] = {"type": "none"}

        # If flexvol -> set aggregate field
        if volume_type == "flexvol":
            volumeDict["aggregates"] = [{'name': aggregate}]
        else:
            if aggregate:
                volumeDict["aggregates"] = []
                for aggr in aggregate.split(','):
                    volumeDict["aggregates"].append({'name': aggr})
                    
        # if snaplock type is valid
        if snaplock_type:
            volumeDict['snaplock'] = {"type": snaplock_type}
            
        #if tiering policy provided
        if tiering_policy:
            volumeDict['tiering'] = {'policy': tiering_policy}

        # Create volume
        if print_output:
            logger.info("Creating volume '" + volume_name + "' on svm '" + svm + "'")
        try:
            volume = NetAppVolume.from_dict(volumeDict)
            volume.post(poll=True)
            if print_output:
                logger.info("Volume created successfully.")
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        # Optionally mount newly created volume
        if mountpoint:
            try:
                mount_volume(volume_name=volume_name, svm_name=svm, mountpoint=mountpoint, readonly=readonly, print_output=True)
            except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
                if print_output:
                    logger.error("Error: Error mounting volume.")
                raise

    else:
        raise ConnectionTypeError()


# Need to declare here so clone_volume can call it - will be implemented in next step
def delete_volume(volume_name: str, cluster_name: str = None, svm_name: str = None, delete_mirror: bool = False,
                delete_non_clone: bool = False, print_output: bool = False):
    # Retrieve config details from config file
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
        except KeyError:
            if print_output :
                _print_invalid_config_error()
            raise InvalidConfigError()
            
        try:
            # Retrieve volume
            volume = NetAppVolume.find(name=volume_name, svm=svm)
            if not volume:
                if print_output:
                    logger.error("Error: Invalid volume name.")
                raise InvalidVolumeParameterError("name")

            if not "CLONENAME:" in volume.comment and not delete_non_clone:
                if print_output:
                    logger.error("Error: volume is not a clone created by this tool. add --delete-non-clone to delete it")
                raise InvalidVolumeParameterError("delete-non-clone")
        except NetAppRestError as err:
            if print_output:
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)


        if delete_mirror:
            #check if this volume has snapmirror destination relationship
            uuid = None
            try:
                from netapp_ontap.resources import SnapmirrorRelationship as NetAppSnapmirrorRelationship
                snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(**{"destination.path": svm+":"+volume_name})
                for rel in snapmirror_relationship:
                    # Retrieve relationship details
                    rel.get()
                    uuid = rel.uuid
            except NetAppRestError as err:
                if print_output:
                    logger.error("Error: ONTAP Rest API Error: %s", err)

            if uuid:
                if print_output:
                    logger.info("Deleting snapmirror relationship: "+svm+":"+volume_name)
                try:
                    deleteRelation = NetAppSnapmirrorRelationship(uuid=uuid)
                    deleteRelation.delete(poll=True, poll_timeout=120)
                except NetAppRestError as err:
                    if print_output:
                        logger.error("Error: ONTAP Rest API Error: %s", err)

            #check if this volume has snapmirror destination relationship
            uuid = None
            try:
                snapmirror_relationship = NetAppSnapmirrorRelationship.get_collection(list_destinations_only=True,**{"source.path": svm+":"+volume_name})
                for rel in snapmirror_relationship:
                    # Retrieve relationship details
                    rel.get(list_destinations_only=True)
                    uuid = rel.uuid
                    if print_output:
                        logger.info("release relationship: "+rel.source.path+" -> "+rel.destination.path)
                    deleteRelation = NetAppSnapmirrorRelationship(uuid=uuid)
                    deleteRelation.delete(poll=True, poll_timeout=120,source_only=True)
            except NetAppRestError as err:
                if print_output:
                    logger.error("Error: ONTAP Rest API Error: %s", err)

        #Unmount volume and skip if not sudo or not locally mounted
        try:
            volumes = list_volumes(check_local_mounts=True)
            for localmount in volumes:
                if localmount["Volume Name"] == volume_name:
                    x=localmount["Local Mountpoint"]
                    if x == "":
                        break
                    elif x != "":
                        if os.getuid() != 0:
                            logger.warning("Warning: Volume was not unmounted. You need to have root privileges to run unmount command.")
                            break
                        else:
                            try:
                                unmount = unmount_volume(mountpoint=x)
                            except (InvalidConfigError, APIConnectionError):
                                if print_output:
                                    logger.error("Error: unmounting volume.")
                                    raise MountOperationError(err)

        except (InvalidConfigError, APIConnectionError):
           if print_output:
                logger.error("Error: volume retrieval failed for unmount operation.")
                raise

        try:
            if print_output:
                logger.info("Deleting volume '" + svm+':'+volume_name + "'.")
            # Delete volume
            volume.delete(poll=True)

            if print_output:
                logger.info("Volume deleted successfully.")

        except NetAppRestError as err:
            if print_output:
                if "You must delete the SnapMirror relationships before" in str(err):
                    logger.error("Error: volume is snapmirror destination. add --delete-mirror to delete snapmirror relationship before deleting the volume")
                elif "the source endpoint of one or more SnapMirror relationships" in str(err):
                    logger.error("Error: volume is snapmirror source. add --delete-mirror to release snapmirror relationship before deleting the volume")
                else:
                    logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

    else:
        raise ConnectionTypeError()


def mount_volume(volume_name: str, mountpoint: str, cluster_name: str = None, svm_name: str = None, mount_options: str = None, lif_name: str = None, readonly: bool = False, print_output: bool = False):
    nfsMountTarget = None

    svm = None
    try:
        config = _retrieve_config(print_output=print_output)
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

    if cluster_name:
        config["hostname"] = cluster_name

    # Retrieve list of volumes
    try:
        volumes = list_volumes(check_local_mounts=True, svm_name = svm)
    except (InvalidConfigError, APIConnectionError):
        if print_output:
            logger.error("Error: Error retrieving NFS mount target for volume.")
        raise

    # Retrieve NFS mount target for volume, and check that no volume is currently mounted at specified mountpoint
    for volume in volumes:
        # Check mountpoint
        if mountpoint == volume["Local Mountpoint"]:
            if print_output:
                logger.error("Error: Volume '" + volume["Volume Name"] + "' is already mounted at '" + mountpoint + "'.")
            raise MountOperationError("Another volume mounted at mountpoint")

        if volume_name == volume["Volume Name"]:
            # Retrieve NFS mount target
            nfsMountTarget = volume["NFS Mount Target"]
            nfsMountTarget = nfsMountTarget.strip()

    # Raise error if invalid volume name was entered
    if not nfsMountTarget:
        if print_output:
            logger.error("Error: Invalid volume name specified.")
        raise InvalidVolumeParameterError("name")

    try:
        if lif_name:
            nfsMountTarget = lif_name+':'+nfsMountTarget.split(':')[1]
    except KeyError:
        if print_output:
            logger.error("Error: Error retrieving NFS mount target for volume.")
        raise


    # Print message describing action to be understaken
    if print_output:
        if readonly:
            logger.info("Mounting volume '" + svm+':'+volume_name + "' as '"+nfsMountTarget+"' at '" + mountpoint + "' as read-only.")
        else:
            logger.info("Mounting volume '" + svm+':'+volume_name + "' as '"+nfsMountTarget+"' at '" + mountpoint + "'.")

    # Create mountpoint if it doesn't already exist
    mountpoint = os.path.expanduser(mountpoint)
    try:
        os.mkdir(mountpoint)
    except FileExistsError:
        pass

    # Mount volume
    mount_cmd_opts = []

    if readonly:
        mount_cmd_opts.append('-o')
        mount_cmd_opts.append('ro')
        if mount_options:
            mount_cmd_opts.remove('ro')
            mount_cmd_opts.append('ro'+','+mount_options)
    elif mount_options:
        mount_cmd_opts.append('-o')
        mount_cmd_opts.append(mount_options)
    mount_cmd = ['mount'] + mount_cmd_opts + [nfsMountTarget, mountpoint]

    if os.getuid() != 0:
        mount_cmd_opts_str = ""
        for item in mount_cmd_opts :
            if item == "-o" :
                continue
            mount_cmd_opts_str = mount_cmd_opts_str + item + ","
        mount_cmd_opts_str = mount_cmd_opts_str[:-1]
        if mount_cmd_opts_str:
            import sys
            sys.exit("You need to have root privileges to run mount command."
                "\nTo mount the volume run the following command as root:"
                "\n"+ "mount -o "+ mount_cmd_opts_str+ " " + nfsMountTarget + " " + mountpoint)
        else:
            import sys
            sys.exit("You need to have root privileges to run mount command."
                "\nTo mount the volume run the following command as root:"
                "\n"+ "mount"+ mount_cmd_opts_str+ " " + nfsMountTarget + " " + mountpoint)

    try:
        subprocess.check_call(mount_cmd)
        if print_output:
            logger.info("Volume mounted successfully.")
    except subprocess.CalledProcessError as err:
        if print_output:
            logger.error("Error: Error running mount command: ", err)
        raise MountOperationError(err)


def unmount_volume(mountpoint: str, print_output: bool = False):
    # Print message describing action to be understaken
    if print_output:
        logger.info("Unmounting volume at '" + mountpoint + "'.")

    # Un-mount volume
    try:
        subprocess.check_call(['umount', mountpoint])
        if print_output:
            logger.info("Volume unmounted successfully.")
    except subprocess.CalledProcessError as err:
        if print_output:
            logger.error("Error: Error running unmount command: ", err)
        raise MountOperationError(err)


def list_volumes(check_local_mounts: bool = False, include_space_usage_details: bool = False, print_output: bool = False, cluster_name: str = None, svm_name: str = None) -> list:
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        connectionType = config["connectionType"]
    except KeyError:
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

                # # Include all vols except for SVM root vol
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
                    except (AttributeError, KeyError):
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
                logger.error("Error: ONTAP Rest API Error: %s", err)
            raise APIConnectionError(err)

        if print_output:
            try:
                import pandas as pd
                from tabulate import tabulate
                volumesDF = pd.DataFrame.from_dict(volumesList, dtype="string")
                logger.info("\n%s", tabulate(volumesDF, showindex=False, headers=volumesDF.columns))
            except ImportError:
                logger.info("Volumes retrieved successfully")
                for vol in volumesList:
                    logger.info(vol)
            
        return volumesList
      
    else:
        raise ConnectionTypeError()


# Backward compatibility functions (deprecated)
@deprecated
def cloneVolume(newVolumeName: str, sourceVolumeName: str, sourceSnapshotName: str = None, unixUID: str = None, unixGID: str = None, mountpoint: str = None, printOutput: bool = False):
    clone_volume(new_volume_name=newVolumeName, source_volume_name=sourceVolumeName, source_snapshot_name=sourceSnapshotName,
                unix_uid=unixUID, unix_gid=unixGID, mountpoint=mountpoint, print_output=printOutput)


@deprecated
def createVolume(volumeName: str, volumeSize: str, guaranteeSpace: bool = False, volumeType: str = "flexvol", unixPermissions: str = "0777", unixUID: str = "0", unixGID: str = "0", exportPolicy: str = "default", snapshotPolicy: str = "none", aggregate: str = None, mountpoint: str = None, printOutput: bool = False):
    create_volume(volume_name=volumeName, volume_size=volumeSize, guarantee_space=guaranteeSpace, volume_type=volumeType, unix_permissions=unixPermissions, unix_uid=unixUID,
                 unix_gid=unixGID, export_policy=exportPolicy, snapshot_policy=snapshotPolicy, aggregate=aggregate, mountpoint=mountpoint, print_output=printOutput)


@deprecated
def deleteVolume(volumeName: str, printOutput: bool = False):
    delete_volume(volume_name=volumeName, print_output=printOutput)


@deprecated
def mountVolume(volumeName: str, mountpoint: str, printOutput: bool = False):
    mount_volume(volume_name=volumeName, mountpoint=mountpoint, print_output=printOutput)


@deprecated
def unmountVolume(mountpoint: str, printOutput: bool = False):
    unmount_volume(mountpoint=mountpoint, print_output=printOutput)


@deprecated
def listVolumes(checkLocalMounts: bool = False, includeSpaceUsageDetails: bool = False, printOutput: bool = False) -> list:
    return list_volumes(check_local_mounts=checkLocalMounts, include_space_usage_details=includeSpaceUsageDetails, print_output=printOutput)
