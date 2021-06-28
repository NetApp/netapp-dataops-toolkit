# Kubeflow Notebook Example
This directory contains a Jupyter Notebook that demonstrates the execution of NetApp DataOps Toolkit for Kubernetes operations from within a notebook environment. This notebook is intended to be used within a [Notebook Server](https://www.kubeflow.org/docs/components/notebooks/) that was provisioned using Kubeflow but may also be compatible with other Kubernetes-based Jupyter Notebook implementations/deployments.

## Getting Started

### Prerequisites
This notebook requires the following prerequisites in order to function correctly.

- [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/), NetApp's dynamic storage orchestrator for Kubernetes, must be installed within the Kubernetes cluster.
- A cluster role that has all of the required permissions for executing NetApp DataOps Toolkit for Kubernetes operations must be present in the Kubernetes cluster. For an example, see [cluster-role-netapp-dataops.yaml](cluster-role-netapp-dataops.yaml). This file contains the manifest for a Kubernetes ClusterRole named 'netapp-dataops' that has all of the required permissions for executing toolkit operations within the cluster.
- Your Kubeflow Notebook Servers service account must be bound to the the previously mentioned cluster role within the namespace that you intend to provision your Notebook Servers in. Note that the default Kubeflow Notebook Servers service account is 'default-editor'. For an example, see [role-binding-kubeflow-netapp-dataops.yaml](role-binding-kubeflow-netapp-dataops.yaml). This file contains the manifest for a Kubernetes RoleBinding named 'kubeflow-netapp-dataops' that will bind the 'default-editor' ServiceAccount to the 'netapp-dataops' cluster role within the 'admin' namespace.

### Instructions for Use
Simply upload the [NetApp-Example.ipynb](NetApp-Example.ipynb) file to your Notebook Server, open the file, and then execute the cells within the notebook.
