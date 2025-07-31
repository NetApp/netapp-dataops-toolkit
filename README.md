NetApp DataOps Toolkit
=========

The NetApp DataOps Toolkit is a collection of Python-based client tools that simplify the management of data volumes and data science/engineering workspaces that are backed by high-performance, scale-out NetApp storage. Key capabilities include:
- Rapidly provision new data volumes (file shares) or JupyterLab workspaces that are backed by high-performance, scale-out NetApp storage.
- Near-instantaneously clone data volumes (file shares) or JupyterLab workspaces in order to enable experimentation or rapid iteration.
- Near-instantaneously save snapshots of data volumes (file shares) or JupyterLab workspaces for backup and/or traceability/baselining.
- Replicate data volumes (file shares) across different environments.

The toolkit includes MCP servers that expose many of these capabilities as "tools" that can be utilized by AI agents.

## Getting Started

The NetApp DataOps Toolkit includes the following client tools:

- The [NetApp DataOps Toolkit for Kubernetes](netapp_dataops_k8s/) includes data volume management, JupyterLab management, and data movement capabilities for users that have access to a Kubernetes cluster. 
- The [NetApp DataOps Toolkit for Traditional Environments](netapp_dataops_traditional/) includes basic data volume management capabilities. It will run on most Linux and macOS clients, and does not require Kubernetes.

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.
