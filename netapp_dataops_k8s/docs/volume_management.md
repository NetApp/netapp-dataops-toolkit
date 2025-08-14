# Volume Management with NetApp DataOps Toolkit for Kubernetes

The NetApp DataOps Toolkit for Kubernetes can be used to manage persistent volumes within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new persistent volume, the ability to almost instantaneously clone a persistent volume, and the ability to almost instantaneously save off a snapshot of a persistent volume for traceability/baselining. These volume management capabilities are available within the toolkit's [command line utility](#command-line-functionality) and as a [set of functions](#library-of-functions) that can be imported and used from other Python programs.

<a name="command-line-functionality"></a>

## Command Line Functionality

You can perform volume management operations using the toolkit's command line utility. The command line utility supports the following operations.

| Kubernetes persistent volume management operations                                   | Supported by BeeGFS | Supported by Trident |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- |
| [Clone a persistent volume.](#cli-clone-volume)                                      | No                  | Yes                  |
| [Create a new persistent volume.](#cli-create-volume)                                | Yes                 | Yes                  |
| [Delete an existing persistent volume.](#cli-delete-volume)                          | Yes                 | Yes                  |
| [List all persistent volumes.](#cli-list-volumes)                                    | Yes                 | Yes                  |
| [Create a new snapshot for a persistent volume.](#cli-create-volume-snapshot)        | No                  | Yes                  |
| [Delete an existing snapshot.](#cli-delete-volume-snapshot)                          | No                  | Yes                  |
| [List all snapshots.](#cli-list-volume-snapshots)                                    | No                  | Yes                  |
| [Restore a snapshot.](#cli-restore-volume-snapshot)                                  | No                  | Yes                  |
| [Create a new FlexCache volume](#cli-create-flexcache)                               | No                  | Yes                  |

### Kubernetes Persistent Volume Management Operations

<a name="cli-clone-volume"></a>

#### Clone a Persistent Volume

The NetApp DataOps Toolkit can be used to near-instantaneously provision a new persistent volume (within a Kubernetes cluster) that is an exact copy of an existing persistent volume or snapshot. In other words, the NetApp DataOps Toolkit can be used to near-instantaneously clone a persistent volume. The command for cloning a persistent volume is `netapp_dataops_k8s_cli.py clone volume`.

Note: Either -s/--source-snapshot-name or -v/--source-pvc-name must be specified. However, only one of these flags (not both) should be specified for a given operation. If -v/--source-pvc-name is specified, then the clone will be created from the current state of the volume. If -s/--source-snapshot-name is specified, then the clone will be created from a specific snapshot related the source volume.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

The following options/arguments are required:

```
    -p, --new-pvc-name=             Name of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC).
```

The following options/arguments are optional:

```
    -c, --volume-snapshot-class=    Kubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    -h, --help                      Print help text.
    -n, --namespace=                Kubernetes namespace that source PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    -s, --source-snapshot-name=     Name of Kubernetes VolumeSnapshot to use as source for clone. Either -s/--source-snapshot-name or -v/--source-pvc-name must be specified.
    -v, --source-pvc-name=          Name of Kubernetes PersistentVolumeClaim (PVC) to use as source for clone. Either -s/--source-snapshot-name or -v/--source-pvc-name must be specified.
```

##### Example Usage

Near-instantaneously create a new persistent volume that is an exact copy of the current contents of the persistent volume attached to Kubernetes PersistentVolumeClaim (PVC) 'test2' in namespace 'default', and attach the new persistent volume to a PVC named 'test2-clone1' in namespace 'default'.

```sh
netapp_dataops_k8s_cli.py clone volume --new-pvc-name=test2-clone1 --source-pvc-name=test2
Creating new PersistentVolumeClaim (PVC) 'test2-clone1' from source PVC 'test2' in namespace 'default'...
Creating PersistentVolumeClaim (PVC) 'test2-clone1' in namespace 'default'.
PersistentVolumeClaim (PVC) 'test2-clone1' created. Waiting for Kubernetes to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'test2-clone1' in namespace 'default'.
Volume successfully cloned.
```

Near-instantaneously create a new persistent volume that is an exact copy of the contents of VolumeSnapshot 'ntap-dsutil.20210304170930' in namespace 'dst-test', and attach the new persistent volume to a PVC named 'test1-clone1' in namespace 'dst-test'.

```sh
netapp_dataops_k8s_cli.py clone volume --new-pvc-name=test1-clone1 --source-snapshot-name=ntap-dsutil.20210304170930 --namespace=dst-test
Creating new PersistentVolumeClaim (PVC) 'test1-clone1' from VolumeSnapshot 'ntap-dsutil.20210304170930' in namespace 'dst-test'...
Creating PersistentVolumeClaim (PVC) 'test1-clone1' in namespace 'dst-test'.
PersistentVolumeClaim (PVC) 'test1-clone1' created. Waiting for Kubernetes to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'test1-clone1' in namespace 'dst-test'.
Volume successfully cloned.
```

<a name="cli-create-volume"></a>

#### Create a New Persistent Volume

The NetApp DataOps Toolkit can be used to rapidly provision a new persistent volume within a Kubernetes cluster. The command for provisioning a new persistent volume is `netapp_dataops_k8s_cli.py create volume`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/) for more information on StorageClasses.

The following options/arguments are required:

```
    -p, --pvc-name=         Name of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC).
    -s, --size=             Size of new volume. Format: '1024Mi', '100Gi', '10Ti', etc.
```

The following options/arguments are optional:

```
    -c, --storage-class=    Kubernetes StorageClass to use when provisioning new volume. If not specified, default StorageClass will be used. Note: StorageClass must be configured to use Trident.
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace to create new PersistentVolumeClaim (PVC) in. If not specified, PVC will be created in namespace "default".
```

##### Example Usage

Provision a new persistent volume of size 1GB and attach it to a Kubernetes PersistentVolumeClaim (PVC) named 'project1' in namespace 'default'.

```sh
netapp_dataops_k8s_cli.py create volume --pvc-name=project1 --size=1Gi
Creating PersistentVolumeClaim (PVC) 'project1' in namespace 'default'.
PersistentVolumeClaim (PVC) 'project1' created. Waiting for Kubernetes to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'project1' in namespace 'default'.
```

Provision a new persistent volume of size 2TB, using the Kubernetes StorageClass 'ontap-flexgroup', and attach the volume to a Kubernetes PersistentVolumeClaim (PVC) named 'test1' in namespace 'dst-test'

```sh
netapp_dataops_k8s_cli.py create volume --pvc-name=test1 --size=2Ti --storage-class=ontap-flexgroup --namespace=dst-test
Creating volume 'test1' in namespace 'dst-test'.
PersistentVolumeClaim (PVC) 'test1' created. Waiting for Kubernetes to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'test1' in namespace 'dst-test'.
```

<a name="cli-delete-volume"></a>

#### Delete an Existing Persistent Volume

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing persistent volume within a Kubernetes cluster. The command for deleting an existing persistent volume is `netapp_dataops_k8s_cli.py delete volume`.

The following options/arguments are required:

```
    -p, --pvc-name=                 Name of Kubernetes PersistentVolumeClaim (PVC) to be deleted.
```

The following options/arguments are optional:

```
    -f, --force                     Do not prompt user to confirm operation.
    -h, --help                      Print help text.
    -n, --namespace=                Kubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    -s, --preserve-snapshots        Do not delete VolumeSnapshots associated with PersistentVolumeClaim (PVC).
```

##### Example Usage

Delete PersistentVolumeClaim (PVC) 'test1' in namespace 'dst-test'.

```sh
netapp_dataops_k8s_cli.py delete volume --pvc-name=test1 --namespace=dst-test
Warning: All data and snapshots associated with the volume will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting PersistentVolumeClaim (PVC) 'test1' in namespace 'dst-test' and associated volume.
PersistentVolumeClaim (PVC) successfully deleted.
```

<a name="cli-list-volumes"></a>

#### List All Persistent Volumes

The NetApp DataOps Toolkit can be used to print a list of all existing persistent volumes in a specific namespace within a Kubernetes cluster. The command for printing a list of all existing persistent volumes is `netapp_dataops_k8s_cli.py list volumes`.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace for which to retrieve list of volumes. If not specified, namespace "default" will be used.
```

##### Example Usage

```sh
netapp_dataops_k8s_cli.py list volumes --namespace=dst-test
PersistentVolumeClaim (PVC) Name    Status    Size    StorageClass     Clone    Source PVC    Source VolumeSnapshot
----------------------------------  --------  ------  ---------------  -------  ------------  -----------------------
test                                Bound     10Gi    ontap-flexvol    No
test-beegfs                         bound     10Gi    beegfs-scratch   No
test-clone1                         Bound     10Gi    ontap-flexvol    Yes      test          snap1
test-clone2                         Bound     10Gi    ontap-flexvol    Yes      test          snap2
test2                               Bound     10Gi    ontap-flexvol    No
test2-clone1                        Bound     10Gi    ontap-flexvol    Yes      test2         n/a
```

<a name="cli-create-volume-snapshot"></a>

#### Create a New Snapshot for a Persistent Volume

The NetApp DataOps Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing persistent volume. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version datasets and/or implement dataset-to-model traceability. The command for creating a new snapshot for a specific persistent volume is `netapp_dataops_k8s_cli.py create volume-snapshot`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

The following options/arguments are required:

```
    -p, --pvc-name=                 Name of Kubernetes PersistentVolumeClaim (PVC) to create snapshot for.
```

The following options/arguments are optional:

```
    -c, --volume-snapshot-class=    Kubernetes VolumeSnapshotClass to use when creating snapshot. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    -h, --help                      Print help text.
    -n, --namespace=                Kubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    -s, --snapshot-name=            Name of new Kubernetes VolumeSnapshot. If not specified, will be set to 'ntap-dsutil.<timestamp>'.
```

##### Example Usage

Create a VolumeSnapshot for the volume attached to the PersistentVolumeClaim (PVC) named 'project1' in namespace 'default'.

```sh
netapp_dataops_k8s_cli.py create volume-snapshot --pvc-name=project1
Creating VolumeSnapshot 'ntap-dsutil.20210218184654' for PersistentVolumeClaim (PVC) 'project1' in namespace 'default'.
VolumeSnapshot 'ntap-dsutil.20210218184654' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

Create a VolumeSnapshot named 'snap1, for the volume attached to the PersistentVolumeClaim (PVC) named 'test1', in namespace 'dst-test'.

```sh
netapp_dataops_k8s_cli.py create volume-snapshot --pvc-name=test1 --snapshot-name=snap1 --namespace=dst-test
Creating VolumeSnapshot 'snap1' for PersistentVolumeClaim (PVC) 'test1' in namespace 'dst-test'.
VolumeSnapshot 'snap1' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

<a name="cli-delete-volume-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing persistent volume snapshot. The command for deleting an existing snapshot is `netapp_dataops_k8s_cli.py delete volume-snapshot`.

The following options/arguments are required:

```
    -s, --snapshot-name=    Name of Kubernetes VolumeSnapshot to be deleted.
```

The following options/arguments are optional:

```
    -f, --force             Do not prompt user to confirm operation.
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
```

##### Example Usage

Delete VolumeSnapshot 'ntap-dsutil.20210304151544' in namespace 'dst-test'.

```sh
netapp_dataops_k8s_cli.py delete volume-snapshot --snapshot-name=ntap-dsutil.20210304151544 --namespace=dst-test
Warning: This snapshot will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting VolumeSnapshot 'ntap-dsutil.20210304151544' in namespace 'dst-test'.
VolumeSnapshot successfully deleted.
```

<a name="cli-list-volume-snapshots"></a>

#### List All Snapshots

The NetApp DataOps Toolkit can be used to list all existing persistent volume snapshots in a specific namespace. The command for listing all existing snapshots is `netapp_dataops_k8s_cli.py list volume-snapshots`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    -p, --pvc-name=         Name of Kubernetes PersistentVolumeClaim (PVC) to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.
```

##### Example Usage

List all VolumeSnapshots in namespace 'default'.

```sh
netapp_dataops_k8s_cli.py list volume-snapshots
VolumeSnapshot Name         Ready to Use    Creation Time         Source PersistentVolumeClaim (PVC)    Source JupyterLab workspace    VolumeSnapshotClass
--------------------------  --------------  --------------------  ------------------------------------  -----------------------------  ---------------------
ntap-dsutil.20210309141230  True            2021-03-11T16:24:03Z  ntap-dsutil-jupyterlab-mike           mike                           csi-snapclass
snap1                       True            2021-03-11T16:29:40Z  test                                                                 csi-snapclass
snap2                       True            2021-03-11T16:29:49Z  test                                                                 csi-snapclass
```

<a name="cli-restore-volume-snapshot"></a>

#### Restore a Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously restore a specific snapshot for a persistent volume. This action will restore the corresponding volume to its exact state at the time that the snapshot was created. The command for restoring an existing snapshot is `netapp_dataops_k8s_cli.py restore volume-snapshot`.

Warning: In order to restore a snapshot, the PersistentVolumeClaim (PVC) associated the snapshot must NOT be mounted to any pods.
Tip: If the PVC associated with the snapshot is currently mounted to a pod that is managed by a deployment, you can scale the deployment to 0 pods using the command `kubectl scale --replicas=0 deployment/<deployment_name>`. After scaling the deployment to 0 pods, you will be able to restore the snapshot. After restoring the snapshot, you can use the `kubectl scale` command to scale the deployment back to the desired number of pods.

The following options/arguments are required:

```
    -s, --snapshot-name=    Name of Kubernetes VolumeSnapshot to be restored.
```

The following options/arguments are optional:

```
    -f, --force             Do not prompt user to confirm operation.
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
```

##### Example Usage

Restore VolumeSnapshot 'snap1' (for PersistentVolumeClaim 'project1') in namespace 'default'.

```sh
netapp_dataops_k8s_cli.py restore volume-snapshot --snapshot-name=snap1
Warning: In order to restore a snapshot, the PersistentVolumeClaim (PVC) associated the snapshot must NOT be mounted to any pods.
Are you sure that you want to proceed? (yes/no): yes
Restoring VolumeSnapshot 'snap1' for PersistentVolumeClaim 'project1' in namespace 'default'.
VolumeSnapshot successfully restored.
```

<a name="cli-create-flexcache"></a>

#### Create a FlexCache Volume

The NetApp DataOps Toolkit can be used to create a FlexCache volume in ONTAP and then create a PV and PVC representing the FlexCache in Kubernetes. The command to create a FlexCache volume is `netapp_dataops_k8s_cli.py create flexcache`.

The following options/arguments are required:

```
    -f, --flexcache-vol=    Name of the FlexCache volume to be created. This is the name that will be applied to the new Kubernetes PersistentVolumeClaim (PVC).
    -s, --source-svm=       Name of the source Storage Virtual Machine (SVM) that contains the origin volume to be cached.
    -v, --source-vol=       Name of the source volume in the source SVM that will be cached by the FlexCache volume.
    -z, --flexcache-size=   Size of the FlexCache volume to be created. The size must be specified in a format such as '1024Mi', '100Gi', '10Ti', etc. Note: The size must be at least 50Gi.
    -b, --backend-name=     Name of the tridentbackendconfig.

```

The following options/arguments are optional:

```
    -c, --junction          The junction path for the FlexCache volume.
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace to create the new PersistentVolumeClaim (PVC) in. If not specified, the PVC will be created in the "default" namespace.
```

##### Example Usage

Create a FlexCache volume 'test-cache-vol1' of size '53Gi', and attach it to a Kubernetes PersistentVolumeClaim (PVC) named 'test-vol1' in namespace 'trident', using 'ontap' tridentbackendconfig.

```sh
netapp_dataops_k8s_cli.py create flexcache --flexcache-vol=test-cache-vol1 --source-vol=test-vol1 --source-svm=svm0 --flexcache-size=53Gi --backend-name=ontap --namespace=trident
Creating FlexCache: svm0:test-vol1 -> svm0:test-cache-vol1
FlexCache created successfully.
[K8s] Creating PV 'pv-test-cache-vol1' in namespace 'trident'...
[K8s] PV 'pv-test-cache-vol1' created successfully.
[K8s] Creating PVC 'test-cache-vol1' in namespace 'trident'...
[K8s] PVC 'test-cache-vol1' created successfully.
Waiting for Kubernetes to bind volume to PVC.
[K8s] PVC 'test-cache-vol1' is bound to PV 'pv-test-cache-vol1'.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'test-cache-vol1' in namespace 'trident'.
```

<a name="library-of-functions"></a>

## Advanced: Set of Functions

The NetApp DataOps Toolkit for Kubernetes provides a set of functions that can be imported into any Python program or Jupyter Notebook. In this manner, data scientists and data engineers can easily incorporate Kubernetes-native data management tasks into their existing projects, programs, and workflows. This functionality is only recommended for advanced users who are proficient in Python.

```py
from netapp_dataops.k8s import clone_volume, create_volume, delete_volume, list_volumes, create_volume_snapshot, delete_volume_snapshot, list_volume_snapshots, restore_volume_snapshot, create_flexcache
```

The following volume management operations are available within the set of functions.

| Kubernetes persistent volume management operations                                   | Supported by BeeGFS | Supported by Trident |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- |
| [Clone a persistent volume.](#lib-clone-volume)                                      | No                  | Yes                  |
| [Create a new persistent volume.](#lib-create-volume)                                | Yes                 | Yes                  |
| [Delete an existing persistent volume.](#lib-delete-volume)                          | Yes                 | Yes                  |
| [List all persistent volumes.](#lib-list-volumes)                                    | Yes                 | Yes                  |
| [Create a new snapshot for a persistent volume.](#lib-create-volume-snapshot)        | No                  | Yes                  |
| [Delete an existing snapshot.](#lib-delete-volume-snapshot)                          | No                  | Yes                  |
| [List all snapshots.](#lib-list-volume-snapshots)                                    | No                  | Yes                  |
| [Restore a snapshot.](#lib-restore-volume-snapshot)                                  | No                  | Yes                  |
| [Create a new FlexCache volume.](#lib-restore-volume-snapshot)                       | No                  | Yes                  |

### Kubernetes Persistent Volume Management Operations

<a name="lib-clone-volume"></a>

#### Clone a Persistent Volume

The NetApp DataOps Toolkit can be used to near-instantaneously provision a new persistent volume (within a Kubernetes cluster) that is an exact copy of an existing persistent volume or snapshot, as part of any Python program or workflow. In other words, the NetApp DataOps Toolkit can be used to near-instantaneously clone a persistent volume as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

##### Function Definition

```py
def clone_volume(
    new_pvc_name: str,                                # Name of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC) (required).
    source_pvc_name: str,                             # Name of Kubernetes PersistentVolumeClaim (PVC) to use as source for clone (required).
    source_snapshot_name: str = None,                 # Name of Kubernetes VolumeSnapshot to use as source for clone.
    volume_snapshot_class: str = "csi-snapclass",     # Kubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                       # Kubernetes namespace that source PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    print_output: bool = False                        # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-create-volume"></a>

#### Create a New Persistent Volume

The NetApp DataOps Toolkit can be used to rapidly provision a new persistent volume within a Kubernetes cluster as part of any Python program or workflow.

Tip: Refer to the [Trident](https://netapp-trident.readthedocs.io/) or [BeeGFS CSI driver](https://github.com/NetApp/beegfs-csi-driver/blob/master/docs/usage.md#dynamic-provisioning-workflow) documentation for more information on StorageClasses.

##### Function Definition

```py
def create_volume(
    pvc_name: str,               # Name of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC) (required).
    volume_size: str,            # Size of new volume. Format: '1024Mi', '100Gi', '10Ti', etc (required).
    storage_class: str = None,   # Kubernetes StorageClass to use when provisioning new volume. If not specified, the default StorageClass will be used. Note: The StorageClass must be configured to use Trident or the BeeGFS CSI driver.
    namespace: str = "default",  # Kubernetes namespace to create new PersistentVolumeClaim (PVC) in. If not specified, PVC will be created in namespace "default".
    print_output: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-delete-volume"></a>

#### Delete an Existing Persistent Volume

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing persistent volume within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def delete_volume(
    pvc_name: str,                      # Name of Kubernetes PersistentVolumeClaim (PVC) to be deleted (required).
    namespace: str = "default",         # Kubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    preserve_snapshots: bool = False,   # Denotes whether or not to preserve VolumeSnapshots associated with PersistentVolumeClaim (PVC)  (if set to False, all VolumeSnapshots associated with PVC will be deleted).
    print_output: bool = False          # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-list-volumes"></a>

#### List All Data Volumes

The NetApp DataOps Toolkit can be used to retrieve a list of all existing persistent volumes in a specific namespace within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def list_volumes(
    namespace: str = "default",     # Kubernetes namespace for which to retrieve list of volumes. If not specified, namespace "default" will be used.
    print_output: bool = False      # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing volumes. Each item in the list will be a dictionary containing details regarding a specific volume. The keys for the values in this dictionary are "PersistentVolumeClaim (PVC) Name", "Status", "Size", "StorageClass", "Clone" (Yes/No), "Source PVC", "Source VolumeSnapshot".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-create-volume-snapshot"></a>

#### Create a New Snapshot for a Persistent Volume

The NetApp DataOps Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing persistent volume as part of any Python program or workflow. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version datasets and/or implement dataset-to-model traceability.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def create_volume_snapshot(
    pvc_name: str,                                  # Name of Kubernetes PersistentVolumeClaim (PVC) to create snapshot for (required).
    snapshot_name: str = None,                      # Name of new Kubernetes VolumeSnapshot. If not specified, will be set to 'ntap-dsutil.<timestamp>'.
    volume_snapshot_class: str = "csi-snapclass",   # Kubernetes VolumeSnapshotClass to use when creating snapshot. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                     # Kubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    print_output: bool = False                      # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-delete-volume-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing snapshot as part of any Python program or workflow.

##### Function Definition

```py
def delete_volume_snapshot(
    snapshot_name: str,             # Name of Kubernetes VolumeSnapshot to be deleted (required).
    namespace: str = "default",     # Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    print_output: bool = False      # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-list-volume-snapshots"></a>

#### List all Snapshots

The NetApp DataOps Toolkit can be used to list all existing persistent volume snapshots in a specific namespace as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def list_volume_snapshots(
    pvc_name: str = None,           # Name of Kubernetes PersistentVolumeClaim (PVC) to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.
    namespace: str = "default",     # Kubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    print_output: bool = False      # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing snapshots. Each item in the list will be a dictionary containing details regarding a specific snapshot. The keys for the values in this dictionary are "VolumeSnapshot Name", "Ready to Use" (True/False), "Creation Time", "Source PersistentVolumeClaim (PVC)", "Source JupyterLab workspace", "VolumeSnapshotClass".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-restore-volume-snapshot"></a>

#### Restore a Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously restore a specific snapshot for a persistent volume as part of any Python program or workflow. This action will restore the corresponding volume to its exact state at the time that the snapshot was created.

Warning: In order to restore a snapshot, the PersistentVolumeClaim (PVC) associated the snapshot must NOT be mounted to any pods.
Tip: If the PVC associated with the snapshot is currently mounted to a pod that is managed by a deployment, you can scale the deployment to 0 pods using the command `kubectl scale --replicas=0 deployment/<deployment_name>`. After scaling the deployment to 0 pods, you will be able to restore the snapshot. After restoring the snapshot, you can use the `kubectl scale` command to scale the deployment back to the desired number of pods.

##### Function Definition

```py
def restore_volume_snapshot(
    snapshot_name: str,             # Name of Kubernetes VolumeSnapshot to be restored (required).
    namespace: str = "default",     # Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    print_output: bool = False      # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-clone-volume"></a>

#### Create a FlexCache Volume

The NetApp DataOps Toolkit can be used to create a FlexCache volume in ONTAP and then create a PV and PVC representing the FlexCache in Kubernetes.

##### Function Definition

```py
def create_flexcache(
    source_vol: str,                # Name of the source volume in the source SVM that will be cached by the FlexCache volume (required).
    source_svm: str,                # Name of the source Storage Virtual Machine (SVM) that contains the origin volume to be cached (required).
    flexcache_vol: str,             # Name of the FlexCache volume to be created (required).
    flexcache_size: str,            # Size of the FlexCache volume to be created. Format: '1024Mi', '100Gi', '10Ti', etc. Note: The size must be at least 50Gi (required).
    backend_name: str,              # Name of the tridentbackendconfig (required).
    junction: str = None,           # The junction path for the FlexCache volume (optional).
    namespace: str = "default",     # Kubernetes namespace to create the new PersistentVolumeClaim (PVC) in. If not specified, the PVC will be created in the "default" namespace (optional).
    print_output: bool = False      # Denotes whether or not to print messages to the console during execution (optional).
) :

```

##### Return Value

The function returns a dictionary containing details about the created FlexCache volume and the associated Kubernetes PersistentVolumeClaim (PVC). The keys for the values in this dictionary are:

- "ontap_flexcache": The FlexCache volume in ONTAP in the format "{svm}: {flexcache_vol}".
- "k8s_pvc": The name of the Kubernetes PersistentVolumeClaim (PVC) created.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
InvalidVolumeParameterError     # Invalid parameters specified for the FlexCache volume.
ConnectionTypeError             # Invalid connection type specified.
NetAppRestError                 # Error with the NetApp REST API.
```