NetApp Data Science Toolkit
=========

The NetApp Data Science Toolkit is a Python library that makes it simple for data scientists and data engineers to perform various data management tasks, such as provisioning a new data volume, near-instantaneously cloning a data volume, and near-instantaneously snapshotting a data volume for traceability/baselining. This Python library can function as either a [command line utility](#command-line-functionality) or a [library of functions](#library-of-functions) that can be imported into any Python program or Jupyter Notebook.

## Compatibility

The NetApp Data Science Toolkit supports Linux and macOS hosts.

The toolkit must be used in conjunction with a data storage system or service in order to be useful. The toolkit simplifies the performing of various data management tasks that are actually executed by the data storage system or service. In order to facilitate this, the toolkit communicates with the data storage system or service via API. The toolkit is currently compatible with the following storage systems and services:

- NetApp AFF (running ONTAP 9.7 and above)
- NetApp FAS (running ONTAP 9.7 and above)
- NetApp Cloud Volumes ONTAP (running ONTAP 9.7 and above)
- NetApp ONTAP Select (running ONTAP 9.7 and above)

<a name="getting-started"></a>

## Getting Started

The NetApp Data Science Toolkit requires that Python 3.5 or above be installed on the local host.

The following Python libraries that are not generally bundled with a standard Python installation are required in order for the NetApp Data Science Toolkit to function correctly - netapp-ontap, pandas, tabulate. These libraries can be installed with a Python package manager like pip.

```sh
pip3 install netapp-ontap pandas tabulate
```

A config file must be created before the NetApp Data Management Toolkit can be used to perform data management operations. To create a config file, run the following command. This command will create a config file named 'config.json' in '~/.ntap_dsutil/'.

```sh
./ntap_dsutil.py config
```

#### Example Usage

```sh
./ntap_dsutil.py config
Enter ONTAP management interface or IP address (Note: Can be cluster or SVM management interface): 192.168.245.200
Enter SVM (Storage VM) name: ai_data
Enter SVM NFS data LIF hostname or IP address: 192.168.245.203
Enter default volume type to use when creating new volumes (flexgroup/flexvol) [flexgroup]: 
Enter export policy to use by default when creating new volumes [default]: 
Enter snapshot policy to use by default when creating new volumes [none]: 
Enter unix filesystem user id (uid) to apply by default when creating new volumes (ex. '0' for root user) [0]: 
Enter unix filesystem group id (gid) to apply by default when creating new volumes (ex. '0' for root group) [0]: 
Enter unix filesystem permissions to apply by default when creating new volumes (ex. '0777' for full read/write permissions for all users and groups) [0777]: 
Enter aggregate to use by default when creating new FlexVol volumes: ai_vsim97_01_FC_1
Enter ONTAP API username (Note: Can be cluster or SVM admin account): admin
Enter ONTAP API password (Note: Can be cluster or SVM admin account): 
Verify SSL certificate when calling ONTAP API (true/false): false
Created config file: '/home/moglesby/.ntap_dsutil/config.json'.
```

## Troubleshooting Errors

If you experience an error and do not know how to resolve it, visit the [Troubleshooting](troubleshooting.md) page.

## Tips and Tricks

- [Using the NetApp Data Science Toolkit with Kubernetes.](kubernetes.md)

<a name="command-line-functionality"></a>

## Command Line Functionality

The simplest way to use the NetApp Data Science Toolkit is as a command line utility. When functioning as a command line utility, the toolkit supports the following operations.

Data volume management operations:
- [Clone a data volume.](#cli-clone-volume)
- [Create a new data volume.](#cli-create-volume)
- [Delete an existing data volume.](#cli-delete-volume)
- [List all data volumes.](#cli-list-volumes)
- [Mount an existing data volume locally.](#cli-mount-volume)

Snapshot management operations:
- [Create a new snapshot for a data volume.](#cli-create-snapshot)
- [Delete an existing snapshot for a data volume.](#cli-delete-snapshot)
- [List all snapshots for a data volume.](#cli-list-snapshots)
- [Restore a snapshot for a data volume.](#cli-restore-snapshot)

### Data Volume Management Operations

<a name="cli-clone-volume"></a>

#### Clone a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously create a new data volume that is an exact copy of an existing volume. This functionality utilizes NetApp FlexClone technology. This means that any clones created will be extremely storage-space-efficient. Aside from metadata, a clone will not consume additional storage space until its contents starts to deviate from the source volume. The command for cloning a data volume is `./ntap_dsutil.py clone volume`.

The following options/arguments are required:

```
    -n, --name=             Name of new volume..
    -v, --source-volume=    Name of volume to be cloned.
```

The following options/arguments are optional:

```
    -g, --gid=              Unix filesystem group id (gid) to apply when creating new volume (if not specified, gid of source volume will be retained) (Note: cannot apply gid of '0' when creating clone).
    -h, --help              Print help text.
    -m, --mountpoint=       Local mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
    -s, --source-snapshot=  Name of the snapshot to be cloned (if specified, the clone will be created from a specific snapshot on the source volume as opposed to the current state of the volume).
    -u, --uid=              Unix filesystem user id (uid) to apply when creating new volume (if not specified, uid of source volume will be retained) (Note: cannot apply uid of '0' when creating clone).
```

##### Example Usage

Create a volume named 'project2' that is an exact copy of the volume 'project1'.

```sh
./ntap_dsutil.py clone volume --name=project2 --source-volume=project1
Creating clone volume 'project2' from source volume 'project1'.
Clone volume created successfully.
```

Create a volume named 'project2' that is an exact copy of the contents of volume 'project1' at the time that the snapshot 'snap1' was created, and locally mount the newly created volume at '~/project2'.

```sh
sudo -E ./ntap_dsutil.py clone volume --name=project2 --source-volume=project1 --source-snapshot=snap1 --mountpoint=~/project2
Creating clone volume 'project2' from source volume 'project1'.
Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.
Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.
Clone volume created successfully.
Mounting volume 'project2' at '~/project2'.
Volume mounted successfully.
```

For additional examples, run `./ntap_dsutil.py clone volume -h`.

<a name="cli-create-volume"></a>

#### Create a New Data Volume

The NetApp Data Science Toolkit can be used to rapidly provision a new data volume. The command for creating a new data volume is `./ntap_dsutil.py create volume`.

The following options/arguments are required:

```
    -n, --name=             Name of new volume.
    -s, --size=             Size of new volume. Format: '1024MB', '100GB', '10TB', etc.
```

The following options/arguments are optional:

```
    -a, --aggregate=        Aggregate to use when creating new volume (flexvol volumes only).
    -d, --snapshot-policy=  Snapshot policy to apply for new volume.
    -e, --export-policy=    NFS export policy to use when exporting new volume.
    -g, --gid=              Unix filesystem group id (gid) to apply when creating new volume (ex. '0' for root group).
    -h, --help              Print help text.
    -m, --mountpoint=       Local mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
    -p, --permissions=      Unix filesystem permissions to apply when creating new volume (ex. '0777' for full read/write permissions for all users and groups).
    -t, --type=             Volume type to use when creating new volume (flexgroup/flexvol).
    -u, --uid=              Unix filesystem user id (uid) to apply when creating new volume (ex. '0' for root user).
```

##### Example Usage

Create a volume named 'project1' of size 10TB.

```sh
./ntap_dsutil.py create volume --name=project1 --size=10TB
Creating volume 'project1'.
Volume created successfully.
```

Create a volume named 'project2' of size 2TB, and locally mount the newly created volume at '~/project2'.

```sh
sudo -E ./ntap_dsutil.py create volume --name=project2 --size=2TB --mountpoint=~/project2
[sudo] password for ai:
Creating volume 'project2'.
Volume created successfully.
Mounting volume 'project2' at '~/project2'.
Volume mounted successfully.
```

For additional examples, run `./ntap_dsutil.py create volume -h`.

<a name="cli-delete-volume"></a>

#### Delete an Existing Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing data volume. The command for deleting an existing data volume is `./ntap_dsutil.py delete volume`.

The following options/arguments are required:

```
    -n, --name=     Name of volume to be deleted.
```

The following options/arguments are optional:

```
    -f, --force     Do not prompt user to confirm operation.
    -h, --help      Print help text.
```

##### Example Usage

Delete the volume named 'test1'.

```sh
./ntap_dsutil.py delete volume --name=test1
Warning: All data and snapshots associated with the volume will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting volume 'test1'.
Volume deleted successfully.
```

<a name="cli-list-volumes"></a>

#### List All Data Volumes

The NetApp Data Science Toolkit can be used to print a list of all existing data volumes. The command for printing a list of all existing data volumes is `./ntap_dsutil.py list volumes`.

No options/arguments are required for this command.

##### Example Usage

```sh
./ntap_dsutil.py list volumes
Volume Name    Size    Type       NFS Mount Target            Local Mountpoint      Clone    Source Volume    Source Snapshot
-------------  ------  ---------  --------------------------  --------------------  -------  ---------------  ---------------------------
test5          2.0TB   flexvol    10.61.188.49:/test5                               yes      test2            clone_test5.1
test1          10.0TB  flexvol    10.61.188.49:/test1                               no
test2          2.0TB   flexvol    10.61.188.49:/test2                               no
test4          2.0TB   flexgroup  10.61.188.49:/test4         /mnt/tmp              no
ailab_data01   10.0TB  flexvol    10.61.188.49:/ailab_data01                        no
home           10.0TB  flexgroup  10.61.188.49:/home                                no
ailab_data02   10.0TB  flexvol    10.61.188.49:/ailab_data02                        no
project        2.0TB   flexvol    10.61.188.49:/project                             no
test3          2.0TB   flexgroup  10.61.188.49:/test3         /home/ai/test3        no
test1_clone    10.0TB  flexvol    10.61.188.49:/test1_clone   /home/ai/test1_clone  yes      test1            ntap_dsutil_20201124_172255
```

<a name="cli-mount-volume"></a>

#### Mount an Existing Data Volume Locally

The NetApp Data Science Toolkit can be used to mount an existing data volume on your local host. The command for mounting an existing volume locally is `./ntap_dsutil.py mount volume`. If executed on a Linux host, this command must be run as root. It is usually not necessary to run this command as root on macOS hosts.

The following options/arguments are required:

```
    -m, --mountpoint=       Local mountpoint to mount volume at.
    -n, --name=             Name of volume.
```

##### Example Usage

Locally mount the volume named 'project1' at '~/project1'.

```sh
sudo -E ./ntap_dsutil.py mount volume --name=project1 --mountpoint=~/project1
[sudo] password for ai:
Mounting volume 'project1' at '~/project1'.
Volume mounted successfully.
```

### Snapshot Management Operations

<a name="cli-create-snapshot"></a>

#### Create a New Snapshot for a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing data volume. These read-only copies are called snapshots. This functionality can be used to version datasets and/or implement dataset-to-model traceability. The command for creating a new snapshot for a specific data volume is `./ntap_dsutil.py create snapshot`.

The following options/arguments are required:

```
    -v, --volume=   Name of volume.
```

The following options/arguments are optional:

```
    -h, --help      Print help text.
    -n, --name=     Name of new snapshot. If not specified, will be set to 'ntap_dsutil_<timestamp>'.
```

##### Example Usage

Create a snapshot named 'final_dataset' for the volume named 'test1'.

```sh
./ntap_dsutil.py create snapshot --volume=test1 --name=final_dataset
Creating snapshot 'final_dataset'.
Snapshot created successfully.
```

Create a snapshot for the volume named 'test1'.

```sh
./ntap_dsutil.py create snapshot -v test1
Creating snapshot 'ntap_dsutil_20201113_125210'.
Snapshot created successfully.
```

<a name="cli-delete-snapshot"></a>

#### Delete an Existing Snapshot for a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing snapshot for a specific data volume. The command for deleting an existing snapshot for a specific data volume is `./ntap_dsutil.py delete snapshot`.

The following options/arguments are required:

```
    -n, --name=     Name of snapshot to be deleted.
    -v, --volume=   Name of volume.
```

The following options/arguments are optional:

```
    -h, --help      Print help text.
```

##### Example Usage

Delete the snapshot named 'snap1' for the volume named 'test1'.

```sh
./ntap_dsutil.py delete snapshot --volume=test1 --name=snap1
Deleting snapshot 'snap1'.
Snapshot deleted successfully.
```

<a name="cli-list-snapshots"></a>

#### List All Snapshots for a Data Volume

The NetApp Data Science Toolkit can be used to print a list of all existing snapshots for a specific data volume. The command for printing a list of all snapshots for a specific data volume is `./ntap_dsutil.py list snapshots`.

The following options/arguments are required:

```
    -v, --volume=   Name of volume.
```

##### Example Usage

List all snapshots for the volume named 'test1'.

```sh
./ntap_dsutil.py list snapshots --volume=test1
Snapshot Name                Create Time
---------------------------  -------------------------
snap1                        2020-11-13 20:17:48+00:00
ntap_dsutil_20201113_151807  2020-11-13 20:18:07+00:00
snap3                        2020-11-13 21:43:48+00:00
ntap_dsutil_20201113_164402  2020-11-13 21:44:02+00:00
final_dataset                2020-11-13 21:45:16+00:00
```

<a name="cli-restore-snapshot"></a>

#### Restore a Snapshot for a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously restore a specific snapshot for a data volume. This action will restore the volume to its exact state at the time that the snapshot was created. The command for restoring a specific snapshot for a data volume is `./ntap_dsutil.py restore snapshot`.

Warning: When you restore a snapshot, all subsequent snapshots are deleted.

The following options/arguments are required:

```
    -n, --name=     Name of snapshot to be restored.
    -v, --volume=   Name of volume.
```

The following options/arguments are optional:

```
    -f, --force     Do not prompt user to confirm operation.
    -h, --help      Print help text.
```

##### Example Usage

Restore the volume 'project2' to its exact state at the time that the snapshot named 'initial_dataset' was created.

Warning: This will delete any snapshots that were created after 'initial_dataset' was created.

```sh
/ntap_dsutil.py restore snapshot --volume=project2 --name=initial_dataset
Warning: When you restore a snapshot, all subsequent snapshots are deleted.
Are you sure that you want to proceed? (yes/no): yes
Restoring snapshot 'initial_dataset'.
Snapshot restored successfully.
```

<a name="library-of-functions"></a>

## Advanced: Importable Library of Functions

The NetApp Data Science Toolkit can also be utilized as a library of functions that can be imported into any Python program or Jupyter Notebook. In this manner, data scientists and data engineers can easily incorporate data management tasks into their existing projects, programs, and workflows. This functionality is only recommended for advanced users who are proficient in Python.

To import the NetApp Data Science Toolkit library functions into a Python program, ensure that the `ntap_dsutil.py` file is in the same directory as the program, and include the following line of code in the program:

```py
from ntap_dsutil import createVolume, listVolumes, mountVolume, createSnapshot, listSnapshots, deleteSnapshot, deleteVolume, restoreSnapshot, cloneVolume
```

Note: The prerequisite steps outlined in the [Getting Started](#getting-started) section still appy when the toolkit is being utilized as an importable library of functions.

When being utilized as an importable library of functions, the toolkit supports the following operations.

Data volume management operations:
- [Clone a data volume.](#lib-clone-volume)
- [Create a new data volume.](#lib-create-volume)
- [Delete an existing data volume.](#lib-delete-volume)
- [List all data volumes.](#lib-list-volumes)
- [Mount an existing data volume locally.](#lib-mount-volume)

Snapshot management operations:
- [Create a new snapshot for a data volume.](#lib-create-snapshot)
- [Delete an existing snapshot for a data volume.](#lib-delete-snapshot)
- [List all snapshots for a data volume.](#lib-list-snapshots)
- [Restore a snapshot for a data volume.](#lib-restore-snapshot)

### Examples

[Examples.ipynb](Examples.ipynb) is a Jupyter Notebook that contains examples that demonstrate how the NetApp Data Science Toolkit can be utilized as an importable library of functions.

### Data Volume Management Operations

<a name="lib-clone-volume"></a>

#### Clone a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously create a new data volume that is an exact copy of an existing volume as part of any Python program or workflow. This functionality utilizes NetApp FlexClone technology. This means that any clones created will be extremely storage-space-efficient. Aside from metadata, a clone will not consume additional storage space until its contents starts to deviate from the source volume.

##### Function Definition

```py
def cloneVolume(
    newVolumeName: str,             # Name of new volume (required).
    sourceVolumeName: str,          # Name of volume to be cloned (required).
    sourceSnapshotName: str,        # Name of the snapshot to be cloned (if specified, the clone will be created from a specific snapshot on the source volume as opposed to the current state of the volume).
    unixUID: str = None,            # Unix filesystem user id (uid) to apply when creating new volume (if not specified, uid of source volume will be retained) (Note: cannot apply uid of '0' when creating clone).
    unixGID: str = None,            # Unix filesystem group id (gid) to apply when creating new volume (if not specified, gid of source volume will be retained) (Note: cannot apply gid of '0' when creating clone).
    mountpoint: str = None,         # Local mountpoint to mount new volume at. If not specified, volume will not be mounted locally. On Linux hosts - if specified, calling program must be run as root.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
InvalidSnapshotParameterError   # An invalid parameter was specified.
MountOperationError             # The volume was not succesfully mounted locally.
```

<a name="lib-create-volume"></a>

#### Create a New Data Volume

The NetApp Data Science Toolkit can be used to rapidly provision a new data volume as part of any Python program or workflow.

##### Function Definition

```py
def createVolume(
    volumeName: str,                # Name of new volume (required).
    volumeSize: str,                # Size of new volume (required). Format: '1024MB', '100GB', '10TB', etc.
    volumeType: str = "flexvol",    # Volume type to use when creating new volume (flexgroup/flexvol).
    unixPermissions: str = "0777",  # Unix filesystem permissions to apply when creating new volume (ex. '0777' for full read/write permissions for all users and groups).
    unixUID: str = "0",             # Unix filesystem user id (uid) to apply when creating new volume (ex. '0' for root user).
    unixGID: str = "0",             # Unix filesystem group id (gid) to apply when creating new volume (ex. '0' for root group).
    exportPolicy: str = "default",  # NFS export policy to use when exporting new volume.
    snapshotPolicy: str = "none",   # Snapshot policy to apply for new volume.
    aggregate: str = None,          # Aggregate to use when creating new volume (flexvol volumes only).
    mountpoint: str = None,         # Local mountpoint to mount new volume at. If not specified, volume will not be mounted locally. On Linux hosts - if specified, calling program must be run as root.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
MountOperationError             # The volume was not succesfully mounted locally.
```

<a name="lib-delete-volume"></a>

#### Delete an Existing Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing data volume as part of any Python program or workflow. 

##### Function Definition

```py
def deleteVolume(
    volumeName: str,            # Name of volume (required).
    printOutput: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-list-volumes"></a>

#### List All Data Volumes

The NetApp Data Science Toolkit can be used to retrieve a list of all existing data volumes as part of any Python program or workflow.

##### Function Definition

```py
def listVolumes(
    checkLocalMounts: bool = False,     # If set to true, then the local mountpoints of any mounted volumes will be included in the returned list and included in printed output.
    printOutput: bool = False           # Denotes whether or not to print messages to the console during execution.
) -> list() :
```

##### Return Value

The function returns a list of all existing volumes. Each item in the list will be a dictionary containing details regarding a specific volume. The keys for the values in this dictionary are "Volume Name", "Size", "Type", "NFS Mount Target". If `checkLocalMounts` is set to `True`, then "Local Mountpoint" will also be included as a key in the dictionary.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
```

<a name="lib-mount-volume"></a>

#### Mount an Existing Data Volume Locally

The NetApp Data Science Toolkit can be used to mount an existing data volume on your local host as part of any Python program or workflow. On Linux hosts, mounting requires root privileges, so any Python program that invokes this function must be run as root. It is usually not necessary to invoke this function as root on macOS hosts.

##### Function Definition

```py
def mountVolume(
    volumeName: str,            # Name of volume (required).
    mountpoint: str,            # Local mountpoint to mount volume at (required).
    printOutput: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
MountOperationError             # The volume was not succesfully mounted locally.
```

### Snapshot Management Operations

<a name="lib-create-snapshot"></a>

#### Create a New Snapshot for a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing data volume as part of any Python program or workflow. These read-only copies are called snapshots. This functionality can be used to version datasets and/or implement dataset-to-model traceability.

##### Function Definition

```py
def createSnapshot(
    volumeName: str,                    # Name of volume (required).
    snapshotName: str = None,           # Name of new snapshot. If not specified, will be set to 'ntap_dsutil_<timestamp>'.
    printOutput: bool = False           # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-delete-snapshot"></a>

#### Delete an Existing Snapshot for a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing snapshot for a specific data volume as part of any Python program or workflow. 

##### Function Definition

```py
def deleteSnapshot(
    volumeName: str,            # Name of volume (required).
    snapshotName: str,          # Name of snapshot to be deleted (required).
    printOutput: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidSnapshotParameterError   # An invalid parameter was specified.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-list-snapshots"></a>

#### List All Existing Snapshots for a Data Volume

The NetApp Data Science Toolkit can be used to retrieve a list of all existing snapshots for a specific data volume as part of any Python program or workflow.

##### Function Definition

```py
def listSnapshots(
    volumeName: str,            # Name of volume.
    printOutput: bool = False   # Denotes whether or not to print messages to the console during execution.
) -> list() :
```

##### Return Value

The function returns a list of all existing snapshots for the specific data volume. Each item in the list will be a dictionary containing details regarding a specific snapshot. The keys for the values in this dictionary are "Snapshot Name", "Create Time".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-restore-snapshot"></a>

#### Restore a Snapshot for a Data Volume

The NetApp Data Science Toolkit can be used to near-instantaneously restore a specific snapshot for a data volume as part of any Python program or workflow. This action will restore the volume to its exact state at the time that the snapshot was created.

Warning: When you restore a snapshot, all subsequent snapshots are deleted.

##### Function Definition

```py
def restoreSnapshot(
    volumeName: str,            # Name of volume (required).
    snapshotName: str,          # Name of snapshot to be restored (required).
    printOutput: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil.py`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidSnapshotParameterError   # An invalid parameter was specified.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
