"""
Help text definitions for NetApp DataOps Toolkit CLI commands.

This module contains all help text strings used by the CLI interface.
Each help text constant provides usage information for a specific command.
"""

# Main help text
HELP_TEXT_STANDARD = '''
The NetApp DataOps Toolkit is a Python library that makes it simple for data scientists and data engineers to perform various data management tasks, such as provisioning a new data volume, near-instantaneously cloning a data volume, and near-instantaneously snapshotting a data volume for traceability/baselining.

Basic Commands:

\tconfig\t\t\t\tCreate a new config file (a config file is required to perform other commands).
\thelp\t\t\t\tPrint help text.
\tversion\t\t\t\tPrint version details.

Data Volume Management Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tclone volume\t\t\tCreate a new data volume that is an exact copy of an existing volume.
\tcreate volume\t\t\tCreate a new data volume.
\tdelete volume\t\t\tDelete an existing data volume.
\tlist volumes\t\t\tList all data volumes.
\tmount volume\t\t\tMount an existing data volume locally. Note: on Linux hosts - must be run as root.
\tunmount volume\t\t\tUnmount an existing data volume. Note: on Linux hosts - must be run as root.

Snapshot Management Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tcreate snapshot\t\t\tCreate a new snapshot for a data volume.
\tdelete snapshot\t\t\tDelete an existing snapshot for a data volume.
\tlist snapshots\t\t\tList all snapshots for a data volume.
\trestore snapshot\t\tRestore a snapshot for a data volume (restore the volume to its exact state at the time that the snapshot was created).

Data Fabric Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tlist cloud-sync-relationships\tList all existing Cloud Sync relationships.
\tsync cloud-sync-relationship\tTrigger a sync operation for an existing Cloud Sync relationship.
\tpull-from-s3 bucket\t\tPull the contents of a bucket from S3.
\tpull-from-s3 object\t\tPull an object from S3.
\tpush-to-s3 directory\t\tPush the contents of a directory to S3 (multithreaded).
\tpush-to-s3 file\t\t\tPush a file to S3.

Advanced Data Fabric Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tprepopulate flexcache\t\tPrepopulate specific files/directories on a FlexCache volume (ONTAP 9.8 and above ONLY).
\tlist snapmirror-relationships\tList all existing SnapMirror relationships.
\tsync snapmirror-relationship\tTrigger a sync operation for an existing SnapMirror relationship.
\tcreate snapmirror-relationship\tCreate new SnapMirror relationship.

CIFS Share Management Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.
\tcreate cifs-share\t\tCreate a new CIFS share.
\tlist cifs-shares\t\tList all CIFS shares.
\tget cifs-share\t\t\tGet details of a specific CIFS share.
'''

# Configuration command help text
HELP_TEXT_CONFIG = '''
Command: config

Create a new config file (a config file is required to perform other commands).

No additional options/arguments required.
'''

