NetApp DataOps Toolkit for Traditional Environments
=========

The NetApp DataOps Toolkit for Traditional Environments is a Python library that makes it simple for developers, data scientists, DevOps engineers, and data engineers to perform various data management tasks, such as provisioning a new data volume, near-instantaneously cloning a data volume, and near-instantaneously snapshotting a data volume for traceability/baselining. This Python library can function as either a [command line utility](#command-line-functionality) or a [library of functions](#library-of-functions) that can be imported into any Python program or Jupyter Notebook.

## Compatibility

The NetApp DataOps Toolkit for Traditional Environments supports Linux and macOS hosts.

The toolkit must be used in conjunction with a data storage system or service in order to be useful. The toolkit simplifies the performing of various data management tasks that are actually executed by the data storage system or service. In order to facilitate this, the toolkit communicates with the data storage system or service via API. The toolkit is currently compatible with the following storage systems and services:

- NetApp AFF (running ONTAP 9.7 and above)
- NetApp FAS (running ONTAP 9.7 and above)
- NetApp Cloud Volumes ONTAP (running ONTAP 9.7 and above)
- NetApp ONTAP Select (running ONTAP 9.7 and above)

Note: The 'prepopulate flexcache' operation only supports ONTAP 9.8 and above. All other operations support ONTAP 9.7 and above.

## Installation

### Prerequisites

The NetApp DataOps Toolkit for Traditional Environments requires that Python 3.6 or above be installed on the local host. Additionally, the toolkit requires that pip for Python3 be installed on the local host. For more details regarding pip, including installation instructions, refer to the [pip documentation](https://pip.pypa.io/en/stable/installing/).

### Installation Instructions

To install the NetApp DataOps Toolkit for Traditional Environments, run the following command.

```sh
python3 -m pip install netapp-dataops-traditional
```

<a name="getting-started"></a>

## Getting Started

A config file must be created before the NetApp Data Management Toolkit for Traditional Environments can be used to perform data management operations. To create a config file, run the following command. This command will create a config file named 'config.json' in '~/.netapp_dataops/'.

```sh
netapp_dataops_cli.py config
```

Note: The toolkit requires an ONTAP account with API access. The toolkit will use this account to access the ONTAP API. NetApp recommends using an SVM-level account. Usage of a cluster admin account should be avoided for security reasons.

#### Example Usage

```sh
netapp_dataops_cli.py config
Enter ONTAP management LIF hostname or IP address (Recommendation: Use SVM management interface): 10.61.188.114
Enter SVM (Storage VM) name: ailab1
Enter SVM NFS data LIF hostname or IP address: 10.61.188.119
Enter default volume type to use when creating new volumes (flexgroup/flexvol) [flexgroup]:        
Enter export policy to use by default when creating new volumes [default]:
Enter snapshot policy to use by default when creating new volumes [none]:
Enter unix filesystem user id (uid) to apply by default when creating new volumes (ex. '0' for root user) [0]:
Enter unix filesystem group id (gid) to apply by default when creating new volumes (ex. '0' for root group) [0]:
Enter unix filesystem permissions to apply by default when creating new volumes (ex. '0777' for full read/write permissions for all users and groups) [0777]:
Enter aggregate to use by default when creating new FlexVol volumes: vsim_ontap97_01_FC_1
Enter ONTAP API username (Recommendation: Use SVM account): vsadmin
Enter ONTAP API password (Recommendation: Use SVM account):
Verify SSL certificate when calling ONTAP API (true/false): false
Do you intend to use this toolkit to trigger Cloud Sync operations? (yes/no): yes
Note: If you do not have a Cloud Central refresh token, visit https://services.cloud.netapp.com/refresh-token to create one.
Enter Cloud Central refresh token:
Do you intend to use this toolkit to push/pull from S3? (yes/no): yes
Enter S3 endpoint: http://10.61.188.75:2113
Enter S3 Access Key ID: TN9ISEC5BDGIOK59LC3I
Enter S3 Secret Access Key:
Verify SSL certificate when calling S3 API (true/false): false
Created config file: '/Users/moglesby/.netapp_dataops/config.json'.
```

## Troubleshooting Errors

If you experience an error and do not know how to resolve it, visit the [Troubleshooting](troubleshooting.md) page.

## Tips and Tricks

- [Accelerating the AI training workflow with the NetApp DataOps Toolkit.](https://netapp.io/2020/12/14/accelerating-the-ai-training-workflow-with-the-netapp-data-science-toolkit/)
- [Easy AI dataset-to-model traceability with the NetApp DataOps Toolkit.](https://netapp.io/2021/01/13/easy-ai-dataset-to-model-traceability-with-the-netapp-data-science-toolkit/)

<a name="command-line-functionality"></a>

## Command Line Functionality

The simplest way to use the NetApp DataOps Toolkit is as a command line utility. When functioning as a command line utility, the toolkit supports the following operations.

Data volume management operations:
- [Clone a data volume.](#cli-clone-volume)
- [Create a new data volume.](#cli-create-volume)
- [Delete an existing data volume.](#cli-delete-volume)
- [List all data volumes.](#cli-list-volumes)
- [Mount an existing data volume locally as "read-only" or "read-write".](#cli-mount-volume)
- [Unmount an existing data volume.](#cli-unmount-volume)

Snapshot management operations:
- [Create a new snapshot for a data volume.](#cli-create-snapshot)
- [Delete an existing snapshot for a data volume.](#cli-delete-snapshot)
- [Rename an existing snapshot for a data volume.](#cli-renmae-snapshot)
- [List all snapshots for a data volume.](#cli-list-snapshots)
- [Restore a snapshot for a data volume.](#cli-restore-snapshot)

Data fabric operations:
- [List all Cloud Sync relationships.](#cli-list-cloud-sync-relationships)
- [Trigger a sync operation for an existing Cloud Sync relationship.](#cli-sync-cloud-sync-relationship)
- [Pull the contents of a bucket from S3 (multithreaded).](#cli-pull-from-s3-bucket)
- [Pull an object from S3.](#cli-pull-from-s3-object)
- [Push the contents of a directory to S3 (multithreaded).](#cli-push-to-s3-directory)
- [Push a file to S3.](#cli-push-to-s3-file)

Advanced data fabric operations:
- [Prepopulate specific files/directories on a FlexCache volume (ONTAP 9.8 and above ONLY).](#cli-prepopulate-flexcache)
- [List all SnapMirror relationships.](#cli-list-snapmirror-relationships)
- [Trigger a sync operation for an existing SnapMirror relationship.](#cli-sync-snapmirror-relationship)
- [Create new SnapMirror relationship.](#cli-create-snapmirror-relationship)

### Data Volume Management Operations

<a name="cli-clone-volume"></a>

#### Clone a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously create a new data volume that is an exact copy of an existing volume. This functionality utilizes NetApp FlexClone technology. This means that any clones created will be extremely storage-space-efficient. Aside from metadata, a clone will not consume additional storage space until its contents starts to deviate from the source volume. The command for cloning a data volume is `netapp_dataops_cli.py clone volume`.

The following options/arguments are required:

```
    -n, --name=             Name of new volume..
    -v, --source-volume=    Name of volume to be cloned.
```

The following options/arguments are optional:

```
    -l, --cluster-name=     non default hosting cluster
    -c, --source-svm=       non default source svm name
    -t, --target-svm=       non default target svm name
    -g, --gid=              Unix filesystem group id (gid) to apply when creating new volume (if not specified, gid of source volume will be retained) (Note: cannot apply gid of '0' when creating clone).
    -h, --help              Print help text.
    -m, --mountpoint=       Local mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
    -s, --source-snapshot=  Name of the snapshot to be cloned (if specified, the clone will be created from a specific snapshot on the source volume as opposed to the current state of the volume).
                            when snapshot name suffixed with * the latest snapshot will be used (hourly* will use the latest snapshot prefixed with hourly )
    -u, --uid=              Unix filesystem user id (uid) to apply when creating new volume (if not specified, uid of source volume will be retained) (Note: cannot apply uid of '0' when creating clone).
    -x, --readonly          Read-only option for mounting volumes locally.
    -j, --junction          Specify a custom junction path for the volume to be exported at.
    -e, --export-hosts      colon(:) seperated hosts/cidrs to to use for export. hosts will be exported for rw and root access
    -e, --export-policy     export policy name to attach to the volume, default policy will be used if export-hosts/export-policy not provided
    -d, --snapshot-policy   snapshot-policy to attach to the volume, default snapshot policy will be used if not provided
    -s, --split             start clone split after creation
    -r, --refresh           delete existing clone if exists before creating a new one
    -a, --preserve-msid     when refreshing clone preserve the original clone msid (can help nfs remount)
    -d, --svm-dr-unprotect  disable svm dr protection if svm-dr protection exists
```

##### Example Usage

Create a volume named 'project2' that is an exact copy of the volume 'project1'.

```sh
netapp_dataops_cli.py clone volume --name=project2 --source-volume=project1
Creating clone volume 'project2' from source volume 'project1'.
Clone volume created successfully.
```

Create a volume named 'project2' that is an exact copy of the volume 'project1', and locally mount the newly created volume at '~/project2' as read-write.

```sh
netapp_dataops_cli.py clone volume --name=project2 --source-volume=project1 --mountpoint=~/project2 --readonly
Creating clone volume 'project2' from source volume 'project1'.
Clone volume created successfully.
Mounting volume 'project2' at '~/project2' as read-only.
Volume mounted successfully.
```

Create a volume named 'project2' that is an exact copy of the contents of volume 'project1' at the time that the snapshot 'snap1' was created, and locally mount the newly created volume at '~/project2' as read-write.

```sh
sudo -E netapp_dataops_cli.py clone volume --name=project2 --source-volume=project1 --source-snapshot=snap1 --mountpoint=~/project2
Creating clone volume 'project2' from source volume 'project1'.
Warning: Cannot apply uid of '0' when creating clone; uid of source volume will be retained.
Warning: Cannot apply gid of '0' when creating clone; gid of source volume will be retained.
Clone volume created successfully.
Mounting volume 'project2' at '~/project2'.
Volume mounted successfully.
```

For additional examples, run `netapp_dataops_cli.py clone volume -h`.

<a name="cli-create-volume"></a>

#### Create a New Data Volume

The NetApp DataOps Toolkit can be used to rapidly provision a new data volume. The command for creating a new data volume is `netapp_dataops_cli.py create volume`.

The following options/arguments are required:

```
    -n, --name=             Name of new volume.
    -s, --size=             Size of new volume. Format: '1024MB', '100GB', '10TB', etc.
```

The following options/arguments are optional:

```
    -l, --cluster-name=     non default hosting cluster
    -v, --svm=              non default svm name
    -a, --aggregate=        Aggregate to use when creating new volume (flexvol) or optional comma seperated aggrlist when specific aggregates are required for FG.
    -d, --snapshot-policy=  Snapshot policy to apply for new volume.
    -e, --export-policy=    NFS export policy to use when exporting new volume.
    -g, --gid=              Unix filesystem group id (gid) to apply when creating new volume (ex. '0' for root group).
    -h, --help              Print help text.
    -m, --mountpoint=       Local mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
    -p, --permissions=      Unix filesystem permissions to apply when creating new volume (ex. '0777' for full read/write permissions for all users and groups).
    -r, --guarantee-space   Guarantee sufficient storage space for full capacity of the volume (i.e. do not use thin provisioning).
    -t, --type=             Volume type to use when creating new volume (flexgroup/flexvol).
    -u, --uid=              Unix filesystem user id (uid) to apply when creating new volume (ex. '0' for root user).
    -x, --readonly          Read-only option for mounting volumes locally.
    -j, --junction          Specify a custom junction path for the volume to be exported at.
    -f, --tiering-policy    Specify tiering policy for fabric-pool enabled systems (default is 'none').
    -y, --dp                Create volume as DP volume (the volume will be used as snapmirror target)
```

##### Example Usage

Create a volume named 'project1' of size 10TB.

```sh
netapp_dataops_cli.py create volume --name=project1 --size=10TB
Creating volume 'project1'.
Volume created successfully.
```

Create a volume named 'project2' of size 2TB, and locally mount the newly created volume at '~/project2' as read-only.

```sh
sudo -E netapp_dataops_cli.py create volume --name=project2 --size=2TB --mountpoint=~/project2 --readonly
[sudo] password for ai:
Mounting Volume at specified junction path: '/project2'
Creating volume 'project2'.
Volume created successfully.
Mounting volume 'project2' at '~/project2' as readonly.
Volume mounted successfully.
```

For additional examples, run `netapp_dataops_cli.py create volume -h`.

<a name="cli-delete-volume"></a>

#### Delete an Existing Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing data volume. The command for deleting an existing data volume is `netapp_dataops_cli.py delete volume`.

The following options/arguments are required:

```
    -n, --name=     Name of volume to be deleted.
```

The following options/arguments are optional:

```
    -u, --cluster-name=     Non default hosting cluster
    -v, --svm=              Non default SVM name
    -f, --force             Do not prompt user to confirm operation.
    -m, --delete-mirror     Delete/release snapmirror relationship prior to volume deletion
        --delete-non-clone  Enable deletion of volume not created as clone by this tool
    -h, --help              Print help text.

```

##### Example Usage

Delete the volume named 'test1'.

```sh
netapp_dataops_cli.py delete volume --name=test1
Warning: All data and snapshots associated with the volume will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting volume 'test1'.
Volume deleted successfully.
```

<a name="cli-list-volumes"></a>

#### List All Data Volumes

The NetApp DataOps Toolkit can be used to print a list of all existing data volumes. The command for printing a list of all existing data volumes is `netapp_dataops_cli.py list volumes`.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -u, --cluster-name=                 non default hosting cluster
    -v, --svm=                          list volume on non default svm
    -p, --vol-prefix=                   list information for volume prefixed by this
    -h, --help                          Print help text.
    -s, --include-space-usage-details   Include storage space usage details in output (see README for explanation).
```

##### Storage Space Usage Details Explanation

If the -s/--include-space-usage-details  option is specified, then four additional columns will be included in the output. These columns will be titled 'Snap Reserve', 'Capacity', 'Usage', and 'Footprint'. These columns and their relation to the 'Size' column are explained in the table below.

| Column        | Explanation                                                                                                                        |
|---------------|------------------------------------------------------------------------------------------------------------------------------------|
| Size          | The logical size of the volume.                                                                                                    |
| Snap Reserve  | The percentage of the volume's logical size that is reserved for snapshot copies.                                                  |
| Capacity      | The logical capacity that is available for users of the volume to store data in.                                                   |
| Usage         | The combined logical size of all of the files that are stored on the volume.                                                       |
| Footprint     | The actual on-disk storage space that is being consumed by the volume after all ONTAP storage efficiencies are taken into account. |

The 'Footprint' value will differ from the 'Usage' value. In some cases, particularly with clone volumes, the 'Footprint' value will be smaller than the 'Usage' value due to ONTAP storage efficiencies. These storage efficiencies include FlexClone technology, deduplication, compression, etc. In the case that the 'Footprint' value is smaller than the 'Usage' value, the delta between the two is a rough representation of the on-disk space savings that you are receiving from ONTAP storage efficiencies.

Note that the 'Footprint' value includes the on-disk storage space that is being consumed by all of the volume's snapshot copies in addition to the on-disk storage space that is being consumed by the data that is currently stored on the volume. If a volume has many snapshots, then the snapshots may represent a large portion of the 'Footprint' value.

Also note that if you are using an ONTAP version earlier than 9.9, then the 'Footprint' value will only be reported for 'flexvol' volumes.

##### Example Usage

Standard usage:

```sh
netapp_dataops_cli.py list volumes
Volume Name    Size    Type       NFS Mount Target            Local Mountpoint      FlexCache    Clone    Source Volume    Source Snapshot
-------------  ------  ---------  --------------------------  --------------------  -----------  -------  ---------------  ---------------------------
test5          2.0TB   flexvol    10.61.188.49:/test5                               no           yes      test2            clone_test5.1
test1          10.0TB  flexvol    10.61.188.49:/test1                               no           no
test2          2.0TB   flexvol    10.61.188.49:/test2                               no           no
test4          2.0TB   flexgroup  10.61.188.49:/test4         /mnt/tmp              no           no
ailab_data01   10.0TB  flexvol    10.61.188.49:/ailab_data01                        no           no
home           10.0TB  flexgroup  10.61.188.49:/home                                no           no
ailab_data02   10.0TB  flexvol    10.61.188.49:/ailab_data02                        no           no
project        2.0TB   flexvol    10.61.188.49:/project                             yes          no
test3          2.0TB   flexgroup  10.61.188.49:/test3         /home/ai/test3        no           no
test1_clone    10.0TB  flexvol    10.61.188.49:/test1_clone   /home/ai/test1_clone  no           yes      test1            netapp_dataops_20201124_172255
```

Include physical storage space footprint in output:

```sh
netapp_dataops_cli.py list volumes --include-space-usage details
Volume Name    Size      Snap Reserve    Capacity    Usage     Footprint    Type       NFS Mount Target                Local Mountpoint    FlexCache    Clone    Source Volume    Source Snapshot
-------------  --------  --------------  ----------  --------  -----------  ---------  ------------------------------  ------------------  -----------  -------  ---------------  -----------------------------------
team1          300.0GB   5%              285.0GB     12.38GB   12.59GB      flexvol    10.61.188.90:/team1             /home/ai/master     no           no
team1_ws1      300.0GB   5%              285.0GB     15.04GB   2.87GB       flexvol    10.61.188.90:/team1_ws1         /home/ai/ws1        no           yes      team1            clone_team1_ws1.2021-06-30_204755.0
```

<a name="cli-mount-volume"></a>

#### Mount an Existing Data Volume Locally

The NetApp DataOps Toolkit can be used to mount an existing data volume on your local host. The command for mounting an existing volume locally is `netapp_dataops_cli.py mount volume`. If executed on a Linux host, this command must be run as root. It is usually not necessary to run this command as root on macOS hosts.

The following options/arguments are required:

```
    -m, --mountpoint=       Local mountpoint to mount volume at.
    -n, --name=             Name of volume.
```

The following options/arguments are optional:

```
    -v, --svm=              non default SVM name
    -l, --lif=              non default lif (nfs server ip/name)
    -h, --help              Print help text.
    -x, --readonly          Mount volume locally as read-only.
```

##### Example Usage

Locally mount the volume named 'project1' at '~/project1' as read-only.

```sh
sudo -E netapp_dataops_cli.py mount volume --name=project1 --mountpoint=~/project1 --readonly
[sudo] password for ai:
Mounting volume 'project1' at '~/project1' as readonly.
Volume mounted successfully.
```

<a name="cli-unmount-volume"></a>

#### Unmount an Existing Data Volume

The NetApp DataOps Toolkit can be used to unmount an existing data volume that is currently on your local host. The command for unmounting an existing volume is `netapp_dataops_cli.py unmount volume`. If executed on a Linux host, this command must be run as root. It is usually not necessary to run this command as root on macOS hosts.

The following options/arguments are required:

```
    -m, --mountpoint=       Mountpoint where volume is mounted at.
```

##### Example Usage

Unmount the volume that is currently mounted at '/test1' on your local host.

```sh
sudo -E netapp_dataops_cli.py unmount volume --mointpoint=/test1
[sudo] password for ai:
Unmounting volume at '/test1'.
Volume unmounted successfully.
```

### Snapshot Management Operations

<a name="cli-create-snapshot"></a>

#### Create a New Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing data volume. These read-only copies are called snapshots. This functionality can be used to version datasets and/or implement dataset-to-model traceability. The command for creating a new snapshot for a specific data volume is `netapp_dataops_cli.py create snapshot`.

The following options/arguments are required:

```
    -v, --volume=   Name of volume.
```

The following options/arguments are optional:

```
    -u, --cluster-name=      non default hosting cluster
    -s, --svm=               Non defaul svm name.
    -n, --name=              Name of new snapshot. If not specified, will be set to 'netapp_dataops_<timestamp>'.
    -r, --retention=         Snapshot name will be suffixed by <timestamp> and excesive snapshots will be deleted.
                             Can be count of snapshots when int (ex. 10) or days when retention is suffixed by d (ex. 10d)
    -l, --snapmirror-label=  if proivded snapmirror label will be configured on the created snapshot   
    -h, --help               Print help text.
```

##### Example Usage

Create a snapshot named 'final_dataset' for the volume named 'test1'.

```sh
netapp_dataops_cli.py create snapshot --volume=test1 --name=final_dataset
Creating snapshot 'final_dataset'.
Snapshot created successfully.
```

Create a snapshot for the volume named 'test1'.

```sh
netapp_dataops_cli.py create snapshot -v test1
Creating snapshot 'netapp_dataops_20201113_125210'.
Snapshot created successfully.
```

<a name="cli-delete-snapshot"></a>

#### Delete an Existing Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing snapshot for a specific data volume. The command for deleting an existing snapshot for a specific data volume is `netapp_dataops_cli.py delete snapshot`.

The following options/arguments are required:

```
    -n, --name=     Name of snapshot to be deleted.
    -v, --volume=   Name of volume.
```

The following options/arguments are optional:

```
    -u, --cluster-name=     non default hosting cluster
    -s, --svm=      Non default svm
    -h, --help      Print help text.

```

##### Example Usage

Delete the snapshot named 'snap1' for the volume named 'test1'.

```sh
netapp_dataops_cli.py delete snapshot --volume=test1 --name=snap1
Deleting snapshot 'snap1'.
Snapshot deleted successfully.
```

<a name="cli-rename-snapshot"></a>

#### Rename an Existing Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously rename an existing snapshot for a specific data volume. The command for renaming an existing snapshot for a specific data volume is `netapp_dataops_cli.py rename snapshot`.

The following options/arguments are required:

```
    -v, --volume=   Name of volume.
    -n, --name=     Name of existing snapshot.
    -t, --new-name= Reanme snapshot to this name.
```

The following options/arguments are optional:

```
    -u, --cluster-name=     non default hosting cluster
    -s, --svm=      Non default svm
    -h, --help      Print help text.

```

##### Example Usage

Rename the snapshot named 'snap1' for the volume named 'test1' to 'snap1_new'.

```sh
netapp_dataops_cli.py rename snapshot --volume=test1 --name=snap1 --new-name=snap1_new 
Renaming snapshot 'snap1' to 'snap1_new'.
Snapshot renamed successfully.
```

<a name="cli-list-snapshots"></a>

#### List All Snapshots for a Data Volume

The NetApp DataOps Toolkit can be used to print a list of all existing snapshots for a specific data volume. The command for printing a list of all snapshots for a specific data volume is `netapp_dataops_cli.py list snapshots`.

The following options/arguments are required:

```
    -v, --volume=   Name of volume.
```
Optional Options/Arguments:
    -u, --cluster-name=     non default hosting cluster
    -s, --svm=      Non default svm.
    -h, --help      Print help text.


##### Example Usage

List all snapshots for the volume named 'test1'.

```sh
netapp_dataops_cli.py list snapshots --volume=test1
Snapshot Name                Create Time
---------------------------  -------------------------
snap1                        2020-11-13 20:17:48+00:00
netapp_dataops_20201113_151807  2020-11-13 20:18:07+00:00
snap3                        2020-11-13 21:43:48+00:00
netapp_dataops_20201113_164402  2020-11-13 21:44:02+00:00
final_dataset                2020-11-13 21:45:16+00:00
```

<a name="cli-restore-snapshot"></a>

#### Restore a Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously restore a specific snapshot for a data volume. This action will restore the volume to its exact state at the time that the snapshot was created. The command for restoring a specific snapshot for a data volume is `netapp_dataops_cli.py restore snapshot`.

Warning: When you restore a snapshot, all subsequent snapshots are deleted.

The following options/arguments are required:

```
    -n, --name=     Name of snapshot to be restored.
    -v, --volume=   Name of volume.
```

The following options/arguments are optional:

```
    -u, --cluster-name=     non default hosting cluster
    -s, --svm=      Non default svm.
    -f, --force     Do not prompt user to confirm operation.
    -h, --help      Print help text.
```

##### Example Usage

Restore the volume 'project2' to its exact state at the time that the snapshot named 'initial_dataset' was created.

Warning: This will delete any snapshots that were created after 'initial_dataset' was created.

```sh
/netapp_dataops_cli.py restore snapshot --volume=project2 --name=initial_dataset
Warning: When you restore a snapshot, all subsequent snapshots are deleted.
Are you sure that you want to proceed? (yes/no): yes
Restoring snapshot 'initial_dataset'.
Snapshot restored successfully.
```

### Data Fabric Operations

<a name="cli-list-cloud-sync-relationships"></a>

#### List All Cloud Sync Relationships

The NetApp DataOps Toolkit can be used to print a list of all existing Cloud Sync relationships that exist under the user's NetApp Cloud Central account. The command for printing a list of all existing Cloud Sync relationships is `netapp_dataops_cli.py list cloud-sync-relationships`.

No options/arguments are required for this command.

Note: To create a new Cloud Sync relationship, visit [cloudsync.netapp.com](https://cloudsync.netapp.com).

##### Example Usage

```sh
netapp_dataops_cli.py list cloud-sync-relationships
- id: 5f4cf53cf7f32c000bc61616
  source:
    nfs:
      export: /iguaziovol01
      host: 172.30.0.4
      path: ''
      provider: nfs
      version: '3'
    protocol: nfs
  target:
    nfs:
      export: /cvs-ab7eaeff7a0843108ec494f7cd0e23c5
      host: 172.30.0.4
      path: ''
      provider: cvs
      version: '3'
    protocol: nfs
- id: 5fe2706697a1892a3ae6db55
  source:
    nfs:
      export: /cloud_sync_source
      host: 192.168.200.41
      path: ''
      provider: nfs
      version: '3'
    protocol: nfs
  target:
    nfs:
      export: /trident_pvc_230358ad_8778_4670_a70e_33327c885c6e
      host: 192.168.200.41
      path: ''
      provider: nfs
      version: '3'
    protocol: nfs
```

<a name="cli-sync-cloud-sync-relationship"></a>

#### Trigger a Sync Operation for an Existing Cloud Sync Relationship

The NetApp DataOps Toolkit can be used to trigger a sync operation for an existing Cloud Sync relationshp under the user's NetApp Cloud Central account. NetApp's Cloud Sync service can be used to replicate data to and from a variety of file and object storage platforms. Potential use cases include the following:

- Replicating newly acquired sensor data gathered at the edge back to the core data center or to the cloud to be used for AI/ML model training or retraining.
- Replicating a newly trained or newly updated model from the core data center to the edge or to the cloud to be deployed as part of an inferencing application.
- Replicating data from an S3 data lake to a high-performance AI/ML training environment for use in the training of an AI/ML model.
- Replicating data from a Hadoop data lake (through Hadoop NFS Gateway) to a high-performance AI/ML training environment for use in the training of an AI/ML model.
- Saving a new version of a trained model to an S3 or Hadoop data lake for permanent storage.
- Replicating NFS-accessible data from a legacy or non-NetApp system of record to a high-performance AI/ML training environment for use in the training of an AI/ML model.

The command for triggering a sync operation for an existing Cloud Sync relationship is `netapp_dataops_cli.py sync cloud-sync-relationship`.

The following options/arguments are required:

```
    -i, --id=       ID of the relationship for which the sync operation is to be triggered.
```

The following options/arguments are optional:

```
    -h, --help      Print help text.
    -w, --wait      Wait for sync operation to complete before exiting.
```

Tip: Run `netapp_dataops_cli.py list cloud-sync-relationships` to obtain the relationship ID.

Note: To create a new Cloud Sync relationship, visit [cloudsync.netapp.com](https://cloudsync.netapp.com).

##### Example Usage

```sh
netapp_dataops_cli.py sync cloud-sync-relationship --id=5fe2706697a1892a3ae6db55 --wait
Triggering sync operation for Cloud Sync relationship (ID = 5fe2706697a1892a3ae6db55).
Sync operation successfully triggered.
Sync operation is not yet complete. Status: RUNNING
Checking again in 60 seconds...
Sync operation is not yet complete. Status: RUNNING
Checking again in 60 seconds...
Sync operation is not yet complete. Status: RUNNING
Checking again in 60 seconds...
Success: Sync operation is complete.
```

<a name="cli-pull-from-s3-bucket"></a>

#### Pull the Contents of a Bucket from S3 (multithreaded)

The NetApp DataOps Toolkit can be used to pull the contents of a bucket from S3. The command for pulling the contents of a bucket from S3 is `netapp_dataops_cli.py pull-from-s3 bucket`.

Note: To pull to a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

The following options/arguments are required:

```
    -b, --bucket=           S3 bucket to pull from.
    -d, --directory=        Local directory to save contents of bucket to.
```

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -p, --key-prefix=       Object key prefix (pull will be limited to objects with key that starts with this prefix).
```

##### Example Usage

Pull all objects in S3 bucket 'project1' and save them to a directory named 'testdl/' on data volume 'project1', which is mounted locally at './test_scripts/test_data/'.

```sh
netapp_dataops_cli.py pull-from-s3 bucket --bucket=project1 --directory=./test_scripts/test_data/testdl
Downloading object 'test1.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test1.csv'.
Downloading object 'test2/dup/test3.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/dup/test3.csv'.
Downloading object 'test2/dup/test2.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/dup/test2.csv'.
Downloading object 'test2/test3/test3.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/test3/test3.csv'.
Downloading object 'test2/test2.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/test2.csv'.
Download complete.
```

Pull all objects in S3 bucket 'project1' with a key that starts with 'test2/', and save them to local directory './test_scripts/test_data/testdl/'.

```sh
netapp_dataops_cli.py pull-from-s3 bucket --bucket=project1 --key-prefix=test2/ --directory=./test_scripts/test_data/testdl
Downloading object 'test2/dup/test3.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/dup/test3.csv'.
Downloading object 'test2/test3/test3.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/test3/test3.csv'.
Downloading object 'test2/test2.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/test2.csv'.
Downloading object 'test2/dup/test2.csv' from bucket 'project1' and saving as './test_scripts/test_data/testdl/test2/dup/test2.csv'.
Download complete.
```

<a name="cli-pull-from-s3-object"></a>

#### Pull an Object from S3

The NetApp DataOps Toolkit can be used to pull an object from S3. The command for pulling an object from S3 is `netapp_dataops_cli.py pull-from-s3 object`.

Note: To pull toa data volume, the volume must be mounted locally.

The following options/arguments are required:

```
    -b, --bucket=           S3 bucket to pull from.
    -k, --key=              Key of S3 object to pull.
```

The following options/arguments are optional:

```
    -f, --file=             Local filepath (including filename) to save object to (if not specified, value of -k/--key argument will be used)
    -h, --help              Print help text.
```

##### Example Usage

Pull the object 'test1.csv' from S3 bucket 'testbucket' and save locally as './test_scripts/test_data/test.csv'.

```sh
netapp_dataops_cli.py pull-from-s3 object --bucket=testbucket --key=test1.csv --file=./test_scripts/test_data/test.csv
Downloading object 'test1.csv' from bucket 'testbucket' and saving as './test_scripts/test_data/test.csv'.
Download complete.
```

<a name="cli-push-to-s3-directory"></a>

#### Push the Contents of a Directory to S3 (multithreaded)

The NetApp DataOps Toolkit can be used to push the contents of a directory to S3. The command for pushing the contents of a directory to S3 is `netapp_dataops_cli.py push-to-s3 directory`.

Note: To push from a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

The following options/arguments are required:

```
    -b, --bucket=           S3 bucket to push to.
    -d, --directory=        Local directory to push contents of.
```

The following options/arguments are optional:

```
    -e, --extra-args        Extra args to apply to newly-pushed S3 objects (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
    -h, --help              Print help text.
    -p, --key-prefix=       Prefix to add to key for newly-pushed S3 objects (Note: by default, key will be local filepath relative to directory being pushed).
```

##### Example Usage

Push the contents of data volume 'project1', which is mounted locally at 'project1_data/', to S3 bucket 'ailab'; apply the prefix 'test/' to all object keys.

```sh
netapp_dataops_cli.py push-to-s3 directory --bucket=ailab --directory=project1_data/ --key-prefix=proj1/
Uploading file 'project1_data/test2/test3/test3.csv' to bucket 'ailab' and applying key 'proj1/test2/test3/test3.csv'.
Uploading file 'project1_data/test2/dup/test3.csv' to bucket 'ailab' and applying key 'proj1/test2/dup/test3.csv'.
Uploading file 'project1_data/test2/test2.csv' to bucket 'ailab' and applying key 'proj1/test2/test2.csv'.
Uploading file 'project1_data/test2/dup/test2.csv' to bucket 'ailab' and applying key 'proj1/test2/dup/test2.csv'.
Uploading file 'project1_data//test1.csv' to bucket 'ailab' and applying key 'proj1/test1.csv'.
Upload complete.
```

Push the contents of the local directory 'test_data/' to S3 bucket 'testbucket'.

```sh
netapp_dataops_cli.py push-to-s3 directory --bucket=testbucket --directory=test_data/
Uploading file 'test_data/test2/test3/test3.csv' to bucket 'testbucket' and applying key 'test2/test3/test3.csv'.
Uploading file 'test_data/test2/dup/test3.csv' to bucket 'testbucket' and applying key 'test2/dup/test3.csv'.
Uploading file 'test_data/test2/test2.csv' to bucket 'testbucket' and applying key 'test2/test2.csv'.
Uploading file 'test_data/test2/dup/test2.csv' to bucket 'testbucket' and applying key 'test2/dup/test2.csv'.
Uploading file 'test_data//test1.csv' to bucket 'testbucket' and applying key 'test1.csv'.
Upload complete.
```

<a name="cli-push-to-s3-file"></a>

#### Push a File to S3

The NetApp DataOps Toolkit can be used to push a file to S3. The command for pushing a file to S3 is `netapp_dataops_cli.py push-to-s3 file`.

Note: To push from a data volume, the volume must be mounted locally.

The following options/arguments are required:

```
    -b, --bucket=           S3 bucket to push to.
    -f, --file=             Local file to push.
```

The following options/arguments are optional:

```
    -e, --extra-args        Extra args to apply to newly-pushed S3 object (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
    -h, --help              Print help text.
    -k, --key=              Key to assign to newly-pushed S3 object (if not specified, key will be set to value of -f/--file argument).
```

##### Example Usage

Push the file 'test_scripts/test_data/test1.csv' to S3 bucket 'testbucket'; assign the key 'test1.csv' to the newly-pushed object.

```sh
netapp_dataops_cli.py push-to-s3 file --bucket=testbucket --file=test_scripts/test_data/test1.csv --key=test1.csv
Uploading file 'test_scripts/test_data/test1.csv' to bucket 'testbucket' and applying key 'test1.csv'.
Upload complete.
```

### Advanced Data Fabric Operations

<a name="cli-prepopulate-flexcache"></a>

#### Prepopulate Specific Files/Directories on a FlexCache Volume

The NetApp DataOps Toolkit can be used to prepopulate specific files/directories on a FlexCache volume. This can be usefule when you have a FlexCache volume acting as a local cache for a remote volume, and you want to prepopulate (i.e. hydrate) the cache with specific files/directories. The command for prepopulating specific files/directories on a FlexCache volume is `netapp_dataops_cli.py prepopulate flexcache`.

Compatibility: ONTAP 9.8 and above ONLY

The following options/arguments are required:

```
    -n, --name=     Name of FlexCache volume.
    -p, --paths=    Comma-separated list of dirpaths/filepaths to prepopulate.
```

##### Example Usage

Prepopulate the file '/test2/test2.csv' and the contents of the directory '/test2/misc' on a FlexCache volume named 'flexcache_cach'.

```sh
netapp_dataops_cli.py prepopulate flexcache --name=flexcache_cache --paths=/test2/misc,/test2/test2.csv
FlexCache 'flexcache_cache' - Prepopulating paths:  ['/test2/misc', '/test2/test2.csv']
FlexCache prepopulated successfully.
```

<a name="cli-list-snapmirror-relationships"></a>

#### List All SnapMirror Relationships

The NetApp DataOps Toolkit can be used to print a list of all existing SnapMirror relationships for which the destination volume resides on the user's storage system. The command for printing a list of all existing SnapMirror relationships is `netapp_dataops_cli.py list snapmirror-relationships`.

Optional Options/Arguments:
    -u, --cluster-name=     non default hosting cluster
    -s, --svm=      Non default svm.
    -h, --help      Print help text.


Note: To create a new SnapMirror relationship, access ONTAP System Manager.

##### Example Usage

```sh
netapp_dataops_cli.py list snapmirror-relationships
UUID                                  Type    Healthy    Current Transfer Status    Source Cluster    Source SVM    Source Volume    Dest Cluster    Dest SVM    Dest Volume
------------------------------------  ------  ---------  -------------------------  ----------------  ------------  ---------------  --------------  ----------  -------------
9e8d14c8-359d-11eb-b94d-005056935ebe  async   True       <NA>                       user's cluster    ailab1        sm01             user's cluster  ailab1      vol_sm01_dest
```

<a name="cli-sync-snapmirror-relationship"></a>

#### Trigger a Sync Operation for an Existing SnapMirror Relationship

The NetApp DataOps Toolkit can be used to trigger a sync operation for an existing SnapMirror relationshp for which the destination volume resides on the user's storage system. NetApp's SnapMirror volume replication technology can be used to quickly and efficiently replicate data between NetApp storage systems. For example, SnapMirror could be used to replicate newly acquired data, gathered on a different NetApp storage system, to the user's NetApp storage system to be used for AI/ML model training or retraining. The command for triggering a sync operation for an existing SnapMirror relationship is `netapp_dataops_cli.py sync snapmirror-relationship`.

Tip: Run `netapp_dataops_cli.py list snapmirror-relationships` to obtain the relationship UUID.

The following options/arguments are required:

```
    -i, --uuid=     UUID of the relationship for which the sync operation is to be triggered.
or
    -n, --name=     Name of target volume to be sync .
```

Optional Options/Arguments:
```
    -u, --cluster-name=     non default hosting cluster
    -v, --svm=              non default target SVM name
    -h, --help              Print help text.
    -w, --wait              Wait for sync operation to complete before exiting.
```

Note: To create a new SnapMirror relationship, access ONTAP System Manager or use the create snapmirror-relationship command.

##### Example Usage

```sh
netapp_dataops_cli.py sync snapmirror-relationship --uuid=132aab2c-4557-11eb-b542-005056932373 --wait
Triggering sync operation for SnapMirror relationship (UUID = 132aab2c-4557-11eb-b542-005056932373).
Sync operation successfully triggered.
Waiting for sync operation to complete.
Status check will be performed in 10 seconds...
Sync operation is not yet complete. Status: transferring
Checking again in 60 seconds...
Success: Sync operation is complete.
```

<a name="cli-create-snapmirror-relationships"></a>
#### Create New SnapMirror Relationship

The NetApp DataOps Toolkit can be used to create SnapMirror relationshp for which the destination volume resides on the user's storage system. NetApp's SnapMirror volume replication technology can be used to quickly and efficiently replicate data between NetApp storage systems. For example, SnapMirror could be used to replicate newly acquired data, gathered on a different NetApp storage system, to the user's NetApp storage system to be used for AI/ML model training or retraining. The command can create relationship and initialize/resync the relationship. The command for create new SnapMirror relationship is `netapp_dataops_cli.py create snapmirror-relationship`.


The following options/arguments are required:

```
    -n, --target-vol=       Name of target volume
    -s, --source-svm=       Source SVM name
    -v, --source-vol=       Source volume name
```

Optional Options/Arguments:
```
    -u, --cluster-name=     non default hosting cluster
    -t, --target-svm=       non default target SVM
    -c, --schedule= non default schedule (default is hourly)
    -p, --policy=   non default policy (default is MirrorAllSnapshots
    -a, --action=   resync,initialize following creation
    -h, --help      Print help text.
```

##### Example Usage

```sh
netapp_dataops_cli.py create snapmirror-relationship --cluster-name=cluster1 --source-svm=svm1 --target-svm=svm2 --source-vol=vol1 --target-vol=vol1 --schedule=daily --policy=MirrorAllSnapshots -a resync
Creating snapmirror relationship: svm1:vol1 -> svm2:vol1
Setting snapmirror policy as: MirrorAllSnapshots schedule:daily
Setting state to snapmirrored, action:resync
```

<a name="library-of-functions"></a>

## Advanced: Importable Library of Functions

The NetApp DataOps Toolkit can also be utilized as a library of functions that can be imported into any Python program or Jupyter Notebook. In this manner, data scientists and data engineers can easily incorporate data management tasks into their existing projects, programs, and workflows. This functionality is only recommended for advanced users who are proficient in Python.

```py
from netapp_dataops.traditional import clone_volume, create_volume, delete_volume, list_volumes, mount_volume, create_snapshot, delete_snapshot, rename_snapshot, list_snapshots, restore_snapshot, list_cloud_sync_relationships, sync_cloud_sync_relationship, list_snap_mirror_relationships, sync_snap_mirror_relationship, create_snap_mirror_relationship, prepopulate_flex_cache, push_directory_to_s3, push_file_to_s3, pull_bucket_from_s3, pull_object_from_s3
```

Note: The prerequisite steps outlined in the [Getting Started](#getting-started) section still appy when the toolkit is being utilized as an importable library of functions.

When being utilized as an importable library of functions, the toolkit supports the following operations.

Data volume management operations:
- [Clone a data volume.](#lib-clone-volume)
- [Create a new data volume.](#lib-create-volume)
- [Delete an existing data volume.](#lib-delete-volume)
- [List all data volumes.](#lib-list-volumes)
- [Mount an existing data volume locally as read-only or read-write.](#lib-mount-volume)
- [Unmount an existing data volume.](#lib-unmount-volume)

Snapshot management operations:
- [Create a new snapshot for a data volume.](#lib-create-snapshot)
- [Delete an existing snapshot for a data volume.](#lib-delete-snapshot)
- [Rename an existing snapshot for a data volume.](#lib-rename-snapshot)
- [List all snapshots for a data volume.](#lib-list-snapshots)
- [Restore a snapshot for a data volume.](#lib-restore-snapshot)

Data fabric operations:
- [List all Cloud Sync relationships.](#lib-list-cloud-sync-relationships)
- [Trigger a sync operation for an existing Cloud Sync relationship.](#lib-sync-cloud-sync-relationship)
- [Pull the contents of a bucket from S3 (multithreaded).](#lib-pull-from-s3-bucket)
- [Pull an object from S3.](#lib-pull-from-s3-object)
- [Push the contents of a directory to S3 (multithreaded).](#lib-push-to-s3-directory)
- [Push a file to S3.](#lib-push-to-s3-file)

Advanced data fabric operations:
- [Prepopulate specific files/directories on a FlexCache volume (ONTAP 9.8 and above ONLY).](#lib-prepopulate-flexcache)
- [List all SnapMirror relationships.](#lib-list-snapmirror-relationships)
- [Trigger a sync operation for an existing SnapMirror relationship.](#lib-sync-snapmirror-relationship)
- [Create SnapMirror relationship.](#lib-create-snapmirror-relationship)

### Examples

[Examples.ipynb](Examples.ipynb) is a Jupyter Notebook that contains examples that demonstrate how the NetApp DataOps Toolkit can be utilized as an importable library of functions.

### Data Volume Management Operations

<a name="lib-clone-volume"></a>

#### Clone a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously create a new data volume that is an exact copy of an existing volume as part of any Python program or workflow. This functionality utilizes NetApp FlexClone technology. This means that any clones created will be extremely storage-space-efficient. Aside from metadata, a clone will not consume additional storage space until its contents starts to deviate from the source volume.

##### Function Definition

```py
def clone_volume(
    new_volume_name: str,                  # Name of new volume (required).
    source_volume_name: str,               # Name of volume to be cloned (required).
    cluster_name: str = None,              # non default cluster name, same credentials as the default credentials should be used 
    source_snapshot_name: str = None,      # Name of the snapshot to be cloned (if specified, the clone will be created from a specific snapshot on the source volume as opposed to the current state of the volume). if snapshot name is suffixed by * the latest snapsho starting with the prefix specified will be used (daily* will use the latest snapshot prefixed by daily)
    source_svm: str = None,                # Name of of the svm hosting the volume to be cloned, when not provided default svm will be used
    target_svm: str = None,                # Name of of the svm hosting the clone. when not provided source svm will be used 
    export_hosts: str = None,              # colon(:) seperated hosts/cidrs to to use for export. hosts will be exported for rw and root access
    export_policy: str = None,             # export policy name to attach to the volume, default policy will be used if export-hosts/export-policy not provided
    snapshot_policy: str = None,           # name of existing snapshot policy to configure on the volume 
    split: bool = False,                   # start clone split after creation
    unix_uid: str = None,                  # Unix filesystem user id (uid) to apply when creating new volume (if not specified, uid of source volume will be retained) (Note: cannot apply uid of '0' when creating clone).
    unix_gid: str = None,                  # Unix filesystem group id (gid) to apply when creating new volume (if not specified, gid of source volume will be retained) (Note: cannot apply gid of '0' when creating clone).
    mountpoint: str = None,                # Local mountpoint to mount new volume at. If not specified, volume will not be mounted locally. On Linux hosts - if specified, calling program must be run as root.
    junction: str= None,                   # Custom junction path for volume to be exported at. If not specified, junction path will be: ("/"+Volume Name).
    readonly: bool = False,                # Option to mount volume locally as "read-only." If not specified volume will be mounted as "read-write". On Linux hosts - if specified, calling program must be run as root.
    refresh: bool = False,                 # when true a previous clone using this name will be deleted prior to the new clone creation
    preserver_msid: bool = False,          # when refreshing clone preserve the original clone msid (can help nfs remount)
    svm_dr_unprotect: bool = False,        # mark the clone created to be excluded from svm-dr replication when onfigured on the clone svm 
    print_output: bool = False             # print log to the console
)
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
InvalidSnapshotParameterError   # An invalid parameter was specified.
MountOperationError             # The volume was not succesfully mounted locally.
```

<a name="lib-create-volume"></a>

#### Create a New Data Volume

The NetApp DataOps Toolkit can be used to rapidly provision a new data volume as part of any Python program or workflow.

##### Function Definition

```py
def create_volume:                   
    volume_name: str,                # Name of new volume (required).
    volume_size: str,                # Size of new volume (required). Format: '1024MB', '100GB', '10TB', etc.
    guarantee_space: bool = False,   # Guarantee sufficient storage space for full capacity of the volume (i.e. do not use thin provisioning).
    cluster_name: str = None,        # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,            # Non default svm name, same credentials as the default credentials should be used 
    volume_type: str = "flexvol",    # Volume type can be flexvol (default) or flexgroup
    unix_permissions: str = "0777",  # Unix filesystem permissions to apply when creating new volume (ex. '0777' for full read/write permissions for all users and groups).  
    unix_uid: str = "0",             # Unix filesystem user id (uid) to apply when creating new volume (ex. '0' for root user).
    unix_gid: str = "0",             # Unix filesystem group id (gid) to apply when creating new volume (ex. '0' for root group).
    export_policy: str = "default",  # NFS export policy to use when exporting new volume.
    snapshot_policy: str = "none",   # Snapshot policy to apply for new volume.
    aggregate: str = None,           # aggregate name or comma seperated aggregates for flexgroup
    mountpoint: str = None,          # Local mountpoint to mount new volume at. If not specified, volume will not be mounted locally. On Linux hosts - if specified, calling program must be run as root.
    junction: str = None,            # Custom junction path for volume to be exported at. If not specified, junction path will be: ("/"+Volume Name).
    readonly: bool = False,          # Mount volume locally as "read-only." If not specified volume will be mounted as "read-write". On Linux hosts - if specified, calling program must be run as root.
    print_output: bool = False,      # Denotes whether or not to print messages to the console during execution.
    tiering_policy: str = None,      # For fabric pool enabled system tiering policy can be: none,auto,snapshot-only,all
    vol_dp: bool = False             # Create volume as type DP which can be used as snapmirror destination
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
MountOperationError             # The volume was not succesfully mounted locally.
```

<a name="lib-delete-volume"></a>

#### Delete an Existing Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing data volume as part of any Python program or workflow.

##### Function Definition

```py
def delete_volume(
    volume_name: str,                # Name of volume (required).
    print_output: bool = False       # Denotes whether or not to print messages to the console during execution.
    cluster_name: str = None,        # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,            # Non default svm name, same credentials as the default credentials should be used 
    delete_mirror: bool = False,     # release snapmirror on source volume/delete snapmirror relation on destination volume
    delete_non_clone: bool = False,  # Enable deletion of non clone volume (extra step not to incedently delete important volume)
    print_output: bool = False       # Denotes whether or not to print messages to the console during execution.
):
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-list-volumes"></a>

#### List All Data Volumes

The NetApp DataOps Toolkit can be used to retrieve a list of all existing data volumes as part of any Python program or workflow.

##### Function Definition

```py
def list_volumes(
    check_local_mounts: bool = False,           # If set to true, then the local mountpoints of any mounted volumes will be included in the returned list and included in printed output.
    include_space_usage_details: bool = False,  # Include storage space usage details in output (see below for explanation).
    cluster_name: str = None,        # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,            # Non default svm name, same credentials as the default credentials should be used    
    print_output: bool = False                  # Denotes whether or not to print messages to the console during execution.
) -> list() :
```

##### Storage Space Usage Details Explanation

If `include_space_usage_details` is set to `True`, then four additional fields will be included in the output. These fields will be labeled with the keys 'Snap Reserve', 'Capacity', 'Usage', and 'Footprint'. These fields and their relation to the 'Size' field are explained in the table below.

| Field         | Explanation                                                                                                                        |
|---------------|------------------------------------------------------------------------------------------------------------------------------------|
| Size          | The logical size of the volume.                                                                                                    |
| Snap Reserve  | The percentage of the volume's logical size that is reserved for snapshot copies.                                                  |
| Capacity      | The logical capacity that is available for users of the volume to store data in.                                                   |
| Usage         | The combined logical size of all of the files that are stored on the volume.                                                       |
| Footprint     | The actual on-disk storage space that is being consumed by the volume after all ONTAP storage efficiencies are taken into account. |

The 'Footprint' value will differ from the 'Usage' value. In some cases, particularly with clone volumes, the 'Footprint' value will be smaller than the 'Usage' value due to ONTAP storage efficiencies. These storage efficiencies include FlexClone technology, deduplication, compression, etc. In the case that the 'Footprint' value is smaller than the 'Usage' value, the delta between the two is a rough representation of the on-disk space savings that you are receiving from ONTAP storage efficiencies.

Note that the 'Footprint' value includes the on-disk storage space that is being consumed by all of the volume's snapshot copies in addition to the on-disk storage space that is being consumed by the data that is currently stored on the volume. If a volume has many snapshots, then the snapshots may represent a large portion of the 'Footprint' value.

Also note that if you are using an ONTAP version earlier than 9.9, then the 'Footprint' value will only be reported for 'flexvol' volumes.

##### Return Value

The function returns a list of all existing volumes. Each item in the list will be a dictionary containing details regarding a specific volume. The keys for the values in this dictionary are "Volume Name", "Logical Size", "Type", "NFS Mount Target", "FlexCache" (yes/no), "Clone" (yes/no), "Source Volume", "Source Snapshot". If `check_local_mounts` is set to `True`, then "Local Mountpoint" will also be included as a key in the dictionary. If `include_space_usage_details` is set to `True`, then "Snap Reserve", "Capacity", "Usage", and "Footprint" will also be included as keys in the dictionary.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
```

<a name="lib-mount-volume"></a>

#### Mount an Existing Data Volume Locally

The NetApp DataOps Toolkit can be used to mount an existing data volume as "read-only" or "read-write" on your local host as part of any Python program or workflow. On Linux hosts, mounting requires root privileges, so any Python program that invokes this function must be run as root. It is usually not necessary to invoke this function as root on macOS hosts.

##### Function Definition

```py
def mount_volume(
    volume_name: str,           # Name of volume (required).
    cluster_name: str = None,        # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,            # Non default svm name, same credentials as the default credentials should be used    
    mountpoint: str,            # Local mountpoint to mount volume at (required).
    readonly: bool = False,     # Mount volume locally as "read-only." If not specified volume will be mounted as "read-write". On Linux hosts - if specified, calling program must be run as root.
    print_output: bool = False  # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
MountOperationError             # The volume was not succesfully mounted locally.
```

<a name="lib-unmount-volume"></a>

#### Unmount an Existing Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously unmount an existing data volume (that is currently mounted on your local host) as part of any Python program or workflow.

##### Function Definition

```py
def unmount_volume(
    mountpoint: str,             # Mountpoint location (required).
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

### Snapshot Management Operations

<a name="lib-create-snapshot"></a>

#### Create a New Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing data volume as part of any Python program or workflow. These read-only copies are called snapshots. This functionality can be used to version datasets and/or implement dataset-to-model traceability.

##### Function Definition

```py
def create_snapshot(
    volume_name: str,                    # Name of volume (required).
    snapshot_name: str = None,           # Name of new snapshot. If not specified, will be set to 'netapp_dataops_<timestamp>'. if retention specified snapshot name will be the prefix for the snapshot.    
    cluster_name: str = None,            # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,                # Non default svm name, same credentials as the default credentials should be used
    retention_count: int = 0,            # the amount of snapshots to keep. excesive snapshots will be deleted
    retention_days: bool = False,        # when true the retention count will represent number of days
    snapmirror_label: str = None,        # when provided snapmirror label will be set on the snapshot created. this is usefull when the volume is source for vault snapmirror 
    print_output: bool = False           # Denotes whether or not to print messages to the console during execution.

) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-delete-snapshot"></a>

#### Delete an Existing Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing snapshot for a specific data volume as part of any Python program or workflow.

##### Function Definition

```py
def delete_snapshot(
    volume_name: str,            # Name of volume (required).
    snapshot_name: str,          # Name of snapshot to be deleted (required).
    cluster_name: str = None,    # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,        # Non default svm name, same credentials as the default credentials should be used    
    skip_owned: bool = False,    # When True snapshot with owners will not be deleted and will not cause an error
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidSnapshotParameterError   # An invalid parameter was specified.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-rename-snapshot"></a>

#### Rename an Existing Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously rename an existing snapshot for a specific data volume as part of any Python program or workflow.

##### Function Definition

```py
def rename_snapshot(
    volume_name: str,              # Name of volume (required).
    snapshot_name: str,            # Name of snapshot to be deleted (required).
    new_snapshot_name: str = None, # When True snapshot with owners will not be deleted and will not cause an error
    cluster_name: str = None,      # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,          # Non default svm name, same credentials as the default credentials should be used    
    print_output: bool = False     # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidSnapshotParameterError   # An invalid parameter was specified.
InvalidVolumeParameterError     # An invalid parameter was specified.
```


<a name="lib-list-snapshots"></a>

#### List All Existing Snapshots for a Data Volume

The NetApp DataOps Toolkit can be used to retrieve a list of all existing snapshots for a specific data volume as part of any Python program or workflow.

##### Function Definition

```py
def list_snapshots(
    volume_name: str,            # Name of volume.
    cluster_name: str = None,    # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,        # Non default svm name, same credentials as the default credentials should be used    
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) -> list() :
```

##### Return Value

The function returns a list of all existing snapshots for the specific data volume. Each item in the list will be a dictionary containing details regarding a specific snapshot. The keys for the values in this dictionary are "Snapshot Name", "Create Time".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-restore-snapshot"></a>

#### Restore a Snapshot for a Data Volume

The NetApp DataOps Toolkit can be used to near-instantaneously restore a specific snapshot for a data volume as part of any Python program or workflow. This action will restore the volume to its exact state at the time that the snapshot was created.

Warning: A snapshot restore operation will delete all snapshots that were created after the snapshot that you are restoring.

##### Function Definition

```py
def restore_snapshot(
    volume_name: str,            # Name of volume (required).
    snapshot_name: str,          # Name of snapshot to be restored (required).
    cluster_name: str = None,    # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,        # Non default svm name, same credentials as the default credentials should be used    
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidSnapshotParameterError   # An invalid parameter was specified.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

### Data Fabric Operations

<a name="lib-list-cloud-sync-relationships"></a>

#### List All Cloud Sync Relationships

The NetApp DataOps Toolkit can be used to retrieve a list of all existing Cloud Sync relationships that exist under the user's NetApp Cloud Central account, as part of any Python program or workflow.

Note: To create a new Cloud Sync relationship, visit [cloudsync.netapp.com](https://cloudsync.netapp.com).

##### Function Definition

```py
def list_cloud_sync_relationships(
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) -> list() :
```

##### Return Value

The function returns a list of all existing Cloud Sync relationships. Each item in the list will be a dictionary containing details regarding a specific Cloud Sync relationship. The keys for the values in this dictionary are "id", "source", "target".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The Cloud Sync API returned an error.
```

<a name="lib-sync-cloud-sync-relationship"></a>

#### Trigger a Sync Operation for an Existing Cloud Sync Relationship

The NetApp DataOps Toolkit can be used to trigger a sync operation for an existing Cloud Sync relationshp under the user's NetApp Cloud Central account, as part of any Python program or workflow. NetApp's Cloud Sync service can be used to replicate data to and from a variety of file and object storage platforms. Potential use cases include the following:

- Replicating newly acquired sensor data gathered at the edge back to the core data center or to the cloud to be used for AI/ML model training or retraining.
- Replicating a newly trained or newly updated model from the core data center to the edge or to the cloud to be deployed as part of an inferencing application.
- Replicating data from an S3 data lake to a high-performance AI/ML training environment for use in the training of an AI/ML model.
- Replicating data from a Hadoop data lake (through Hadoop NFS Gateway) to a high-performance AI/ML training environment for use in the training of an AI/ML model.
- Saving a new version of a trained model to an S3 or Hadoop data lake for permanent storage.
- Replicating NFS-accessible data from a legacy or non-NetApp system of record to a high-performance AI/ML training environment for use in the training of an AI/ML model.

Tip: Use the listCloudSyncRelationships() function to obtain the relationship ID.

Note: To create a new Cloud Sync relationship, visit [cloudsync.netapp.com](https://cloudsync.netapp.com).

##### Function Definition

```py
def sync_cloud_sync_relationship(
    relationship_id: str,                # ID of the relationship for which the sync operation is to be triggered (required).
    wait_until_complete: bool = False,   # Denotes whether or not to wait for sync operation to complete before returning.
    print_output: bool = False           # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The Cloud Sync API returned an error.
CloudSyncSyncOperationError     # The sync operation failed.
```

<a name="lib-pull-from-s3-bucket"></a>

#### Pull the Contents of a Bucket S3 (multithreaded)

The NetApp DataOps Toolkit can be used to pull the contents of a bucket from S3 as part of any Python program or workflow.

Note: To pull to a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

##### Function Definition

```py
def pull_bucket_from_s3(
    s3_bucket: str,                  # S3 bucket to pull from (required).
    local_directory: str,            # Local directory to save contents of bucket to (required).
    s3_object_key_prefix: str = "",  # Object key prefix (pull will be limited to objects with key that starts with this prefix).
    print_output: bool = False       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The S3 API returned an error.
```

<a name="lib-pull-from-s3-object"></a>

#### Pull an Object from S3

The NetApp DataOps Toolkit can be used to pull an object from S3 as part of any Python program or workflow.

Note: To pull to a data volume, the volume must be mounted locally.

##### Function Definition

```py
def pull_object_from_s3(
    s3_bucket: str,              # S3 bucket to pull from. (required).
    s3_object_key: str,          # Key of S3 object to pull (required).
    local_file: str = None,      # Local filepath (including filename) to save object to (if not specified, value of s3_object_key argument will be used).
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The S3 API returned an error.
```

<a name="lib-push-to-s3-directory"></a>

#### Push the Contents of a Directory to S3 (multithreaded)

The NetApp DataOps Toolkit can be used to push the contents of a directory to S3 as part of any Python program or workflow.

Note: To push from a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

##### Function Definition

```py
def push_directory_to_s3(
    s3_bucket: str,                  # S3 bucket to push to (required).
    local_directory: str,            # Local directory to push contents of (required).
    s3_object_key_prefix: str = "",  # Prefix to add to key for newly-pushed S3 objects (Note: by default, key will be local filepath relative to directory being pushed).
    s3_extra_args: str = None,       # Extra args to apply to newly-pushed S3 objects (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
    print_output: bool = False       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The S3 API returned an error.
```

<a name="lib-push-to-s3-file"></a>

#### Push a File to S3

The NetApp DataOps Toolkit can be used to push a file to S3 as part of any Python program or workflow.

Note: To push from a data volume, the volume must be mounted locally.

##### Function Definition

```py
def push_file_to_s3(
    s3_bucket: str,             # S3 bucket to push to (required).
    local_file: str,            # Local file to push (required).
    s3_object_key: str = None,  # Key to assign to newly-pushed S3 object (if not specified, key will be set to value of local_file).
    s3_extra_args: str = None,  # Extra args to apply to newly-pushed S3 object (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
    print_output: bool = False  # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The S3 API returned an error.
```

### Advanced Data Fabric Operations

<a name="lib-prepopulate-flexcache"></a>

#### Prepopulate Specific Files/Directories on a FlexCache Volume

The NetApp DataOps Toolkit can be used to prepopulate specific files/directories on a FlexCache volume as part of any Python program or workflow. This can be usefule when you have a FlexCache volume acting as a local cache for a remote volume, and you want to prepopulate (i.e. hydrate) the cache with specific files/directories.

Compatibility: ONTAP 9.8 and above ONLY

##### Function Definition

```py
def prepopulate_flex_cache(
    volume_name: str,           # Name of FlexCache volume (required).
    paths: list,                # List of dirpaths/filepaths to prepopulate (required).
    print_output: bool = False
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
InvalidVolumeParameterError     # An invalid parameter was specified.
```

<a name="lib-list-snapmirror-relationships"></a>

#### List All SnapMirror Relationships

The NetApp DataOps Toolkit can be used to retrieve a list of all existing SnapMirror relationships for which the destination volume resides on the user's storage system, as part of any Python program or workflow.

Note: To create a new SnapMirror relationship, access ONTAP System Manager.

##### Function Definition

```py
def list_snap_mirror_relationships(
    cluster_name: str = None,    # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,        # Non default svm name, same credentials as the default credentials should be used    
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) -> list() :
```

##### Return Value

The function returns a list of all existing SnapMirror relationships for which the destination volume resides on the user's storage system. Each item in the list will be a dictionary containing details regarding a specific SnapMirror relationship. The keys for the values in this dictionary are "UUID", "Type", "Healthy", "Current Transfer Status", "Source Cluster", "Source SVM", "Source Volume", "Dest Cluster", "Dest SVM", "Dest Volume".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError              # Config file is missing or contains an invalid value.
APIConnectionError              # The storage system/service API returned an error.
```

<a name="lib-sync-snapmirror-relationship"></a>

#### Trigger a Sync Operation for an Existing SnapMirror Relationship

The NetApp DataOps Toolkit can be used to trigger a sync operation for an existing SnapMirror relationshp for which the destination volume resides on the user's storage system, as part of any Python program or workflow. NetApp's SnapMirror volume replication technology can be used to quickly and efficiently replicate data between NetApp storage systems. For example, SnapMirror could be used to replicate newly acquired data, gathered on a different NetApp storage system, to the user's NetApp storage system to be used for AI/ML model training or retraining.

Tip: Use the listSnapMirrorRelationships() function to obtain the UUID.

Note: To create a new SnapMirror relationship, access ONTAP System Manager or use the createSnapMirrorRelationships()

##### Function Definition

```py
def sync_snap_mirror_relationship(
    uuid: str,                          # UUID of the relationship for which the sync operation is to be triggered (required).
    volume_name: str = None             # destination volume name (only when uuid not provided)
    cluster_name: str = None,           # Non default cluster name, same credentials as the default credentials should be used 
    svm_name: str = None,               # Non default svm name, same credentials as the default credentials should be used    
    wait_until_complete: bool = False,  # Denotes whether or not to wait for sync operation to complete before returning.
    print_output: bool = False          # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError                  # Config file is missing or contains an invalid value.
APIConnectionError                  # The storage system/service API returned an error.
SnapMirrorSyncOperationError        # The sync operation failed.
InvalidSnapMirrorParameterError     # An invalid parameter was specified.
```



<a name="lib-create-snapmirror-relationship"></a>

#### Create New SnapMirror Relationship

The NetApp DataOps Toolkit can be used to create SnapMirror relationshp for which the destination volume resides on the user's storage system. NetApp's SnapMirror volume replication technology can be used to quickly and efficiently replicate data between NetApp storage systems. For example, SnapMirror could be used to replicate newly acquired data, gathered on a different NetApp storage system, to the user's NetApp storage system to be used for AI/ML model training or retraining. The command can create relationship and initialize/resync the relationship. 

##### Function Definition

```py
def create_snap_mirror_relationship(
    source_svm: str,                    # snapmirror replication source svm name 
    source_vol: str,                    # snapmirror replication source volume name 
    target_svm: str = None,             # snapmirror replication target svm name 
    target_vol: str,                    # snapmirror replication target volume name, when not provided default svm will be used
    cluster_name: str = None,           # Non default cluster name, same credentials as the default credentials should be used     
    schedule: str = '',                 # name of the schedule to use, when not provided no schedule will be provided 
    policy: str = 'MirrorAllSnapshots', # snapmirror poilcy to use, when not provided MirrorAllSnapshots will be used 
    action: str = None,                 # the action to perform after the creation of the snapmirror relationship. can be: initialize or resync. initialize can be used to initialize new replication (requires destination volume to be of DP type). resync can be used to resync volumes with common snapshot
    print_output: bool = False          # Denotes whether or not to print messages to the console during execution.

) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.traditional`.

```py
InvalidConfigError                  # Config file is missing or contains an invalid value.
APIConnectionError                  # The storage system/service API returned an error.
SnapMirrorSyncOperationError        # The sync operation failed.
InvalidSnapMirrorParameterError     # An invalid parameter was specified.
```



## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
