# Workspace Management with NetApp DataOps Toolkit for Kubernetes

The NetApp DataOps Toolkit for Kubernetes can be used to manage data science workspaces within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new JupyterLab workspace, the ability to almost instantaneously clone a JupyterLab workspace, and the ability to almost instantaneously save off a snapshot of a JupyterLab workspace for traceability/baselining. These workspace management capabilities are available within the toolkit's [command line utility](#command-line-functionality) and as a [set of functions](#library-of-functions) that can be imported and used from other Python programs.

<a name="command-line-functionality"></a>

## Command Line Functionality

You can perform volume management operations using the toolkit's command line utility. The command line utility supports the following operations.

| JupyterLab workspace management operations                                           | Supported by BeeGFS | Supported by Trident | Requires Astra Control |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- | ---------------------- |
| [Clone a JupyterLab workspace within the same namespace.](#cli-clone-jupyterlab)     | No                  | Yes                  | No                     |
| [Clone a JupyterLab workspace to a brand new namespace.](#cli-clone-new-jupyterlab)  | No                  | Yes                  | Yes                    |
| [Create a new JupyterLab workspace.](#cli-create-jupyterlab)                         | Yes                 | Yes                  | No                     |
| [Delete an existing JupyterLab workspace.](#cli-delete-jupyterlab)                   | Yes                 | Yes                  | No                     |
| [List all JupyterLab workspaces.](#cli-list-jupyterlabs)                             | Yes                 | Yes                  | No                     |
| [Create a new snapshot for a JupyterLab workspace.](#cli-create-jupyterlab-snapshot) | No                  | Yes                  | No                     |
| [Delete an existing snapshot.](#cli-delete-jupyterlab-snapshot)                      | No                  | Yes                  | No                     |
| [List all snapshots.](#cli-list-jupyterlab-snapshots)                                | No                  | Yes                  | No                     |
| [Restore a snapshot.](#cli-restore-jupyterlab-snapshot)                              | No                  | Yes                  | No                     |
| [Register a JupyterLab workspace with Astra Control.](#cli-register-jupyterlab)      | No                  | Yes                  | Yes                    |
| [Backup a JupyterLab workspace using Astra Control.](#cli-backup-jupyterlab)         | No                  | Yes                  | Yes                    |

### JupyterLab Workspace Management Operations

<a name="cli-clone-jupyterlab"></a>

#### Clone a JupyterLab Workspace Within the same Namespace

The NetApp DataOps Toolkit can be used to near-instantaneously provision a new JupyterLab workspace (within the same Kubernetes namespace) that is an exact copy of an existing JupyterLab workspace or JupyterLab workspace snapshot. In other words, the NetApp DataOps Toolkit can be used to near-instantaneously clone a JupyterLab workspace. The command for cloning a JupyterLab workspace is `netapp_dataops_k8s_cli.py clone jupyterlab`.

Note: Either -s/--source-snapshot-name or -j/--source-workspace-name must be specified. However, only one of these flags (not both) should be specified for a given operation. If -j/--source-workspace-name is specified, then the clone will be created from the current state of the workspace. If -s/--source-snapshot-name is specified, then the clone will be created from a specific snapshot related the source workspace.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

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
    -b, --load-balancer             Option to choose a LoadBalancer service instead of using NodePort service. If not specified, NodePort service will be utilized.
    -r, --allocate-resource=        Option to specify custom resource allocations, ex. 'nvidia.com/mig-1g.5gb=1'. If not specified, no custom resource will be allocated.
```

##### Example Usage

Near-instantaneously create a new JupyterLab workspace, named 'project1-experiment3', that is an exact copy of the current contents of existing JupyterLab workspace 'project1' in namespace 'default'. Allocate 2 NVIDIA GPUs to the new workspace and use LoadBalancer service instead of NodePort.

```sh
netapp_dataops_k8s_cli.py clone jupyterlab --new-workspace-name=project1-experiment3 --source-workspace-name=project1 --nvidia-gpu=2 --load-balancer
Creating new JupyterLab workspace 'project1-experiment3' from source workspace 'project1' in namespace 'default'...

Creating new VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' for source PVC 'ntap-dsutil-jupyterlab-project1' in namespace 'default' to use as source for clone...
Creating VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' for PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1' in namespace 'default'.
VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
Creating new PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment3' from VolumeSnapshot 'ntap-dsutil.for-clone.20210315185504' in namespace 'default'...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment3' in namespace 'default'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment3' created. Waiting for Kubernetes to bind volume to PVC.
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
To access workspace, navigate to http://10.61.188.110
JupyterLab workspace successfully cloned.
```

Near-instantaneously create a new JupyterLab workspace, named 'project1-experiment2', that is an exact copy of the contents of JupyterLab workspace VolumeSnapshot 'project1-snap1' in namespace 'default'.

```sh
netapp_dataops_k8s_cli.py clone jupyterlab -s project1-snap1 -w project1-experiment2
Creating new JupyterLab workspace 'project1-experiment2' from VolumeSnapshot 'project1-snap1' in namespace 'default'...

Creating new PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment2' from VolumeSnapshot 'project1-snap1' in namespace 'default'...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment2' in namespace 'default'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-project1-experiment2' created. Waiting for Kubernetes to bind volume to PVC.
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

<a name="cli-clone-new-jupyterlab"></a>

#### Clone a JupyterLab Workspace to a Brand New Namespace

The NetApp DataOps Toolkit can be used to rapidly provision a new JupyterLab workspace (within a brand new Kubernetes namespace) that is an exact copy of an existing JupyterLab workspace. In other words, the NetApp DataOps Toolkit can be used to rapidly clone a JupyterLab workspace to a brand new namespace. The command for cloning a JupyterLab workspace to a brand new namespace is `netapp_dataops_k8s_cli.py clone-to-new-ns jupyterlab`.

Note: This command requires Astra Control.

The following options/arguments are required:

```
    -j, --source-workspace-name=    Name of JupyterLab workspace to use as source for clone.
    -n, --new-namespace=            Kubernetes namespace to create new workspace in. This namespace must not exist; it will be created during this operation.
```

The following options/arguments are optional:

```
    -c, --clone-to-cluster-name=    Name of destination Kubernetes cluster within Astra Control. Workspace will be cloned a to a new namespace in this cluster. If not specified, then the workspace will be cloned to a new namespace within the user's current cluster.
    -h, --help                      Print help text.
    -s, --source-namespace=         Kubernetes namespace that source workspace is located in. If not specified, namespace "default" will be used.
```

##### Example Usage

Clone the JupyterLab workspace 'ws1' in namespace 'default' to a brand new namespace named 'team2'.

```sh
netapp_dataops_k8s_cli.py clone-to-new-ns jupyterlab --source-workspace-name=ws1 --new-namespace=team2
Creating new JupyterLab workspace 'ws1' in namespace 'team2' within your cluster using Astra Control...
New workspace is being cloned from source workspace 'ws1' in namespace 'default' within your cluster...

Astra SDK output:
{'type': 'application/astra-managedApp', 'version': '1.1', 'id': '9949c21c-8c36-44e8-b3cf-317eb393177f', 'name': 'ntap-dsutil-jupyterlab-ws1', 'state': 'provisioning', 'stateUnready': [], 'managedState': 'managed', 'managedStateUnready': [], 'managedTimestamp': '2021-10-11T20:36:09Z', 'protectionState': '', 'protectionStateUnready': [], 'appDefnSource': 'other', 'appLabels': [], 'system': 'false', 'namespace': 'team2', 'clusterName': 'ocp1', 'clusterID': '50b1e635-075f-42bb-bf81-3a6fd5518d2b', 'clusterType': 'openshift', 'sourceAppID': 'e6ac2e92-6abf-43c9-ac94-0437dc543149', 'sourceClusterID': '50b1e635-075f-42bb-bf81-3a6fd5518d2b', 'backupID': 'ee24afec-93c7-4226-9da3-006b2a870458', 'metadata': {'labels': [{'name': 'astra.netapp.io/labels/read-only/appType', 'value': 'clone'}], 'creationTimestamp': '2021-10-11T20:36:09Z', 'modificationTimestamp': '2021-10-11T20:36:09Z', 'createdBy': '946d8bb0-0d88-4469-baf4-8cfef52a7a90'}}

Clone operation has been initiated. The operation may take several minutes to complete.
If the new workspace is being created within your cluster, run 'netapp_dataops_k8s_cli.py list jupyterlabs -n team2 -a' to check the status of the new workspace.
```

<a name="cli-create-jupyterlab"></a>

#### Create a New JupyterLab Workspace

The NetApp DataOps Toolkit can be used to rapidly provision a new JupyterLab workspace within a Kubernetes cluster. Workspaces provisioned using the NetApp DataOps Toolkit will be backed by NetApp persistent storage and, thus, will persist across any shutdowns or outages in the Kubernetes environment. The command for creating a new JupyterLab workspace is `netapp_dataops_k8s_cli.py create jupyterlab`.

Tip: Refer to the [Trident](https://netapp-trident.readthedocs.io/) or [BeeGFS CSI driver](https://github.com/NetApp/beegfs-csi-driver/blob/master/docs/usage.md#dynamic-provisioning-workflow) documentation for more information on StorageClasses.

The following options/arguments are required:

```
    -w, --workspace-name=       Name of new JupyterLab workspace.
    -s, --size=                 Size new workspace (i.e. size of backing persistent volume to be created). Format: '1024Mi', '100Gi', '10Ti', etc.
```

The following options/arguments are optional:

```
    -c, --storage-class=        Kubernetes StorageClass to use when provisioning backing volume for new workspace. If not specified, the default StorageClass will be used. Note: The StorageClass must be configured to use Trident or the BeeGFS CSI driver.
    -g, --nvidia-gpu=           Number of NVIDIA GPUs to allocate to JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    -h, --help                  Print help text.
    -i, --image=                Container image to use when creating workspace. If not specified, "nvcr.io/nvidia/tensorflow:22.05-tf2-py3" will be used.
    -m, --memory=               Amount of memory to reserve for JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    -n, --namespace=            Kubernetes namespace to create new workspace in. If not specified, workspace will be created in namespace "default".
    -p, --cpu=                  Number of CPUs to reserve for JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    -b, --load-balancer         Option to choose a LoadBalancer service instead of using NodePort service. If not specified, NodePort service will be utilized.
    -a, --register-with-astra   Register new workspace with Astra Control (requires Astra Control).
    -v, --mount-pvc         	Option to attach an additional existing PVC that can be mounted at a spefic path whithin the container. Format: -v/--mount-pvc=existing_pvc_name:mount_point. If not specified, no additional PVC will be attached.
    -r, --allocate-resource=    Option to specify custom resource allocations, ex. 'nvidia.com/mig-1g.5gb=1'. If not specified, no custom resource will be allocated.
```

##### Example Usage

Provision a new JupyterLab workspace named 'mike' of size 10GB in namespace 'default'. Allocate 1 NVIDIA GPU to the new workspace.

```sh
netapp_dataops_k8s_cli.py create jupyterlab --workspace-name=mike --size=10Gi --nvidia-gpu=1
Set workspace password (this password will be required in order to access the workspace):
Re-enter password:

Creating persistent volume for workspace...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' created. Waiting for Kubernetes to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.

Creating Service 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
Service successfully created.

Creating Deployment 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
Deployment 'ntap-dsutil-jupyterlab-mike' created. Waiting for Deployment to reach Ready state.
Deployment successfully created.

Workspace successfully created.
To access workspace, navigate to http://10.61.188.112:31082
```

Provision a new JupyterLab workspace named 'dave', of size 2TB, in the namespace 'dst-test', using the container image 'nvcr.io/nvidia/pytorch:22.04-py3', use the Load Balancer service and Kubernetes StorageClass 'ontap-flexgroup' when provisioning the backing volume for the workspace.

```sh
netapp_dataops_k8s_cli.py create jupyterlab --namespace=dst-test --workspace-name=dave --image=nvcr.io/nvidia/pytorch:22.04-py3 --size=2Ti --load-balancer --storage-class=ontap-flexgroup
Set workspace password (this password will be required in order to access the workspace):
Re-enter password:

Creating persistent volume for workspace...
Creating PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.
PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-dave' created. Waiting for Kubernetes to bind volume to PVC.
Volume successfully created and bound to PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.

Creating Service 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.
Service successfully created.

Creating Deployment 'ntap-dsutil-jupyterlab-dave' in namespace 'dst-test'.
Deployment 'ntap-dsutil-jupyterlab-dave' created. Waiting for Deployment to reach Ready state.
Deployment successfully created.

Workspace successfully created.
To access workspace, navigate to http://10.61.188.110
```

<a name="cli-delete-jupyterlab"></a>

#### Delete an Existing JupyterLab Workspace

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace within a Kubernetes cluster. The command for deleting an existing JupyterLab workspace is `netapp_dataops_k8s_cli.py delete jupyterlab`.

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
netapp_dataops_k8s_cli.py delete jupyterlab --workspace-name=mike --namespace=dst-test
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

The NetApp DataOps Toolkit can be used to print a list of all existing JupyterLab workspaces in a specific namespace within a Kubernetes cluster. The command for printing a list of all existing JupyterLab workspaces is `netapp_dataops_k8s_cli.py list jupyterlabs`.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -h, --help                  Print help text.
    -n, --namespace=            Kubernetes namespace for which to retrieve list of workspaces. If not specified, namespace "default" will be used.
    -a, --include-astra-app-id  Include Astra Control app IDs in the output (requires Astra Control API access).
```

##### Example Usage

```sh
netapp_dataops_k8s_cli.py list jupyterlabs --namespace=dst-test
Workspace Name        Status    Size    StorageClass     Access URL                  Clone    Source Workspace    Source VolumeSnapshot
--------------------  --------  ------  ---------------  --------------------------  -------  ------------------  ------------------------------------
aj                    Ready     1Ti     ontap-flexvol    http://10.61.188.112:30590  No
dave                  Ready     2Ti     ontap-flexvol    http://10.61.188.112:30792  No
joe                   Ready     1Ti     beegfs-scratch   http://10.61.188.112:30006  No
mike                  Ready     1Ti     ontap-flexvol    http://10.61.188.112:31047  No
mike-clone1           Ready     1Ti     ontap-flexvol    http://10.61.188.112:30430  Yes      mike                ntap-dsutil.20210318204637
project1              Ready     10Gi    ontap-flexvol    http://10.61.188.112:31555  No
project1-experiment1  Ready     10Gi    ontap-flexvol    http://10.61.188.112:32363  Yes      project1            ntap-dsutil.for-clone.20210315184514
project1-experiment2  Ready     10Gi    ontap-flexvol    http://10.61.188.112:30677  Yes      project1            project1-snap1
project1-experiment3  Ready     10Gi    ontap-flexvol    http://10.61.188.112:30993  Yes      project1            ntap-dsutil.for-clone.20210315185504
rick                  Ready     2Ti     ontap-flexvol    http://10.61.188.112:31939  No
sathish               Ready     2Ti     ontap-flexvol    http://10.61.188.112:31820  No
```

Note: The value of the "Clone" field will be "Yes" only if the workspace was cloned, using the DataOps Toolkit, from a source workspace within the same namespace.

<a name="cli-create-jupyterlab-snapshot"></a>

#### Create a New Snapshot for a JupyterLab Workspace

The NetApp DataOps Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing JupyterLab workspace. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version workspaces and/or implement workspace-to-model traceability. The command for creating a new snapshot for a specific JupyterLab workspace is `netapp_dataops_k8s_cli.py create jupyterlab-snapshot`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

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
netapp_dataops_k8s_cli.py create jupyterlab-snapshot --workspace-name=mike
Creating VolumeSnapshot for JupyterLab workspace 'mike' in namespace 'default'...
Creating VolumeSnapshot 'ntap-dsutil.20210309141230' for PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
VolumeSnapshot 'ntap-dsutil.20210309141230' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

Create a VolumeSnapshot named 'snap1', for the workspace named 'rick', in namespace 'dst-test'.

```sh
netapp_dataops_k8s_cli.py create jupyterlab-snapshot --workspace-name=rick --namespace=dst-test --snapshot-name=snap1
Creating VolumeSnapshot for JupyterLab workspace 'rick' in namespace 'dst-test'...
Creating VolumeSnapshot 'snap1' for PersistentVolumeClaim (PVC) 'ntap-dsutil-jupyterlab-rick' in namespace 'dst-test'.
VolumeSnapshot 'snap1' created. Waiting for Trident to create snapshot on backing storage.
Snapshot successfully created.
```

<a name="cli-delete-jupyterlab-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace snapshot. The command for deleting an existing snapshot is `netapp_dataops_k8s_cli.py delete jupyterlab-snapshot`.

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
netapp_dataops_k8s_cli.py delete jupyterlab-snapshot --snapshot-name=ntap-dsutil.20210304151544 --namespace=dst-test
Warning: This snapshot will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting VolumeSnapshot 'ntap-dsutil.20210304151544' in namespace 'dst-test'.
VolumeSnapshot successfully deleted.
```

<a name="cli-list-jupyterlab-snapshots"></a>

#### List All Snapshots

The NetApp DataOps Toolkit can be used to list all existing JupyterLab workspace snapshots in a specific namespace. The command for listing all existing snapshots is `netapp_dataops_k8s_cli.py list jupyterlab-snapshots`.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

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
netapp_dataops_k8s_cli.py list jupyterlab-snapshots --workspace-name=dave
VolumeSnapshot Name         Ready to Use    Creation Time         Source PersistentVolumeClaim (PVC)    Source JupyterLab workspace    VolumeSnapshotClass
--------------------------  --------------  --------------------  ------------------------------------  -----------------------------  ---------------------
dave-snap1                  True            2021-03-11T16:24:03Z  ntap-dsutil-jupyterlab-dave           dave                           csi-snapclass
dave-snap2                  True            2021-03-11T16:29:40Z  ntap-dsutil-jupyterlab-dave           dave                           csi-snapclass
ntap-dsutil.20210310145815  True            2021-03-11T16:29:49Z  ntap-dsutil-jupyterlab-dave           dave                           csi-snapclass
```

<a name="cli-restore-jupyterlab-snapshot"></a>

#### Restore a Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously restore a specific snapshot for a JupyterLab workspace. This action will restore the corresponding workspace to its exact state at the time that the snapshot was created. The command for restoring an existing snapshot is `netapp_dataops_k8s_cli.py restore jupyterlab-snapshot`.

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
netapp_dataops_k8s_cli.py restore jupyterlab-snapshot --snapshot-name=ntap-dsutil.20210311164904
Restoring VolumeSnapshot 'ntap-dsutil.20210311164904' for JupyterLab workspace 'mike' in namespace 'default'...
Scaling Deployment 'ntap-dsutil-jupyterlab-mike' in namespace 'default' to 0 pod(s).
Restoring VolumeSnapshot 'ntap-dsutil.20210311164904' for PersistentVolumeClaim 'ntap-dsutil-jupyterlab-mike' in namespace 'default'.
VolumeSnapshot successfully restored.
Scaling Deployment 'ntap-dsutil-jupyterlab-mike' in namespace 'default' to 1 pod(s).
Waiting for Deployment 'ntap-dsutil-jupyterlab-mike' to reach Ready state.
JupyterLab workspace snapshot successfully restored.
```

<a name="cli-register-jupyterlab"></a>

#### Register an Existing JupyterLab Workspace with Astra Control

The NetApp DataOps Toolkit can be used to register an existing JupyterLab workspace with Astra Control. The command for registering an existing JupyterLab workspace with Astra Control is `netapp_dataops_k8s_cli.py register-with-astra jupyterlab`.

Note: This command requires Astra Control.

The following options/arguments are required:

```
    -w, --workspace-name=   Name of JupyterLab workspace to be registered.
```

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
```

##### Example Usage

Register the workspace 'mike' in namespace 'project1' with Astra Control.

```sh
netapp_dataops_k8s_cli.py register-with-astra jupyterlab -n project1 -w mike
Registering JupyterLab workspace 'mike' in namespace 'project1' with Astra Control...
JupyterLab workspace is now managed by Astra Control.
```

<a name="cli-backup-jupyterlab"></a>

#### Backup a JupyterLab Workspace Using Astra Control

The NetApp DataOps Toolkit can be used to trigger a backup of an existing JupyterLab workspace using Astra Control. The command for triggering a backup of an existing JupyterLab workspace using Astra Control is `netapp_dataops_k8s_cli.py backup-with-astra jupyterlab`.

Note: This command requires Astra Control.

The following options/arguments are required:

```
    -w, --workspace-name=   Name of JupyterLab workspace to be backed up.
    -b, --backup-name=      Name to be applied to new backup.
```

The following options/arguments are optional:

```
    -h, --help              Print help text.
    -n, --namespace=        Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
```

##### Example Usage

Backup the workspace 'ws1' in namespace 'default' using Astra Control; name the backup 'backup1'.

```sh
netapp_dataops_k8s_cli.py backup-with-astra jupyterlab --workspace-name=ws1 --backup-name=backup1
Trigerring backup of workspace 'ws1' in namespace 'default' using Astra Control...

Astra SDK output:
{'type': 'application/astra-appBackup', 'version': '1.1', 'id': 'bd4ee39e-a3f6-4cf4-a75e-2a09d71b2b03', 'name': 'backup1', 'bucketID': '1e547cee-fbb9-4097-9a64-f542a79d6e80', 'state': 'pending', 'stateUnready': [], 'metadata': {'labels': [], 'creationTimestamp': '2021-10-11T20:39:59Z', 'modificationTimestamp': '2021-10-11T20:39:59Z', 'createdBy': '946d8bb0-0d88-4469-baf4-8cfef52a7a90'}}

Backup operation has been initiated. The operation may take several minutes to complete.
Access the Astra Control dashboard to check the status of the backup operation.
```

<a name="library-of-functions"></a>

## Advanced: Set of Functions

The NetApp DataOps Toolkit for Kubernetes provides a set of functions that can be imported into any Python program or Jupyter Notebook. In this manner, data scientists and data engineers can easily incorporate Kubernetes-native data management tasks into their existing projects, programs, and workflows. This functionality is only recommended for advanced users who are proficient in Python.

```py
from netapp_dataops.k8s import clone_jupyter_lab, clone_jupyter_lab_to_new_namespace, create_jupyter_lab, delete_jupyter_lab, list_jupyter_labs, create_jupyter_lab_snapshot, list_jupyter_lab_snapshots, restore_jupyter_lab_snapshot, register_jupyter_lab_with_astra, backup_jupyter_lab_with_astra
```

The following workspace management operations are available within the set of functions.

| JupyterLab workspace management operations                                           | Supported by BeeGFS | Supported by Trident | Requires Astra Control |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- | ---------------------- |
| [Clone a JupyterLab workspace within the same namespace.](#lib-clone-jupyterlab)     | No                  | Yes                  | No                     |
| [Clone a JupyterLab workspace to a brand new namespace.](#lib-clone-new-jupyterlab)  | No                  | Yes                  | Yes                    |
| [Create a new JupyterLab workspace.](#lib-create-jupyterlab)                         | Yes                 | Yes                  | No                     |
| [Delete an existing JupyterLab workspace.](#lib-delete-jupyterlab)                   | Yes                 | Yes                  | No                     |
| [List all JupyterLab workspaces.](#lib-list-jupyterlabs)                             | Yes                 | Yes                  | No                     |
| [Create a new snapshot for a JupyterLab workspace.](#lib-create-jupyterlab-snapshot) | No                  | Yes                  | No                     |
| [Delete an existing snapshot.](#lib-delete-jupyterlab-snapshot)                      | No                  | Yes                  | No                     |
| [List all snapshots.](#lib-list-jupyterlab-snapshots)                                | No                  | Yes                  | No                     |
| [Restore a snapshot.](#lib-restore-jupyterlab-snapshot)                              | No                  | Yes                  | No                     |
| [Register a JupyterLab workspace with Astra Control.](#lib-register-jupyterlab)      | No                  | Yes                  | Yes                    |
| [Backup a JupyterLab workspace using Astra Control.](#lib-backup-jupyterlab)         | No                  | Yes                  | Yes                    |

### JupyterLab Workspace Management Operations

<a name="lib-clone-jupyterlab"></a>

#### Clone a JupyterLab Workspace Within the same Namespace

The NetApp DataOps Toolkit can be used to near-instantaneously provision a new JupyterLab workspace (within the same Kubernetes namespace), that is an exact copy of an existing JupyterLab workspace or JupyterLab workspace snapshot, as part of any Python program or workflow. In other words, the NetApp DataOps Toolkit can be used to near-instantaneously clone a JupyterLab workspace as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots and PVC cloning. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots and PVC cloning within a Kubernetes cluster.

##### Function Definition

```py
def clone_jupyter_lab(
    new_workspace_name: str,                          # Name of new workspace (name to be applied to new JupyterLab workspace) (required).
    source_workspace_name: str,                       # Name of JupyterLab workspace to use as source for clone. (required).
    source_snapshot_name: str = None,                 # Name of Kubernetes VolumeSnapshot to use as source for clone.
    load_balancer_service: bool = False,              # Option to use a LoadBalancer instead of using NodePort service. If not specified, NodePort service will be utilized.
    new_workspace_password: str = None,               # Workspace password (this password will be required in order to access the workspace). If not specified, you will be prompted to enter a password via the console.
    volume_snapshot_class: str = "csi-snapclass",     # Kubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                       # Kubernetes namespace that source workspace is located in. If not specified, namespace "default" will be used.
    request_cpu: str = None,                          # Number of CPUs to reserve for new JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    request_memory: str = None,                       # Amount of memory to reserve for newe JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    request_nvidia_gpu: str = None,                   # Number of NVIDIA GPUs to allocate to new JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    allocate_resource: str = None,                    # Option to specify custom resource allocations, ex. 'nvidia.com/mig-1g.5gb=1'. If not specified, no custom resource will be allocated.
    print_output: bool = False                        # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

This function will return a string containing the URL that you can use to access the workspace.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
ServiceUnavailableError         # A Kubernetes service is not available.
```

<a name="lib-clone-new-jupyterlab"></a>

#### Clone a JupyterLab Workspace to a Brand New Naamespace

The NetApp DataOps Toolkit can be used to rapidly provision a new JupyterLab workspace (within a brand new Kubernetes namespace) that is an exact copy of an existing JupyterLab workspace, as part of any Python program or workflow. In other words, the NetApp DataOps Toolkit can be used to rapidly clone a JupyterLab workspace to a brand new namespace.

Note: This function requires Astra Control.

##### Function Definition

```py
def clone_jupyter_lab_to_new_namespace(
    source_workspace_name: str,                     # Name of JupyterLab workspace to use as source for clone (required).
    new_namespace: str,                             # Kubernetes namespace to create new workspace in (required). This namespace must not exist; it will be created during this operation.
    source_workspace_namespace: str = "default",    # Kubernetes namespace that source workspace is located in. If not specified, namespace "default" will be used.
    clone_to_cluster_name: str = None,              # Name of destination Kubernetes cluster within Astra Control. Workspace will be cloned a to a new namespace in this cluster. If not specified, then the workspace will be cloned to a new namespace within the user's current cluster.
    print_output: bool = False                      # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes or Astra API returned an error.
AstraAppNotManagedError         # The source JupyterLab workspace has not been registered with Astra Control.
AstraClusterDoesNotExistError   # The destination cluster does not exist in Astra Control.
```

<a name="lib-create-jupyterlab"></a>

#### Create a New JupyterLab Workspace

The NetApp DataOps Toolkit can be used to rapidly provision a new JupyterLab workspace within a Kubernetes cluster as part of any Python program or workflow. Workspaces provisioned using the NetApp DataOps Toolkit will be backed by NetApp persistent storage and, thus, will persist across any shutdowns or outages in the Kubernetes environment.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/) for more information on StorageClasses.

##### Function Definition

```py
def create_jupyter_lab(
    workspace_name: str,                                                # Name of new JupyterLab workspace (required).
    workspace_size: str,                                                # Size new workspace (i.e. size of backing persistent volume to be created) (required). Format: '1024Mi', '100Gi', '10Ti', etc.
    mount_pvc: str = None,                                              # Option to attach an additional existing PVC that can be mounted at a spefic path whithin the container. Format: 'existing_pvc_name:mount_point'. If not specified, no additional PVC will be attached.
    storage_class: str = None,                                          # Kubernetes StorageClass to use when provisioning backing volume for new workspace. If not specified, the default StorageClass will be used. Note: The StorageClass must be configured to use Trident or the BeeGFS CSI driver.
    load_balancer_service: bool = False,                                # Option to use a LoadBalancer instead of using NodePort service. If not specified, NodePort service will be utilized.
    namespace: str = "default",                                         # Kubernetes namespace to create new workspace in. If not specified, workspace will be created in namespace "default".
    workspace_password: str = None,                                     # Workspace password (this password will be required in order to access the workspace). If not specified, you will be prompted to enter a password via the console.
    workspace_image: str = "nvcr.io/nvidia/tensorflow:22.05-tf2-py3",   # Container image to use when creating workspace. If not specified, "nvcr.io/nvidia/tensorflow:22.05-tf2-py3" will be used.
    request_cpu: str = None,                                            # Number of CPUs to reserve for JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    request_memory: str = None,                                         # Amount of memory to reserve for JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    request_nvidia_gpu: str = None,                                     # Number of NVIDIA GPUs to allocate to JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    register_with_astra: bool = False,                                  # Register new workspace with Astra Control (requires Astra Control).
    allocate_resource: str = None,                                      # Option to specify custom resource allocations, ex. 'nvidia.com/mig-1g.5gb=1'. If not specified, no custom resource will be allocated.    
    print_output: bool = False                                          # Denotes whether or not to print messages to the console during execution.
) -> str :
```

##### Return Value

This function will return a string containing the URL that you can use to access the workspace.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
ServiceUnavailableError         # A Kubernetes service is not available.
```

<a name="lib-delete-jupyterlab"></a>

#### Delete an Existing JupyterLab Workspace

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def delete_jupyter_lab(
    workspace_name: str,                 # Name of JupyterLab workspace to be deleted (required).
    namespace: str = "default",          # Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
    preserve_snapshots: bool = False,    # Denotes whether or not to preserve VolumeSnapshots associated with workspace (if set to False, all VolumeSnapshots associated with workspace will be deleted).
    print_output: bool = False           # Denotes whether or not to print messages to the console during execution.
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

<a name="lib-list-jupyterlabs"></a>

#### List All JupyterLab Workspaces

The NetApp DataOps Toolkit can be used to retrieve a list of all existing JupyterLab workspaces in a specific namespace within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def list_jupyter_labs(
    namespace: str = "default",             # Kubernetes namespace for which to retrieve list of workspaces. If not specified, namespace "default" will be used.
    include_astra_app_id: bool = False,     # Include Astra Control app IDs in the output (requires Astra Control API access).
    print_output: bool = False              # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing JupyterLab workspaces. Each item in the list will be a dictionary containing details regarding a specific workspace. The keys for the values in this dictionary are "Workspace Name", "Status", "Size", "StorageClass", "Access URL", "Clone" (Yes/No), "Source Workspace", and "Source VolumeSnapshot". If `include_astra_app_id` is set to `True`, then "Astra Control App ID" will also be included as a key in the dictionary.

Note: The value of the "Clone" field will be "Yes" only if the workspace was cloned, using the DataOps Toolkit, from a source workspace within the same namespace.

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-create-jupyterlab-snapshot"></a>

#### Create a New Snapshot for a JupyterLab Workspace

The NetApp DataOps Toolkit can be used to near-instantaneously save a space-efficient, read-only copy of an existing JupyterLab workspace as part of any Python program or workflow. These read-only copies are called snapshots, and are represented within a Kubernetes cluster by VolumeSnapshot objects. This functionality can be used to version workspaces and/or implement workspace-to-model traceability.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def create_jupyter_lab_snapshot(
    workspace_name: str,                             # Name of JupyterLab workspace (required).
    snapshot_name: str = None,                       # Name of new Kubernetes VolumeSnapshot for workspace. If not specified, will be set to 'ntap-dsutil.<timestamp>'.
    volume_snapshot_class: str = "csi-snapclass",    # Kubernetes VolumeSnapshotClass to use when creating snapshot of backing volume for workspace. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
    namespace: str = "default",                      # Kubernetes namespace that workspace is located in. If not specified, namespace "default" will be used.
    print_output: bool = False                       # Denotes whether or not to print messages to the console during execution.
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

<a name="lib-delete-jupyterlab-snapshot"></a>

#### Delete an Existing Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously delete an existing JupyterLab workspace snapshot as part of any Python program or workflow.

##### Function Definition

To delete a JupyterLab workspace snapshot, use the [delete_volume_snapshot() function](volume_management.md#lib-delete-volume-snapshot).

<a name="lib-list-jupyterlab-snapshots"></a>

#### List all Snapshots

The NetApp DataOps Toolkit can be used to list all existing JupyterLab workspace snapshots in a specific namespace as part of any Python program or workflow.

Tip: Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on VolumeSnapshots. There are often a few prerequisite tasks that need to be performed in order to enable VolumeSnapshots within a Kubernetes cluster.

##### Function Definition

```py
def list_jupyter_lab_snapshots(
    workspace_name: str = None,      # Name of JupyterLab workspace to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.
    namespace: str = "default",      # Kubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    print_output: bool = False       # Denotes whether or not to print messages to the console during execution.
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

<a name="lib-restore-jupyterlab-snapshot"></a>

#### Restore a Snapshot

The NetApp DataOps Toolkit can be used to near-instantaneously restore a specific snapshot for a JupyterLab workspace as part of any Python program or workflow. This action will restore the corresponding workspace to its exact state at the time that the snapshot was created.

##### Function Definition

```py
def restore_jupyter_lab_snapshot(
    snapshot_name: str,              # Name of Kubernetes VolumeSnapshot to be restored (required).
    namespace: str = "default",      # Kubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.
    print_output: bool = False       # Denotes whether or not to print messages to the console during execution.
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

<a name="lib-register-jupyterlab"></a>

#### Register an Existing JupyterLab Workspace with Astra Control

The NetApp DataOps Toolkit can be used to register an existing JupyterLab workspace with Astra Control as part of any Python program or workflow.

Note: This function requires Astra Control.

##### Function Definition

```py
def register_jupyter_lab_with_astra(
    workspace_name: str,            # Name of JupyterLab workspace to be registered (required).
    namespace: str = "default",     # Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
    print_output: bool = False      # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig or AstraSDK config file is missing or is invalid.
APIConnectionError              # The Kubernetes or Astra Control API returned an error.
AstraAppDoesNotExistError       # App does not exist in Astra. Are you sure that the workspace name is correct?
```

<a name="lib-backup-jupyterlab"></a>

#### Backup a JupyterLab Workspace Using Astra Control

The NetApp DataOps Toolkit can be used to trigger a backup of an existing JupyterLab workspace using Astra Control as part of any Python program or workflow.

Note: This function requires Astra Control.

##### Function Definition

```py
def backup_jupyter_lab_with_astra(
    workspace_name: str,            # Name of JupyterLab workspace to be backed up (required).
    backup_name: str,               # Name to be applied to new backup (required)
    namespace: str = "default",     # Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
    print_output: bool = False      # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value

None

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig or AstraSDK config file is missing or is invalid.
APIConnectionError              # The Kubernetes or Astra Control API returned an error.
AstraAppNotManagedError         # JupyterLab workspace has not been registered with Astra Control.
```