# Volume management help text
HELP_TEXT_CLONE_VOLUME = '''
Command: clone volume

Create a new data volume that is an exact copy of an existing volume.

Required Options/Arguments:
\t-n, --name=\t\tName of new volume..
\t-v, --source-volume=\tName of volume to be cloned.

Optional Options/Arguments:
\t-l, --cluster-name=\tnon default hosting cluster
\t-c, --source-svm=\tnon default source svm name
\t-t, --target-svm=\tnon default target svm name
\t-g, --gid=\t\tUnix filesystem group id (gid) to apply when creating new volume (if not specified, gid of source volume will be retained) (Note: cannot apply gid of '0' when creating clone).
\t-h, --help\t\tPrint help text.
\t-m, --mountpoint=\tLocal mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
\t-s, --source-snapshot=\tName of the snapshot to be cloned (if specified, the clone will be created from a specific snapshot on the source volume as opposed to the current state of the volume).
\t\t\t\twhen snapshot name suffixed with * the latest snapshot will be used (hourly* will use the latest snapshot prefixed with hourly )
\t-u, --uid=\t\tUnix filesystem user id (uid) to apply when creating new volume (if not specified, uid of source volume will be retained) (Note: cannot apply uid of '0' when creating clone).
\t-x, --readonly\t\tRead-only option for mounting volumes locally.
\t-j, --junction\t\tSpecify a custom junction path for the volume to be exported at.
\t-e, --export-hosts\tcolon(:) separated hosts/cidrs to use for export. hosts will be exported for rw and root access
\t-e, --export-policy\texport policy name to attach to the volume, default policy will be used if export-hosts/export-policy not provided
\t-d, --snapshot-policy\tsnapshot-policy to attach to the volume, default snapshot policy will be used if not provided
\t-s, --split\t\tstart clone split after creation
\t-r, --refresh\t\tdelete existing clone if exists before creating a new one
\t-d, --svm-dr-unprotect\tdisable svm dr protection if svm-dr protection exists

Examples (basic usage):
\tnetapp_dataops_cli.py clone volume --name=project1 --source-volume=gold_dataset
\tnetapp_dataops_cli.py clone volume -n project2 -v gold_dataset -s snap1
\tnetapp_dataops_cli.py clone volume --name=project1 --source-volume=gold_dataset --mountpoint=~/project1 --readonly


Examples (advanced usage):
\tnetapp_dataops_cli.py clone volume -n testvol -v gold_dataset -u 1000 -g 1000 -x -j /project1 -d snappolicy1
\tnetapp_dataops_cli.py clone volume --name=project1 --source-volume=gold_dataset --source-svm=svm1 --target-svm=svm2 --source-snapshot=daily* --export-hosts 10.5.5.3:host1:10.6.4.0/24 --split
'''

HELP_TEXT_CREATE_VOLUME = '''
Command: create volume

Create a new data volume.

Required Options/Arguments:
\t-n, --name=\t\tName of new volume.
\t-s, --size=\t\tSize of new volume. Format: '1024MB', '100GB', '10TB', etc.

Optional Options/Arguments:
\t-l, --cluster-name=\tnon default hosting cluster
\t-v, --svm=\t\tnon default svm name
\t-a, --aggregate=\tAggregate to use when creating new volume (flexvol) or optional comma separated aggrlist when specific aggregates are required for FG.
\t-d, --snapshot-policy=\tSnapshot policy to apply for new volume.
\t-e, --export-policy=\tNFS export policy to use when exporting new volume.
\t-g, --gid=\t\tUnix filesystem group id (gid) to apply when creating new volume (ex. '0' for root group).
\t-h, --help\t\tPrint help text.
\t-m, --mountpoint=\tLocal mountpoint to mount new volume at after creating. If not specified, new volume will not be mounted locally. On Linux hosts - if specified, must be run as root.
\t-p, --permissions=\tUnix filesystem permissions to apply when creating new volume (ex. '0777' for full read/write permissions for all users and groups).
\t-r, --guarantee-space\tGuarantee sufficient storage space for full capacity of the volume (i.e. do not use thin provisioning).
\t-t, --type=\t\tVolume type to use when creating new volume (flexgroup/flexvol).
\t-u, --uid=\t\tUnix filesystem user id (uid) to apply when creating new volume (ex. '0' for root user).
\t-w, --snaplock-type=\tSnaplock type to apply for new volume. (can be 'compliance','enterprise',None)
\t-x, --readonly\t\tRead-only option for mounting volumes locally.
\t-j, --junction\t\tSpecify a custom junction path for the volume to be exported at.
\t-f, --tiering-policy\tSpecify tiering policy for fabric-pool enabled systems (default is 'none').
\t-y, --dp\t\tCreate volume as DP volume (the volume will be used as snapmirror target)


Examples (basic usage):
\tnetapp_dataops_cli.py create volume --name=project1 --size=10GB
\tnetapp_dataops_cli.py create volume -n datasets -s 10TB
\tsudo -E netapp_dataops_cli.py create volume --name=project2 --size=2TB --mountpoint=~/project2 --readonly

Examples (advanced usage):
\tsudo -E netapp_dataops_cli.py create volume --name=project1 --size=10GB --permissions=0755 --type=flexvol --mountpoint=~/project1 --readonly --junction=/project1
\tsudo -E netapp_dataops_cli.py create volume --name=project2_flexgroup --size=2TB --type=flexgroup --mountpoint=/mnt/project2
\tnetapp_dataops_cli.py create volume --name=testvol --size=10GB --type=flexvol --aggregate=n2_data
\tnetapp_dataops_cli.py create volume -n testvol -s 10GB -t flexvol -p 0755 -u 1000 -g 1000 -j /project1
\tsudo -E netapp_dataops_cli.py create volume -n vol1 -s 5GB -t flexvol --export-policy=team1 -m /mnt/vol1
\tnetapp_dataops_cli.py create vol -n test2 -s 10GB -t flexvol --snapshot-policy=default --tiering-policy=auto
\tnetapp_dataops_cli.py create volume --name=project1 --size=100GB --snaplock-type=compliance
'''

