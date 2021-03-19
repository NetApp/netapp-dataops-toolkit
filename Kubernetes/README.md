NetApp Data Science Toolkit for Kubernetes
=========

The NetApp Data Science Toolkit for Kubernetes is a Python library that makes it simple for data scientists and data engineers to perform various data management tasks within a Kubernetes cluster, such as provisioning a new Kubernetes persistent volume or JupyterLab workspace, near-instantaneously cloning a Kubernetes persistent volume or JupterLab workspace, and near-instantaneously snapshotting a Kubernetes persistent volume or JupyterLab workspace for traceability/baselining. This Python library can function as either a [command line utility](#command-line-functionality) or a [library of functions](#library-of-functions) that can be imported into any Python program or Jupyter Notebook.

## Compatibility

The NetApp Data Science Toolkit for Kubernetes supports Linux and macOS hosts.

The toolkit must be used in conjunction with a Kubernetes cluster in order to be useful. Additionally, [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/), NetApp's dynamic storage orchestrator for Kubernetes, must be installed within the Kubernetes cluster. The toolkit simplifies the performing of various data management tasks that are actually executed by Trident. In order to facilitate this, the toolkit communicates with Trident via API. 

The toolkit is currently compatible with Kubernetes versions 1.17* and above.

\* The toolkit has been fully validated with Kubernetes versions 1.17 and 1.18.

The toolkit is currently compatible with Trident versions 20.07 and above. Additionaly, the toolkit is compatible with the following Trident backend types:

- ontap-nas
- aws-cvs
- gcp-cvs
- azure-netapp-files

<a name="getting-started"></a>

## Getting Started: Standard Usage

The NetApp Data Science Toolkit for Kubernetes can be utilized from any Linux or macOS host that has network access to the Kubernetes cluster.

The toolkit requires that Python 3.6 or above be installed on the local host.

The following Python libraries that are not generally bundled with a standard Python installation are required in order for the toolkit to function correctly - ipython, kubernetes, pandas, tabulate. These libraries can be installed with a Python package manager like pip.

```sh
python3 -m pip install ipython kubernetes pandas tabulate
```

Additionally, the toolkit requires that a valid kubeconfig file be present on the local host, located at `$HOME/.kube/config` or at another path specified by the `KUBECONFIG` environment variable. Refer to the [Kubernetes documentation](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) for more information regarding kubeconfig files.

## Getting Started: In-cluster Usage (for advanced Kubernetes users)

The NetApp Data Science Toolkit for Kubernetes can also be utilized from within a pod that is running in the Kubernetes cluster. If the toolkit is being utilized within a pod in the Kubernetes cluster, then the pod's ServiceAccount must have the following permissions:

```yaml
- apiGroups: [""]
  resources: ["persistentvolumeclaims", "persistentvolumeclaims/status", "services"]
  verbs: ["get", "list", "create", "delete"]
- apiGroups: ["snapshot.storage.k8s.io"]
  resources: ["volumesnapshots", "volumesnapshots/status", "volumesnapshotcontents", "volumesnapshotcontents/status"]
  verbs: ["get", "list", "create", "delete"]
- apiGroups: ["apps", "extensions"]
  resources: ["deployments", "deployments/scale", "deployments/status"]
  verbs: ["get", "list", "create", "delete", "patch", "update"]
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list"]
```

In the [Examples](Examples/) directory, you will find the following examples pertaining to utilizing the toolkit within a pod in the Kubernetes cluster:
- [service-account-ntap-dsutil.yaml](Examples/service-account-ntap-dsutil.yaml): Manifest for a ServiceAccount named 'ntap-dsutil' that has all of the required permissions for executing toolkit operations.
- [pod-ntap-dsutil.yaml](Examples/pod-ntap-dsutil.yaml): Manifest for a Pod named 'ntap-dsutil' in which toolkit operations can be executed.

Refer to the [Kubernetes documentation](https://kubernetes.io/docs/tasks/run-application/access-api-from-pod/) for more information on accessing the Kubernetes API from within a pod.

<a name="command-line-functionality"></a>

## Command Line Functionality

The simplest way to use the NetApp Data Science Toolkit for Kubernetes is as a command line utility. When functioning as a command line utility, the toolkit supports the following operations.

JupyterLab workspace management operations:
- [Clone a JupyterLab workspace.](#cli-clone-jupyterlab)
- [Create a new JupyterLab workspace.](#cli-create-jupyterlab)
- [Delete an existing JupyterLab workspace.](#cli-delete-jupyterlab)
- [List all JupyterLab workspaces.](#cli-list-jupyterlabs)
- [Create a new snapshot for a JupyterLab workspace.](#cli-create-jupyterlab-snapshot)
- [Delete an existing snapshot.](#cli-delete-jupyterlab-snapshot)
- [List all snapshots.](#cli-list-jupyterlab-snapshots)
- [Restore a snapshot.](#cli-restore-jupyterlab-snapshot)

Kubernetes persistent volume management operations (for advanced Kubernetes users):
- [Clone a persistent volume.](#cli-clone-volume)
- [Create a new persistent volume.](#cli-create-volume)
- [Delete an existing persistent volume.](#cli-delete-volume)
- [List all persistent volumes.](#cli-list-volumes)
- [Create a new snapshot for a persistent volume.](#cli-create-volume-snapshot)
- [Delete an existing snapshot.](#cli-delete-volume-snapshot)
- [List all snapshots.](#cli-list-volume-snapshots)
- [Restore a snapshot.](#cli-restore-volume-snapshot)

### JupyterLab Workspace Management Operations

<a name="cli-clone-jupyterlab"></a>

#### Clone a JupyterLab Workspace

The NetApp Data Science Toolkit can be used to near-instantaneously provision a new JupyterLab workspace (within a Kubernetes cluster) that is an exact copy of an existing JupyterLab workspace or JupyterLab workspace snapshot. In other words, the NetApp Data Science Toolkit can be used to near-instantaneously clone a JupyterLab workspace. The command for cloning a JupyterLab workspace is `./ntap_dsutil_k8s.py clone jupyterlab`.

Note: Either -s/--source-snapshot-name or -j/--source-workspace-name must be specified. However, only one of these flags (not both) should be specified for a given operation. If -j/--source-workspace-name is specified, then the clone will be created from the current state of the workspace. If -s/--source-snapshot-name is specified, then the clone will be created from a specific snapshot related the source workspace.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

The following options/arguments are required:

```
    -w, --new-workspace-name=       Name of new workspace (name to be applied to new JupyterLab workspace).
```

The following options/arguments are optional:

```
    -c, --volume-snapshot-class=    Kubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    -g, --nvidia-gpu=               Number of NVIDIA GPUs to allocate to new JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    -h, --help                      Print help text.
    -j, --source-workspace-name=    Name of JupyterLab workspace to use as source for clone. Either -s/--source-snapshot-name or -j/--source-workspace-name must be specified.
    -m, --memory=                   Amount of memory to reserve for new JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    -n, --namespace=                Kubernetes namespace that source workspace is located in. If not specified, namespace "default" will be used.
    -p, --cpu=                      Number of CPUs to reserve for new JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    -s, --source-snapshot-name=     Name of Kubernetes VolumeSnapshot to use as source for clone. Either -s/--source-snapshot-name or -j/--source-workspace-name must be specified.
```

##### Example Usage

Near-instantaneously create a new JupyterLab workspace, named 'project1-experiment3', that is an exact copy of the current contents of existing JupyterLab workspace 'project1' in namespace 'default'. Allocate 2 NVIDIA GPUs to the new workspace.

```sh
./ntap_dsutil_k8s.py clone jupyterlab --new-workspace-name=project1-experiment3 --source-workspace-name=project1 --nvidia-gpu=2
Creating new JupyterLab workspace 'project1-experiment3' from source workspace 'project1' in namespace 'default'...

Creating new VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' for source PVC 'ntap-dsutil-jupyterlab-project1' in namespace 'default' to use as source for clone...
Creating VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' for PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1' in namespace 'default'.
VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
Creating new PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment3' from VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' in namespace 'default'...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment3' in namespace 'default'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment3' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment3' in namespace 'default'.
Volume successfully cloned.

Set workspace password (this password will be required in order to access the workspace): 
Re-enter password: 

Creating Service 'ntap-dsutil-jupyterlab-project1-experiment3' in namespace 'default'.
Service successfully created.

Creating Deployment 'ntap-dsutil-jupyterlab-project1-experiment3' in namespace 'default'.
Deployment 'ntap-dsutil-jupyterlab-project1-experiment3' created.
Waiting for Deployment 'ntap-dsutil-jupyterlab-project1-experiment3' to reach Ready state.
Deployment successfully created.

Workspace successfully created.
To access workspace, navigate to http://10.61.188.112:30993
JupyterLab workspace successfully cloned.
```

Near-instantaneously create a new JupyterLab workspace, named 'project1-experiment2', that is an exact copy of the contents of JupyterLab workspace VolumeSnapshot 'project1-snap1' in namespace 'defauult'.

```sh
./ntap_dsutil_k8s.py clone jupyterlab -s project1-snap1 -w project1-experiment2
Creating new JupyterLab workspace 'project1-experiment2' from VolumeSnapshot 'project1-snap1' in namespace 'default'...

Creating new PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment2' from VolumeSnapshot 'project1-snap1' in namespace 'default'...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment2' in namespace 'default'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment2' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment2' in namespace 'default'.
Volume successfully cloned.

Set workspace password (this password will be required in order to access the workspace): 
Re-enter password: 

Creating Service 'ntap-dsutil-jupyterlab-project1-experiment2' in namespace 'default'.
Service successfully created.

Creating Deployment 'ntap-dsutil-jupyterlab-project1-experiment2' in namespace 'default'.
Deployment 'ntap-dsutil-jupyterlab-project1-experiment2' created.
Waiting for Deployment 'ntap-dsutil-jupyterlab-project1-experiment2' to reach Ready state.
Deployment successfully created.

Workspace successfully created.
To access workspace, navigate to http://10.61.188.112:30677
JupyterLab workspace successfully cloned.
```

<a name="cli-create-jupyterlab"></a>

#### Create a New JupyterLab Workspace

The NetApp Data Science Toolkit can be used to rapidly provision a new JupyterLab workspace within a Kubernetes cluster. Workspaces provisioned using the NetApp Data Science Toolkit will be backed by NetApp persistent storage and, thus, will persist across any shutdowns or outages in the Kubernetes environment. The command for creating a new JupyterLab workspace is `./ntap_dsutil_k8s.py create jupyterlab`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/) for more information on StorageClasses.

The following options/arguments are required:

```
    -w, --workspace-name=   Name of new JupyterLab workspace.
    -s, --size=             Size new workspace (i.e. size of backing persistent volume to be created). Format: '1024Mi', '100Gi', '10Ti', etc.
```

The following options/arguments are optional:

```
    -c, --storage-class=    Kubernetes StorageClass to use when provisioning backing volume for new workspace. If not specified, default StorageClass will be used. Note: StorageClass must be configured to use Trident.
    -g, --nvidia-gpu=       Number of NVIDIA GPUs to allocate to JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    -h, --help              Print help text.
    -i, --image=            Container image to use when creating workspace. If not specified, "jupyter/tensorflow-notebook" will be used.
    -m, --memory=           Amount of memory to reserve for JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    -n, --namespace=        Kubernetes namespace to create new workspace in. If not specified, workspace will be created in namespace "default".
    -p, --cpu=              Number of CPUs to reserve for JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
```

##### Example Usage

Provision a new JupyterLab workspace named 'mike' of size 10GB in namespace 'default'. Allocate 1 NVIDIA GPU to the new workspace.

```sh
./ntap_dsutil_k8s.py create jupyterlab --workspace-name=mike --size=10Gi --nvidia-gpu=1
Set workspace password (this password will be required in order to access the workspace): 
Re-enter password: 

Creating persistent volume for workspace...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.

Creating Service 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
Service successfully created.

Creating Deployment 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
Deployment 'ntap-dsutil-jupyterlab-mike' created. Waiting for Deployment to reach Ready state.
Deployment successfully created.

Workspace successfully created.
To access workspace, navigate to http://10.61.188.112:31082
```

Provision a new JupyterLab workspace named 'dave', of size 2TB, in the namespace 'dst-test', using the container image 'jupyter/scipy-notebook:latest', and use Kubernetes StorageClass 'ontap-flexgroup' when provisioning the backing volume for the workspace.

```sh
./ntap_dsutil_k8s.py create jupyterlab --namespace=dst-test --workspace-name=dave --image=jupyter/scipy-notebook:latest --size=2Ti --storage-class=ontap-flexgroup
Set workspace password (this password will be required in order to access the workspace): 
Re-enter password: 

Creating persistent volume for workspace...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-dave' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.

Creating Service 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.
Service successfully created.

Creating Deployment 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.
Deployment 'ntap-dsutil-jupyterlab-dave' created. Waiting for Deployment to reach Ready state.
Deployment successfully created.

Workspace successfully created.
To access workspace, navigate to http://10.61.188.112:32275
```

<a name="cli-delete-jupyterlab"></a>

#### Delete an Existing JupyterLab Workspace

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace within a Kubernetes cluster. The command for deleting an existing JupyterLab workspace is `./ntap_dsutil_k8s.py delete jupyterlab`.

The following options/arguments are required:

```
    -w, --workspace-name=           Name of JupyterLab workspace to be deleted.
```

The following options/arguments are optional:

```
    -f, --force                     Do not prompt user to confirm operation.
    -h, --help                      Print help text.
    -n, --namespace=                Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
    -s, --preserve-snapshots        Do not delete VolumeSnapshots associated with workspace.
```

##### Example Usage

Delete the workspace 'mike' in namespace 'dst-test'.

```sh
./ntap_dsutil_k8s.py delete jupyterlab --workspace-name=mike --namespace=dst-test
Warning: All data and snapshots associated with the workspace will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting workspace 'mike' in namespace 'dst-test'.
Deleting Deployment...
Deleting Service...
Deleting PVC...
Workspace successfully deleted.
```

<a name="cli-list-jupyterlabs"></a>

#### List All JupyterLab Workspaces

The NetApp Data Science Toolkit can be used to print a list of all existing JupyterLab workspaces in a specific namespace within a Kubernetes cluster. The command for printing a list of all existing JupyterLab workspaces is `./ntap_dsutil_k8s.py list jupyterlabs`.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace for which to retrieve list of workspaces. If not specified, namespace "default" will be used.
```

##### Example Usage

```sh
./ntap_dsutil_k8s.py list jupyterlabs --namespace=dst-test
Workspace Name        Status    Size    StorageClass    Access URL                  Clone    Source Workspace    Source VolumeSnapshot
--------------------  --------  ------  --------------  --------------------------  -------  ------------------  ------------------------------------
aj                    Ready     1Ti     ontap-flexvol   http://10.61.188.112:30590  No
dave                  Ready     2Ti     ontap-flexvol   http://10.61.188.112:30792  No
mike                  Ready     1Ti     ontap-flexvol   http://10.61.188.112:31047  No
mike-clone1           Ready     1Ti     ontap-flexvol   http://10.61.188.112:30430  Yes      mike                ntap-dsutil.20210318204637
project1              Ready     10Gi    ontap-flexvol   http://10.61.188.112:31555  No
project1-experiment1  Ready     10Gi    ontap-flexvol   http://10.61.188.112:32363  Yes      project1            ntap-dsutil.for-clone.20210315184514
project1-experiment2  Ready     10Gi    ontap-flexvol   http://10.61.188.112:30677  Yes      project1            project1-snap1
project1-experiment3  Ready     10Gi    ontap-flexvol   http://10.61.188.112:30993  Yes      project1            ntap-dsutil.for-clone.20210315185504
rick                  Ready     2Ti     ontap-flexvol   http://10.61.188.112:31939  No
sathish               Ready     2Ti     ontap-flexvol   http://10.61.188.112:31820  No
```

<a name="cli-create-jupyterlab-snapshot"></a>

#### Create a New Snapshot for a JupyterLab Workspace

The NetApp Data Science Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing JupyterLab workspace. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version workspaces and/or implement workspace-to-model traceability. The command for creating a new snapshot for a specific JupyterLab workspace is `./ntap_dsutil_k8s.py create jupyterlab-snapshot`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

The following options/arguments are required:

```
    -w, --workspace-name=           Name of JupyterLab workspace.
```

The following options/arguments are optional:

```
    -c, --volume-snapshot-class=    Kubernetes VolumeSnapshotClass to use when creating snapshot of backing volume for workspace. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    -h, --help                      Print help text.
    -n, --namespace=                Kubernetes namespace that workspace is located in. If not specified, namespace "default" will be used.
    -s, --snapshot-name=            Name of new Kubernetes VolumeSnapshot for workspace. If not specified, will be set to 'ntap-dsutil.<timestamp>'.
```

##### Example Usage

Create a VolumeSnapshot for the workspace named 'mike' in namespace 'default'.

```sh
./ntap_dsutil_k8s.py create jupyterlab-snapshot --workspace-name=mike
Creating VolumeSnapshot for JupyterLab workspace 'mike' in namespace 'default'...
Creating VolumeSnapshot 'ntap-dsutil.20210309141230' for PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
VolumeSnapshot 'ntap-dsutil.20210309141230' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

Create a VolumeSnapshot named 'snap1', for the workspace named 'rick', in namespace 'dst-test'.

```sh
./ntap_dsutil_k8s.py create jupyterlab-snapshot --workspace-name=rick --namespace=dst-test --snapshot-name=snap1
Creating VolumeSnapshot for JupyterLab workspace 'rick' in namespace 'dst-test'...
Creating VolumeSnapshot 'snap1' for PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-rick' in namespace 'dst-test'.
VolumeSnapshot 'snap1' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

<a name="cli-delete-jupyterlab-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace snapshot. The command for deleting an existing snapshot is `./ntap_dsutil_k8s.py delete jupyterlab-snapshot`.

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
./ntap_dsutil_k8s.py delete jupyterlab-snapshot --snapshot-name=ntap-dsutil.20210304151544 --namespace=dst-test
Warning: This snapshot will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting VolumeSnapshot 'ntap-dsutil.20210304151544' in namespace 'dst-test'.
VolumeSnapshot successfully deleted.
```

<a name="cli-list-jupyterlab-snapshots"></a>

#### List All Snapshots

The NetApp Data Science Toolkit can be used to list all existing JupyterLab workspace snapshots in a specific namespace. The command for listing all existing snapshots is `./ntap_dsutil_k8s.py list jupyterlab-snapshots`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    -w, --workspace-name=   Name of JupyterLab workspace to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.
```

##### Example Usage

List all VolumeSnapshots for the JupyterLab workspace named 'dave' in namespace 'default'.

```sh
./ntap_dsutil_k8s.py list jupyterlab-snapshots --workspace-name=dave
VolumeSnapshot Name         Ready to Use    Creation Time         Source PersistentVolumeClaim (PVC)    Source JupyterLab workspace    VolumeSnapshotClass
--------------------------  --------------  --------------------  ------------------------------------  -----------------------------  ---------------------
dave-snap1                  True            2021-03-11T16:24:03Z  ntap-dsutil-jupyterlab-dave           dave                           csi-snapclass
dave-snap2                  True            2021-03-11T16:29:40Z  ntap-dsutil-jupyterlab-dave           dave                           csi-snapclass
ntap-dsutil.20210310145815  True            2021-03-11T16:29:49Z  ntap-dsutil-jupyterlab-dave           dave                           csi-snapclass
```

<a name="cli-restore-jupyterlab-snapshot"></a>

#### Restore a Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously restore a specific snapshot for a JupyterLab workspace. This action will restore the corresponding workspace to its exact state at the time that the snapshot was created. The command for restoring an existing snapshot is `./ntap_dsutil_k8s.py restore jupyterlab-snapshot`.

The following options/arguments are required:

```
    -s, --snapshot-name=    Name of Kubernetes VolumeSnapshot to be restored.
```

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
```

##### Example Usage

Restore VolumeSnapshot 'ntap-dsutil.20210311164904' (for JupyterLab workspace 'mike') in namespace 'default'.

```sh
./ntap_dsutil_k8s.py restore jupyterlab-snapshot --snapshot-name=ntap-dsutil.20210311164904
Restoring VolumeSnapshot 'ntap-dsutil.20210311164904' for JupyterLab workspace 'mike' in namespace 'default'...
Scaling Deployment 'ntap-dsutil-jupyterlab-mike' in namespace 'default' to 0 pod(s).
Restoring VolumeSnapshot 'ntap-dsutil.20210311164904' for PersistentVolumeClaim 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
VolumeSnapshot successfully restored.
Scaling Deployment 'ntap-dsutil-jupyterlab-mike' in namespace 'default' to 1 pod(s).
Waiting for Deployment 'ntap-dsutil-jupyterlab-mike' to reach Ready state.
JupyterLab workspace snapshot successfully restored.
```

### Kubernetes Persistent Volume Management Operations

<a name="cli-clone-volume"></a>

#### Clone a Persistent Volume

The NetApp Data Science Toolkit can be used to near-instantaneously provision a new persistent volume (within a Kubernetes cluster) that is an exact copy of an existing persistent volume or snapshot. In other words, the NetApp Data Science Toolkit can be used to near-instantaneously clone a persistent volume. The command for cloning a persistent volume is `./ntap_dsutil_k8s.py clone volume`.

Note: Either -s/--source-snapshot-name or -v/--source-pvc-name must be specified. However, only one of these flags (not both) should be specified for a given operation. If -v/--source-pvc-name is specified, then the clone will be created from the current state of the volume. If -s/--source-snapshot-name is specified, then the clone will be created from a specific snapshot related the source volume.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

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
./ntap_dsutil_k8s.py clone volume --new-pvc-name=test2-clone1 --source-pvc-name=test2
Creating new PersistentVolumeClaim (PVC) 'test2-clone1' from source PVC 'test2' in namespace 'default'...
Creating PersistentVolumeClaim (PVC) 'test2-clone1' in namespace 'default'.
PersistentVolumeClaim (PVC) 'test2-clone1' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'test2-clone1' in namespace 'default'.
Volume successfully cloned.
```

Near-instantaneously create a new persistent volume that is an exact copy of the contents of VolumeSnapshot 'ntap-dsutil.20210304170930' in namespace 'dst-test', and attach the new persistent volume to a PVC named 'test1-clone1' in namespace 'dst-test'.

```sh
./ntap_dsutil_k8s.py clone volume --new-pvc-name=test1-clone1 --source-snapshot-name=ntap-dsutil.20210304170930 --namespace=dst-test
Creating new PersistentVolumeClaim (PVC) 'test1-clone1' from VolumeSnapshot 'ntap-dsutil.20210304170930' in namespace 'dst-test'...
Creating PersistentVolumeClaim (PVC) 'test1-clone1' in namespace 'dst-test'.
PersistentVolumeClaim (PVC) 'test1-clone1' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'test1-clone1' in namespace 'dst-test'.
Volume successfully cloned.
```

<a name="cli-create-volume"></a>

#### Create a New Persistent Volume

The NetApp Data Science Toolkit can be used to rapidly provision a new persistent volume within a Kubernetes cluster. The command for provisioning a new persistent volume is `./ntap_dsutil_k8s.py create volume`.

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
./ntap_dsutil_k8s.py create volume --pvc-name=project1 --size=1Gi
Creating PersistentVolumeClaim (PVC) 'project1' in namespace 'default'.
PersistentVolumeClaim (PVC) 'project1' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'project1' in namespace 'default'.
```

Provision a new persistent volume of size 2TB, using the Kubernetes StorageClass 'ontap-flexgroup', and attach the volume to a Kubernetes PersistentVolumeClaim (PVC) named 'test1' in namespace 'dst-test'

```sh
./ntap_dsutil_k8s.py create volume --pvc-name=test1 --size=2Ti --storage-class=ontap-flexgroup --namespace=dst-test
Creating volume 'test1' in namespace 'dst-test'.
PersistentVolumeClaim (PVC) 'test1' created. Waiting for Trident to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'test1' in namespace 'dst-test'.
```

<a name="cli-delete-volume"></a>

#### Delete an Existing Persistent Volume

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing persistent volume within a Kubernetes cluster. The command for deleting an existing persistent volume is `./ntap_dsutil_k8s.py delete volume`.

The following options/arguments are required:

```
    -p, --pvc-name=             Name of Kubernetes PersistentVolumeClaim (PVC) to be deleted.
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
./ntap_dsutil_k8s.py delete volume --pvc-name=test1 --namespace=dst-test
Warning: All data and snapshots associated with the volume will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting PersistentVolumeClaim (PVC) 'test1' in namespace 'dst-test' and associated volume.
PersistentVolumeClaim (PVC) successfully deleted.
```

<a name="cli-list-volumes"></a>

#### List All Persistent Volumes

The NetApp Data Science Toolkit can be used to print a list of all existing persistent volumes in a specific namespace within a Kubernetes cluster. The command for printing a list of all existing persistent volumes is `./ntap_dsutil_k8s.py list volumes`.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace for which to retrieve list of volumes. If not specified, namespace "default" will be used.
```

##### Example Usage

```sh
./ntap_dsutil_k8s.py list volumes --namespace=dst-test
PersistentVolumeClaim (PVC) Name    Status    Size    StorageClass    Clone    Source PVC    Source VolumeSnapshot
----------------------------------  --------  ------  --------------  -------  ------------  -----------------------
test                                Bound     10Gi    ontap-flexvol   No
test-clone1                         Bound     10Gi    ontap-flexvol   Yes      test          snap1
test-clone2                         Bound     10Gi    ontap-flexvol   Yes      test          snap2
test2                               Bound     10Gi    ontap-flexvol   No
test2-clone1                        Bound     10Gi    ontap-flexvol   Yes      test2         n/a
```

<a name="cli-create-volume-snapshot"></a>

#### Create a New Snapshot for a Persistent Volume

The NetApp Data Science Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing persistent volume. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version datasets and/or implement dataset-to-model traceability. The command for creating a new snapshot for a specific persistent volume is `./ntap_dsutil_k8s.py create volume-snapshot`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

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
./ntap_dsutil_k8s.py create volume-snapshot --pvc-name=project1
Creating VolumeSnapshot 'ntap-dsutil.20210218184654' for PersistentVolumeClaim (PVC) 'project1' in namespace 'default'.
VolumeSnapshot 'ntap-dsutil.20210218184654' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

Create a VolumeSnapshot named 'snap1, for the volume attached to the PersistentVolumeClaim (PVC) named 'test1', in namespace 'dst-test'.

```sh
./ntap_dsutil_k8s.py create volume-snapshot --pvc-name=test1 --snapshot-name=snap1 --namespace=dst-test
Creating VolumeSnapshot 'snap1' for PersistentVolumeClaim (PVC) 'test1' in namespace 'dst-test'.
VolumeSnapshot 'snap1' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

<a name="cli-delete-volume-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing persistent volume snapshot. The command for deleting an existing snapshot is `./ntap_dsutil_k8s.py delete volume-snapshot`.

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
./ntap_dsutil_k8s.py delete volume-snapshot --snapshot-name=ntap-dsutil.20210304151544 --namespace=dst-test
Warning: This snapshot will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting VolumeSnapshot 'ntap-dsutil.20210304151544' in namespace 'dst-test'.
VolumeSnapshot successfully deleted.
```

<a name="cli-list-volume-snapshots"></a>

#### List All Snapshots

The NetApp Data Science Toolkit can be used to list all existing persistent volume snapshots in a specific namespace. The command for listing all existing snapshots is `./ntap_dsutil_k8s.py list volume-snapshots`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

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
./ntap_dsutil_k8s.py list volume-snapshots
VolumeSnapshot Name         Ready to Use    Creation Time         Source PersistentVolumeClaim (PVC)    Source JupyterLab workspace    VolumeSnapshotClass
--------------------------  --------------  --------------------  ------------------------------------  -----------------------------  ---------------------
ntap-dsutil.20210309141230  True            2021-03-11T16:24:03Z  ntap-dsutil-jupyterlab-mike           mike                           csi-snapclass
snap1                       True            2021-03-11T16:29:40Z  test                                                                 csi-snapclass
snap2                       True            2021-03-11T16:29:49Z  test                                                                 csi-snapclass
```

<a name="cli-restore-volume-snapshot"></a>

#### Restore a Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously restore a specific snapshot for a persistent volume. This action will restore the corresponding volume to its exact state at the time that the snapshot was created. The command for restoring an existing snapshot is `./ntap_dsutil_k8s.py restore volume-snapshot`.

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
./ntap_dsutil_k8s.py restore volume-snapshot --snapshot-name=snap1
Warning: In order to restore a snapshot, the PersistentVolumeClaim (PVC) associated the snapshot must NOT be mounted to any pods.
Are you sure that you want to proceed? (yes/no): yes
Restoring VolumeSnapshot 'snap1' for PersistentVolumeClaim 'project1' in namespace 'default'.
VolumeSnapshot successfully restored.
```

<a name="library-of-functions"></a>

## Advanced: Importable Library of Functions

The NetApp Data Science Toolkit for Kubernetes can also be utilized as a library of functions that can be imported into any Python program or Jupyter Notebook. In this manner, data scientists and data engineers can easily incorporate Kubernetes-native data management tasks into their existing projects, programs, and workflows. This functionality is only recommended for advanced users who are proficient in Python.

To import the NetApp Data Science Toolkit for Kubernetes library functions into a Python program, ensure that the `ntap_dsutil_k8s.py` file is in the same directory as the program, and include the following line of code in the program:

```py
from ntap_dsutil_k8s import cloneJupyterLab, createJupyterLab, deleteJupyterLab, listJupyterLab, createJupyterLabSnapshot, listJupyterLabSnapshot, restoreJupyterLabSnapshot, cloneVolume, createVolume, deleteVolume, listVolumes, createVolumeSnapshot, deleteVolumeSnapshot, listVolumeSnapshot, restoreVolumeSnapshot
```

Note: The prerequisite steps outlined in the [Getting Started](#getting-started) section still appy when the toolkit is being utilized as an importable library of functions.

When being utilized as an importable library of functions, the toolkit supports the following operations.

JupyterLab workspace management operations:
- [Clone a JupyterLab workspace.](#lib-clone-jupyterlab)
- [Create a new JupyterLab workspace.](#lib-create-jupyterlab)
- [Delete an existing JupyterLab workspace.](#lib-delete-jupyterlab)
- [List all JupyterLab workspaces.](#lib-list-jupyterlabs)
- [Create a new snapshot for a JupyterLab workspace.](#lib-create-jupyterlab-snapshot)
- [Delete an existing snapshot.](#lib-delete-jupyterlab-snapshot)
- [List all snapshots.](#lib-list-jupyterlab-snapshots)
- [Restore a snapshot.](#lib-restore-jupyterlab-snapshot)

Kubernetes persistent volume management operations (for advanced Kubernetes users):
- [Clone a persistent volume.](#lib-clone-volume)
- [Create a new persistent volume.](#lib-create-volume)
- [Delete an existing persistent volume.](#lib-delete-volume)
- [List all persistent volumes.](#lib-list-volumes)
- [Create a new snapshot for a persistent volume.](#lib-create-volume-snapshot)
- [Delete an existing snapshot.](#lib-delete-volume-snapshot)
- [List all snapshots.](#lib-list-volume-snapshots)
- [Restore a snapshot.](#lib-restore-volume-snapshot)

### JupyterLab Workspace Management Operations

<a name="lib-clone-jupyterlab"></a>

#### Clone a JupyterLab Workspace

The NetApp Data Science Toolkit can be used to near-instantaneously provision a new JupyterLab workspace (within a Kubernetes cluster), that is an exact copy of an existing JupyterLab workspace or JupyterLab workspace snapshot, as part of any Python program or workflow. In other words, the NetApp Data Science Toolkit can be used to near-instantaneously clone a JupyterLab workspace as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

##### Function Definition

```py
def cloneJupyterLab(
    newWorkspaceName: str,                          # Name of new workspace (name to be applied to new JupyterLab workspace) (required).
    sourceWorkspaceName: str,                       # Name of JupyterLab workspace to use as source for clone. (required).
    sourceSnapshotName: str = None,                 # Name of Kubernetes VolumeSnapshot to use as source for clone.
    newWorkspacePassword: str = None,               # Workspace password (this password will be required in order to access the workspace). If not specified, you will be prompted to enter a password via the console.
    volumeSnapshotClass: str = "csi-snapclass",     # Kubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                     # Kubernetes namespace that source workspace is located in. If not specified, namespace "default" will be used.
    requestCpu: str = None,                         # Number of CPUs to reserve for new JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    requestMemory: str = None,                      # Amount of memory to reserve for newe JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    requestNvidiaGpu: str = None,                   # Number of NVIDIA GPUs to allocate to new JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    printOutput: bool = False                       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

This function will return a string containing the URL that you can use to access the workspace.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-create-jupyterlab"></a>

#### Create a New JupyterLab Workspace

The NetApp Data Science Toolkit can be used to rapidly provision a new JupyterLab workspace within a Kubernetes cluster as part of any Python program or workflow. Workspaces provisioned using the NetApp Data Science Toolkit will be backed by NetApp persistent storage and, thus, will persist across any shutdowns or outages in the Kubernetes environment.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/) for more information on StorageClasses.

##### Function Definition

```py
def createJupyterLab(
    workspaceName: str,                                     # Name of new JupyterLab workspace (required).
    workspaceSize: str,                                     # Size new workspace (i.e. size of backing persistent volume to be created) (required). Format: '1024Mi', '100Gi', '10Ti', etc.
    storageClass: str = None,                               # Kubernetes StorageClass to use when provisioning backing volume for new workspace. If not specified, default StorageClass will be used. Note: StorageClass must be configured to use Trident.
    namespace: str = "default",                             # Kubernetes namespace to create new workspace in. If not specified, workspace will be created in namespace "default".
    workspacePassword: str = None,                          # Workspace password (this password will be required in order to access the workspace). If not specified, you will be prompted to enter a password via the console.
    workspaceImage: str = "jupyter/tensorflow-notebook",    # Container image to use when creating workspace. If not specified, "jupyter/tensorflow-notebook" will be used.
    requestCpu: str = None,                                 # Number of CPUs to reserve for JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    requestMemory: str = None,                              # Amount of memory to reserve for JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    requestNvidiaGpu: str = None,                           # Number of NVIDIA GPUs to allocate to JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    printOutput: bool = False                               # Denotes whether or not to print messages to the console during execution.
) -> str :
```

##### Return Value

This function will return a string containing the URL that you can use to access the workspace.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-delete-jupyterlab"></a>

#### Delete an Existing JupyterLab Workspace

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def deleteJupyterLab(
    workspaceName: str,                 # Name of JupyterLab workspace to be deleted (required).
    namespace: str = "default",         # Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
    preserveSnapshots: bool = False,    # Denotes whether or not to preserve VolumeSnapshots associated with workspace (if set to False, all VolumeSnapshots associated with workspace will be deleted).
    printOutput: bool = False           # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-list-jupyterlabs"></a>

#### List All JupyterLab Workspaces

The NetApp Data Science Toolkit can be used to retrieve a list of all existing JupyterLab workspaces in a specific namespace within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def listJupyterLabs(
    namespace: str = "default",     # Kubernetes namespace for which to retrieve list of workspaces. If not specified, namespace "default" will be used.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing JupyterLab workspaces. Each item in the list will be a dictionary containing details regarding a specific workspace. The keys for the values in this dictionary are "Workspace Name", "Status", "Size", "StorageClass", "Access URL".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-create-jupyterlab-snapshot"></a>

#### Create a New Snapshot for a JupyterLab Workspace

The NetApp Data Science Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing JupyterLab workspace as part of any Python program or workflow. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version workspaces and/or implement workspace-to-model traceability.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def createJupyterLabSnapshot(
    workspaceName: str,                             # Name of JupyterLab workspace (required).
    snapshotName: str = None,                       # Name of new Kubernetes VolumeSnapshot for workspace. If not specified, will be set to 'ntap-dsutil.<timestamp>'.
    volumeSnapshotClass: str = "csi-snapclass",     # Kubernetes VolumeSnapshotClass to use when creating snapshot of backing volume for workspace. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                     # Kubernetes namespace that workspace is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False                       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-delete-jupyterlab-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace snapshot as part of any Python program or workflow. 

##### Function Definition

To delete a JupyterLab workspace snapshot, use the [deleteVolumeSnapshot function](#lib-delete-volume-snapshot).

<a name="lib-list-jupyterlab-snapshots"></a>

#### List all Snapshots

The NetApp Data Science Toolkit can be used to list all existing JupyterLab workspace snapshots in a specific namespace as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def listJupyterLabSnapshots(
    workspaceName: str = None,      # Name of JupyterLab workspace to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.
    namespace: str = "default",     # Kubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing snapshots. Each item in the list will be a dictionary containing details regarding a specific snapshot. The keys for the values in this dictionary are "VolumeSnapshot Name", "Ready to Use" (True/False), "Creation Time", "Source PersistentVolumeClaim (PVC)", "Source JupyterLab workspace", "VolumeSnapshotClass".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-restore-jupyterlab-snapshot"></a>

#### Restore a Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously restore a specific snapshot for a JupyterLab workspace as part of any Python program or workflow. This action will restore the corresponding workspace to its exact state at the time that the snapshot was created.

##### Function Definition

```py
def restoreJupyterLabSnapshot(
    snapshotName: str,              # Name of Kubernetes VolumeSnapshot to be restored (required).
    namespace: str = "default",     # Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

### Kubernetes Persistent Volume Management Operations

<a name="lib-clone-volume"></a>

#### Clone a Persistent Volume

The NetApp Data Science Toolkit can be used to near-instantaneously provision a new persistent volume (within a Kubernetes cluster) that is an exact copy of an existing persistent volume or snapshot, as part of any Python program or workflow. In other words, the NetApp Data Science Toolkit can be used to near-instantaneously clone a persistent volume as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

##### Function Definition

```py
def cloneVolume(
    newPvcName: str,                                # Name of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC) (required).
    sourcePvcName: str,                             # Name of Kubernetes PersistentVolumeClaim (PVC) to use as source for clone (required).
    sourceSnapshotName: str = None,                 # Name of Kubernetes VolumeSnapshot to use as source for clone.
    volumeSnapshotClass: str = "csi-snapclass",     # Kubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                     # Kubernetes namespace that source PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False                       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-create-volume"></a>

#### Create a New Persistent Volume

The NetApp Data Science Toolkit can be used to rapidly provision a new persistent volume within a Kubernetes cluster as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/) for more information on StorageClasses.

##### Function Definition

```py
def createVolume(
    pvcName: str,               # Name of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC) (required).
    volumeSize: str,            # Size of new volume. Format: '1024Mi', '100Gi', '10Ti', etc (required).
    storageClass: str = None,   # Kubernetes StorageClass to use when provisioning new volume. If not specified, default StorageClass will be used. Note: StorageClass must be configured to use Trident.
    namespace: str = "default", # Kubernetes namespace to create new PersistentVolumeClaim (PVC) in. If not specified, PVC will be created in namespace "default".
    printOutput: bool = False   # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-delete-volume"></a>

#### Delete an Existing Persistent Volume

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing persistent volume within a Kubernetes cluster as part of any Python program or workflow. 

##### Function Definition

```py
def deleteVolume(
    pvcName: str,                       # Name of Kubernetes PersistentVolumeClaim (PVC) to be deleted (required).
    namespace: str = "default",         # Kubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    preserveSnapshots: bool = False,    # Denotes whether or not to preserve VolumeSnapshots associated with PersistentVolumeClaim (PVC)  (if set to False, all VolumeSnapshots associated with PVC will be deleted).
    printOutput: bool = False           # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-list-volumes"></a>

#### List All Data Volumes

The NetApp Data Science Toolkit can be used to retrieve a list of all existing persistent volumes in a specific namespace within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def listVolumes(
    namespace: str = "default",     # Kubernetes namespace for which to retrieve list of volumes. If not specified, namespace "default" will be used.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing volumes. Each item in the list will be a dictionary containing details regarding a specific volume. The keys for the values in this dictionary are "PersistentVolumeClaim (PVC) Name", "Status", "Size", "StorageClass", "Clone" (yes/no), "Source PVC", "Source VolumeSnapshot".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-create-volume-snapshot"></a>

#### Create a New Snapshot for a Persistent Volume

The NetApp Data Science Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing persistent volume as part of any Python program or workflow. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version datasets and/or implement dataset-to-model traceability.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def createVolumeSnapshot(
    pvcName: str,                                   # Name of Kubernetes PersistentVolumeClaim (PVC) to create snapshot for (required).
    snapshotName: str = None,                       # Name of new Kubernetes VolumeSnapshot. If not specified, will be set to 'ntap-dsutil.<timestamp>'.
    volumeSnapshotClass: str = "csi-snapclass",     # Kubernetes VolumeSnapshotClass to use when creating snapshot. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                     # Kubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False                       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-delete-volume-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously delete an existing snapshot as part of any Python program or workflow. 

##### Function Definition

```py
def deleteVolumeSnapshot(
    snapshotName: str,              # Name of Kubernetes VolumeSnapshot to be deleted (required).
    namespace: str = "default",     # Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-list-volume-snapshots"></a>

#### List all Snapshots

The NetApp Data Science Toolkit can be used to list all existing persistent volume snapshots in a specific namespace as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/stable-v21.01/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def listVolumeSnapshots(
    pvcName: str = None,            # Name of Kubernetes PersistentVolumeClaim (PVC) to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.
    namespace: str = "default",     # Kubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing snapshots. Each item in the list will be a dictionary containing details regarding a specific snapshot. The keys for the values in this dictionary are "VolumeSnapshot Name", "Ready to Use" (True/False), "Creation Time", "Source PersistentVolumeClaim (PVC)", "Source JupyterLab workspace", "VolumeSnapshotClass".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-restore-volume-snapshot"></a>

#### Restore a Snapshot

The NetApp Data Science Toolkit can be used to near-instantaneously restore a specific snapshot for a persistent volume as part of any Python program or workflow. This action will restore the corresponding volume to its exact state at the time that the snapshot was created.

Warning: In order to restore a snapshot, the PersistentVolumeClaim (PVC) associated the snapshot must NOT be mounted to any pods.
Tip: If the PVC associated with the snapshot is currently mounted to a pod that is managed by a deployment, you can scale the deployment to 0 pods using the command `kubectl scale --replicas=0 deployment/<deployment_name>`. After scaling the deployment to 0 pods, you will be able to restore the snapshot. After restoring the snapshot, you can use the `kubectl scale` command to scale the deployment back to the desired number of pods.

##### Function Definition

```py
def restoreVolumeSnapshot(
    snapshotName: str,              # Name of Kubernetes VolumeSnapshot to be restored (required).
    namespace: str = "default",     # Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    printOutput: bool = False       # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `ntap_dsutil_k8s.py`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
