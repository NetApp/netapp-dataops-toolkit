NetApp DataOps Toolkit
=========

The NetApp DataOps Toolkit is a Python-based tool that simplifies the management of development/training workspaces and inference servers that are backed by high-performance, scale-out NetApp storage. Key capabilities include:
- Rapidly provision new high-capacity JupyterLab workspaces that are backed by high-performance, scale-out NetApp storage.
- Rapidly provision new NVIDIA Triton Inference Server instances that are backed by enterprise-class NetApp storage.
- Near-instaneously clone high-capacity JupyterLab workspaces in order to enable experimentation or rapid iteration.
- Near-instaneously save snapshots of high-capacity JupyterLab workspaces for backup and/or traceability/baselining.
- Near-instaneously provision, clone, and snapshot scale-out data volumes.

## Getting Started

The latest stable release of the NetApp DataOps Toolkit is version 2.4.0. It is recommended to always use the latest stable release. You can access the documentation for the latest stable release [here](https://github.com/NetApp/netapp-dataops-toolkit/tree/v2.4.0)

The NetApp DataOps Toolkit comes in two different flavors. For access to the most capabilities, we recommend using the [NetApp DataOps Toolkit for Kubernetes](netapp_dataops_k8s/). This flavor supports the full functionality of the toolkit, including JupyterLab workspace and NVIDIA Triton Inference Server management capabilities, but requires access to a Kubernetes cluster. 

If you do not have access to a Kubernetes cluster, then you can use the [NetApp DataOps Toolkit for Traditional Environments](netapp_dataops_traditional/). However, this flavor only supports data volume management capabilities. It does not support the JupyterLab workspace and NVIDIA Triton Inference Server management capabilities that are available with the NetApp DataOps Toolkit for Kubernetes.

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.