HELP_TEXT_DELETE_VOLUME = '''
Command: delete volume

Delete an existing data volume.

Required Options/Arguments:
\t-n, --name=\tName of volume to be deleted.

Optional Options/Arguments:
\t-u, --cluster-name=\tnon default hosting cluster
\t-v, --svm \t\tnon default SVM name
\t-f, --force\t\tDo not prompt user to confirm operation.
\t-m, --delete-mirror\tdelete/release snapmirror relationship prior to volume deletion
\t    --delete-non-clone\tEnable deletion of volume not created as clone by this tool
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py delete volume --name=project1
\tnetapp_dataops_cli.py delete volume -n project2
'''

HELP_TEXT_LIST_VOLUMES = '''
Command: list volumes

List all data volumes.

No options/arguments are required.

Optional Options/Arguments:
\t-u, --cluster-name=\t\t\tnon default hosting cluster
\t-v, --svm=\t\t\t\tlist volume on non default svm
\t-h, --help\t\t\t\tPrint help text.
\t-s, --include-space-usage-details\tInclude storage space usage details in output (see README for explanation).

Examples:
\tnetapp_dataops_cli.py list volumes
\tnetapp_dataops_cli.py list volumes --include-space-usage-details
'''

HELP_TEXT_MOUNT_VOLUME = '''
Command: mount volume

Mount an existing data volume locally.

Requirement: On Linux hosts, must be run as root.

Required Options/Arguments:
\t-m, --mountpoint=\tLocal mountpoint to mount volume at.
\t-n, --name=\t\tName of volume.

Optional Options/Arguments:
\t-v, --svm \t\tnon default SVM name
\t-l, --lif \t\tnon default lif (nfs server ip/name)
\t-h, --help\t\tPrint help text.
\t-x, --readonly\t\tMount volume locally as read-only.
\t-o, --options\t\tSpecify custom NFS mount options.

Examples:
\tsudo -E netapp_dataops_cli.py mount volume --name=project1 --mountpoint=/mnt/project1
\tsudo -E netapp_dataops_cli.py mount volume -m ~/testvol -n testvol -x
\tsudo -E netapp_dataops_cli.py mount volume --name=project1 --mountpoint=/mnt/project1 --readonly
\tsudo -E netapp_dataops_cli.py mount volume --name=project1 --mountpoint=/mnt/project1 --readonly --options=rsize=262144,wsize=262144,nconnect=16
'''

HELP_TEXT_UNMOUNT_VOLUME = '''
Command: unmount volume

Unmount an existing data volume that is currently mounted locally.

Required Options/Arguments:
\t-m, --mountpoint=\tMountpoint where volume is mounted at.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py unmount volume --mountpoint=/project2
\tnetapp_dataops_cli.py unmount volume -m /project2
'''

