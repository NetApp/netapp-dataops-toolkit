NetApp DataOps Toolkit for Kubernetes
=========

The NetApp DataOps Toolkit for Kubernetes is a Python library that makes it simple for developers, data scientists, DevOps engineers, and data engineers to perform various data management tasks within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new persistent volume or data science workspace, the ability to almost instantaneously clone a volume or workspace, the ability to almost instantaneously save off a snapshot of a volume or workspace for traceability/baselining, and the ability to move data between S3 compatible object storage and a Kubernetes persistent volume.

## Compatibility

The NetApp DataOps Toolkit for Kubernetes supports Linux and macOS hosts.

The toolkit must be used in conjunction with a Kubernetes cluster in order to be useful. Additionally, [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/), NetApp's dynamic storage orchestrator for Kubernetes, and/or the [BeeGFS CSI driver](https://github.com/NetApp/beegfs-csi-driver/) must be installed within the Kubernetes cluster. The toolkit simplifies performing of various data management tasks that are actually executed by a NetApp maintained CSI driver. In order to facilitate this, the toolkit communicates with the appropriate driver via the Kubernetes API.

The toolkit is currently compatible with Kubernetes versions 1.17 and above, and OpenShift versions 4.4 and above.

The toolkit is currently compatible with Trident versions 20.07 and above. Additionally, the toolkit is compatible with the following Trident backend types:

- ontap-nas
- aws-cvs
- gcp-cvs
- azure-netapp-files

The toolkit is also compatible with all versions of the BeeGFS CSI driver, though not all functionality is supported by BeeGFS.
For details on supported BeeGFS CSI driver functionality refer to the following documentation.
- [Volume Management Command Line Operations](docs/volume_management.md#command-line-functionality)
- [Workspace Management Command Line Operations](docs/workspace_management.md#command-line-functionality)


## Installation

### Prerequisites

The NetApp DataOps Toolkit for Kubernetes requires that Python 3.8 or above be installed on the local host. Additionally, the toolkit requires that pip for Python3 be installed on the local host. For more details regarding pip, including installation instructions, refer to the [pip documentation](https://pip.pypa.io/en/stable/installing/).

### Installation Instructions

To install the NetApp DataOps Toolkit for Kubernetes, run the following command.

```sh
python3 -m pip install netapp-dataops-k8s
```

<a name="getting-started"></a>

## Getting Started: Standard Usage

The NetApp DataOps Toolkit for Kubernetes can be utilized from any Linux or macOS host that has network access to the Kubernetes cluster.

The toolkit requires that a valid kubeconfig file be present on the local host, located at `$HOME/.kube/config` or at another path specified by the `KUBECONFIG` environment variable. Refer to the [Kubernetes documentation](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) for more information regarding kubeconfig files.

## Getting Started: In-cluster Usage (for advanced Kubernetes users)

The NetApp DataOps Toolkit for Kubernetes can also be utilized from within a pod that is running in the Kubernetes cluster. If the toolkit is being utilized within a pod in the Kubernetes cluster, then the pod's ServiceAccount must have the following permissions:

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
- [service-account-netapp-dataops.yaml](Examples/service-account-netapp-dataops.yaml): Manifest for a Kubernetes ServiceAccount named 'netapp-dataops' that has all of the required permissions for executing toolkit operations.
- [job-netapp-dataops.yaml](Examples/job-netapp-dataops.yaml): Manifest for a Kubernetes Job named 'netapp-dataops' that can be used as a template for executing toolkit operations.

Refer to the [Kubernetes documentation](https://kubernetes.io/docs/tasks/run-application/access-api-from-pod/) for more information on accessing the Kubernetes API from within a pod.

## Extended Functionality with Astra Control

The NetApp DataOps Toolkit provides several extended capabilities that require [Astra Control](https://cloud.netapp.com/astra). Any operation that requires Astra Control is specifically noted within the documentation as requiring Astra Control. The prerequisites outlined in this section are required in order to perform any operation that requires Astra Control.

The toolkit uses the Astra Control Python SDK to interface with the Astra Control API. The Astra Control Python SDK is installed automatically when you install the NetApp DataOps Toolkit using pip.

In order for the Astra Control Python SDK to be able to communicate with the Astra Control API, you must create a 'config.yaml' file containing your Astra Control API connection details. Refer to the [Astra Control Python SDK README](https://github.com/NetApp/netapp-astra-toolkits/tree/b478109b084ad387753d085219a8a8d3d399a4e6) for formatting details. Note that you do not need to follow the installation instructions outlined in the Astra Control Python SDK README; you only need to create the 'config.yaml' file. Once you have created the 'config.yaml' file, you must store it in one of the following locations:
- ~/.config/astra-toolkits/
- /etc/astra-toolkits/
- The directory pointed to by the shell environment variable 'ASTRATOOLKITS_CONF'

Additionally, you must set the shell environment variable 'ASTRA_K8S_CLUSTER_NAME' to the name of your specific Kubernetes cluster in Astra Control.

```sh
export ASTRA_K8S_CLUSTER_NAME="<Kubernetes_cluster_name_in_Astra_Control"
```

## Capabilities

The NetApp DataOps Toolkit for Kubernetes provides the following capabilities.

### Workspace Management

The NetApp DataOps Toolkit can be used to manage data science workspaces within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new JupyterLab workspace, the ability to almost instantaneously clone a JupyterLab workspace, and the ability to almost instantaneously save off a snapshot of a JupyterLab workspace for traceability/baselining.

Refer to the [NetApp DataOps Toolkit for Kubernetes Workspace Management](docs/workspace_management.md) documentation for more details.

### Volume Management

The NetApp DataOps Toolkit can be used to manage persistent volumes within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new persistent volume, the ability to almost instantaneously clone a persistent volume, and the ability to almost instantaneously save off a snapshot of a persistent volume for traceability/baselining.

Refer to the [NetApp DataOps Toolkit for Kubernetes Volume Management](docs/volume_management.md) documentation for more details.

### Data Movement

The NetApp DataOps Toolkit provides the ability to facilitate data movement between Kubernetes persistent volumes
and external services. The data movement operations currently provided are for use with S3 compatible services.

Refer to the [NetApp DataOps Toolkit for Kubernetes Data Movement](docs/data_movement.md) documentation for more details.

### NVIDIA Triton Inference Server Management

The NetApp DataOps Toolkit provides the ability to manage NVIDIA Triton Inference Server instances whithin a Kubernetes clusters. Some of the key capabilities that the toolkit provides are the ability to deploy a new Triton instance. 

Refer to the [NetApp DataOps Toolkit for NVIDIA Triton Inference Server Management](docs/inference_server_management.md) documentation for more details.


## Tips and Tricks

- [Use the NetApp DataOps Toolkit in conjunction with Kubeflow.](Examples/Kubeflow/)
- [Use the NetApp DataOps Toolkit in conjunction with Apache Airflow.](Examples/Airflow/)

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