# Snapshot management help text
HELP_TEXT_CREATE_SNAPSHOT = '''
Command: create snapshot

Create a new snapshot for a data volume.

Required Options/Arguments:
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-u, --cluster-name=\tnon default hosting cluster
\t-s, --svm=\t\tNon default svm name.
\t-h, --help\t\tPrint help text.
\t-n, --name=\t\tName of new snapshot. If not specified, will be set to 'netapp_dataops_<timestamp>'.
\t-r, --retention=\tSnapshot name will be suffixed by <timestamp> and excessive snapshots will be deleted.
\t                \tCan be count of snapshots when int (ex. 10) or days when retention is suffixed by d (ex. 10d)
\t-l, --snapmirror-label=\tif provided snapmirror label will be configured on the created snapshot

Examples:
\tnetapp_dataops_cli.py create snapshot --volume=project1 --name=snap1
\tnetapp_dataops_cli.py create snapshot -v project2 -n final_dataset
\tnetapp_dataops_cli.py create snapshot --volume=test1
\tnetapp_dataops_cli.py create snapshot -v project2 -n daily_consistent -r 7 -l daily
\tnetapp_dataops_cli.py create snapshot -v project2 -n daily_for_month -r 30d -l daily
'''

HELP_TEXT_DELETE_SNAPSHOT = '''
Command: delete snapshot

Delete an existing snapshot for a data volume.

Required Options/Arguments:
\t-n, --name=\tName of snapshot to be deleted.
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-u, --cluster-name=\tNon default hosting cluster
\t-s, --svm=\t\tNon default svm
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py delete snapshot --volume=project1 --name=snap1
\tnetapp_dataops_cli.py delete snapshot -v project2 -n netapp_dataops_20201113_221917
'''

HELP_TEXT_LIST_SNAPSHOTS = '''
Command: list snapshots

List all snapshots for a data volume.

Required Options/Arguments:
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-u, --cluster-name=\tNon default hosting cluster
\t-s, --svm=\t\tNon default svm.
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py list snapshots --volume=project1
\tnetapp_dataops_cli.py list snapshots -v test1
'''

HELP_TEXT_RESTORE_SNAPSHOT = '''
Command: restore snapshot

Restore a snapshot for a data volume (restore the volume to its exact state at the time that the snapshot was created).

Required Options/Arguments:
\t-n, --name=\tName of snapshot to be restored.
\t-v, --volume=\tName of volume.

Optional Options/Arguments:
\t-u, --cluster-name=\tNon default hosting cluster
\t-s, --svm=\t\tNon default svm.
\t-f, --force\t\tDo not prompt user to confirm operation.
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py restore snapshot --volume=project1 --name=snap1
\tnetapp_dataops_cli.py restore snapshot -v project2 -n netapp_dataops_20201113_221917
'''

# SnapMirror management help text
HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP = '''
Command: create snapmirror-relationship

create snapmirror relationship

Required Options/Arguments:
\t-n, --target-vol=\tName of target volume
\t-s, --source-svm=\tSource SVM name
\t-v, --source-vol=\tSource volume name

Optional Options/Arguments:
\t-u, --cluster-name=\tnon default hosting cluster
\t-t, --target-svm=\tnon default target SVM
\t-c, --schedule=\t\tnon default schedule (default is hourly)
\t-p, --policy=\t\tnon default policy (default is MirrorAllSnapshots
\t-a, --action=\t\tresync,initialize following creation
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py create snapmirror-relationship -u cluster1 -s svm1 -t svm2 -v vol1 -n vol1 -p MirrorAllSnapshots -c hourly
\tnetapp_dataops_cli.py create snapmirror-relationship -u cluster1 -s svm1 -t svm2 -v vol1 -n vol1 -p MirrorAllSnapshots -c hourly -a resync
'''

HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS = '''
Command: list snapmirror-relationships

List all SnapMirror relationships.

Optional Options/Arguments:
\t-u, --cluster-name=\tNon default hosting cluster
\t-s, --svm=\t\tNon default svm.
\t-h, --help\t\tPrint help text.
'''

HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP = '''
Command: sync snapmirror-relationship

Trigger a sync operation for an existing SnapMirror relationship.

Tip: Run `netapp_dataops_cli.py list snapmirror-relationships` to obtain relationship UUID.

Required Options/Arguments:
\t-i, --uuid=\tUUID of the relationship for which the sync operation is to be triggered.
or
\t-n, --name=\tName of target volume to be sync .

Optional Options/Arguments:
\t-u, --cluster-name=\tnon default hosting cluster
\t-v, --svm \t\tnon default target SVM name
\t-h, --help\t\tPrint help text.
\t-w, --wait\t\tWait for sync operation to complete before exiting.

Examples:
\tnetapp_dataops_cli.py sync snapmirror-relationship --uuid=132aab2c-4557-11eb-b542-005056932373
\tnetapp_dataops_cli.py sync snapmirror-relationship -i 132aab2c-4557-11eb-b542-005056932373 -w
\tnetapp_dataops_cli.py sync snapmirror-relationship -u cluster1 -v svm1 -n vol1 -w
'''

# Cloud Sync management help text
HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS = '''
Command: list cloud-sync-relationships

List all existing Cloud Sync relationships.

No additional options/arguments required.
'''

HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP = '''
Command: sync cloud-sync-relationship

Trigger a sync operation for an existing Cloud Sync relationship.

Tip: Run `netapp_dataops_cli.py list cloud-sync-relationships` to obtain relationship ID.

Required Options/Arguments:
\t-i, --id=\tID of the relationship for which the sync operation is to be triggered.

Optional Options/Arguments:
\t-h, --help\tPrint help text.
\t-w, --wait\tWait for sync operation to complete before exiting.

Examples:
\tnetapp_dataops_cli.py sync cloud-sync-relationship --id=5ed00996ca85650009a83db2
\tnetapp_dataops_cli.py sync cloud-sync-relationship -i 5ed00996ca85650009a83db2 -w
'''

# S3 operations help text
HELP_TEXT_PULL_FROM_S3_BUCKET = '''
Command: pull-from-s3 bucket

Pull the contents of a bucket from S3 (multithreaded).

Note: To pull to a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to pull from.
\t-d, --directory=\tLocal directory to save contents of bucket to.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.
\t-p, --key-prefix=\tObject key prefix (pull will be limited to objects with key that starts with this prefix).

Examples:
\tnetapp_dataops_cli.py pull-from-s3 bucket --bucket=project1 --directory=/mnt/project1
\tnetapp_dataops_cli.py pull-from-s3 bucket -b project1 -p project1/ -d ./project1/
'''

HELP_TEXT_PULL_FROM_S3_OBJECT = '''
Command: pull-from-s3 object

Pull an object from S3.

Note: To pull to a data volume, the volume must be mounted locally.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to pull from.
\t-k, --key=\t\tKey of S3 object to pull.

Optional Options/Arguments:
\t-f, --file=\t\tLocal filepath (including filename) to save object to (if not specified, value of -k/--key argument will be used)
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py pull-from-s3 object --bucket=project1 --key=data.csv --file=./project1/data.csv
\tnetapp_dataops_cli.py pull-from-s3 object -b project1 -k data.csv
'''

HELP_TEXT_PUSH_TO_S3_DIRECTORY = '''
Command: push-to-s3 directory

Push the contents of a directory to S3 (multithreaded).

Note: To push from a data volume, the volume must be mounted locally.

Warning: This operation has not been tested at scale and may not be appropriate for extremely large datasets.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to push to.
\t-d, --directory=\tLocal directory to push contents of.

Optional Options/Arguments:
\t-e, --extra-args=\tExtra args to apply to newly-pushed S3 objects (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
\t-h, --help\t\tPrint help text.
\t-p, --key-prefix=\tPrefix to add to key for newly-pushed S3 objects (Note: by default, key will be local filepath relative to directory being pushed).

Examples:
\tnetapp_dataops_cli.py push-to-s3 directory --bucket=project1 --directory=/mnt/project1
\tnetapp_dataops_cli.py push-to-s3 directory -b project1 -d /mnt/project1 -p project1/ -e '{"Metadata": {"mykey": "myvalue"}}'
'''

HELP_TEXT_PUSH_TO_S3_FILE = '''
Command: push-to-s3 file

Push a file to S3.

Note: To push from a data volume, the volume must be mounted locally.

Required Options/Arguments:
\t-b, --bucket=\t\tS3 bucket to push to.
\t-f, --file=\t\tLocal file to push.

Optional Options/Arguments:
\t-e, --extra-args=\tExtra args to apply to newly-pushed S3 object (For details on this field, refer to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html#the-extraargs-parameter).
\t-h, --help\t\tPrint help text.
\t-k, --key=\t\tKey to assign to newly-pushed S3 object (if not specified, key will be set to value of -f/--file argument).

Examples:
\tnetapp_dataops_cli.py push-to-s3 file --bucket=project1 --file=data.csv
\tnetapp_dataops_cli.py push-to-s3 file -b project1 -k data.csv -f /mnt/project1/data.csv -e '{"Metadata": {"mykey": "myvalue"}}'
'''

# FlexCache operations help text
HELP_TEXT_PREPOPULATE_FLEXCACHE = '''
Command: prepopulate flexcache

Prepopulate specific files/directories on a FlexCache volume.

Compatibility: ONTAP 9.8 and above ONLY

Required Options/Arguments:
\t-n, --name=\tName of FlexCache volume.
\t-p, --paths=\tComma-separated list of dirpaths/filepaths to prepopulate.

Optional Options/Arguments:
\t-h, --help\tPrint help text.

Examples:
\tnetapp_dataops_cli.py prepopulate flexcache --name=project1 --paths=/datasets/project1,/datasets/project2
\tnetapp_dataops_cli.py prepopulate flexcache -n test1 -p /datasets/project1,/datasets/project2
'''

# CIFS Share operations help text
HELP_TEXT_CREATE_CIFS_SHARE = '''
Command: create cifs-share

Create a new CIFS share.

Required Options/Arguments:
\t-n, --name=\t\tName of the CIFS share.
\t-v, --volume=\tName of the volume to share.
\t-s, --svm=\t\tExisting SVM in which to create the CIFS share.

Optional Options/Arguments:
\t-u, --cluster-name=\tNon default hosting cluster
\t-c, --comment=\t\tComment/ description for the CIFS share.
\t-a, --acls=\t\tComma-separated list of ACLs to apply to the share. 
\t-l, --properties=\tComma-separated list of properties to apply to the share ('browsable', 'oplocks', 'showsnapshot', 'changenotify', 'attributecache', 'continuously_available', 'encryption').
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py create cifs share --name=cifs-share1 --path=/mnt/project1 
\tnetapp_dataops_cli.py create cifs share -n cifs-share2 -p /mnt/project2
'''

# List CIFS Shares help text
HELP_TEXT_LIST_CIFS_SHARES = '''
Command: list cifs-shares

List all CIFS shares.

Note: Administrative shares (c$, ipc$, admin$, print$) are hidden by default.

Optional Options/Arguments:
\t-s, --svm=\t\tExisting SVM in which to create the CIFS share.
\t-n, --name-pattern=\tPattern to filter share names by (supports wildcard '*').
\t-u, --cluster-name=\tNon default hosting cluster
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py list cifs shares --cluster-name=cluster1
\tnetapp_dataops_cli.py list cifs shares -u cluster1
\tnetapp_dataops_cli.py list cifs-shares --name-pattern="cifs*"
'''

# Get CIFS Share help text
HELP_TEXT_GET_CIFS_SHARE = '''
Command: get cifs-share

Get details of a specific CIFS share.

Required Options/Arguments:
\t-n, --name=\t\tName of the CIFS share to retrieve.
\t-s, --svm=\t\tExisting SVM in which the CIFS share resides.

Optional Options/Arguments:
\t-u, --cluster-name=\tNon default hosting cluster
\t-h, --help\t\tPrint help text.

Examples:
\tnetapp_dataops_cli.py get cifs share --name=cifs-share1
\tnetapp_dataops_cli.py get cifs share -n cifs-share2
'''