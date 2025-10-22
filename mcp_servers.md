# MCP Servers Included in the NetApp DataOps Toolkit

The NetApp DataOps Toolkit includes multiple MCP Servers. These MCP Servers expose DataOps Toolkit capabilities as "tools" that can be utilized by AI agents.

## NetApp DataOps Toolkit MCP Server for ONTAP

The [NetApp DataOps Toolkit MCP Server for ONTAP](netapp_dataops_traditional/docs/mcp_server.md) is an MCP Server that enables AI agents to manage volumes and snapshots on an ONTAP system, including NetApp AFF and FAS appliances, Amazon FSx for NetApp ONTAP instances, and NetApp Cloud Volumes ONTAP instances.

### Available Tools

- **Create Volume**: Rapidly provision new data volumes with customizable configurations.
- **Clone Volume**: Create near-instantaneous, space-efficient clones of existing volumes using NetApp FlexClone technology.
- **List Volumes**: Retrieve a list of all existing data volumes, with optional space usage details.
- **Mount Volume**: Mount existing data volumes locally as read-only or read-write.
- **Create Snapshot**: Create space-efficient, read-only copies of data volumes for versioning and traceability.
- **List Snapshots**: Retrieve a list of all snapshots for a specific volume.
- **Create SnapMirror Relationship**: Set up SnapMirror relationships for efficient data replication.
- **List SnapMirror Relationships**: Retrieve a list of all SnapMirror relationships on the storage system.
- **Create FlexCache Volume**: Create FlexCache volumes for efficient data access and caching.

## NetApp DataOps Toolkit for Kubernetes MCP Server

The [NetApp DataOps Toolkit for Kubernetes MCP Server](netapp_dataops_k8s/docs/mcp_server_k8s.md) is an MCP Server that enables AI agents to manage persistent volumes, volume snapshots, and JupyterLab workspaces within a Kubernetes cluster. This MCP server relies on the NetApp Trident CSI driver and is compatible with NetApp AFF and FAS appliances, Amazon FSx for NetApp ONTAP, Azure NetApp Files, Google Cloud NetApp Volumes, and NetApp Cloud Volumes ONTAP.

### Available Tools

This MCP Server provides the following tools for managing JupyterLab workspaces and volumes in a Kubernetes environment:

#### Workspace Management Tools

- **CreateJupyterLab**: Create a new JupyterLab workspace.
- **CloneJupyterLab**: Clone an existing JupyterLab workspace.
- **ListJupyterLabs**: List all JupyterLab workspaces.
- **CreateJupyterLabSnapshot**: Create a snapshot of a JupyterLab workspace.
- **ListJupyterLabSnapshots**: List all snapshots of JupyterLab workspaces.

#### Volume Management Tools

- **CreateVolume**: Create a new volume.
- **CloneVolume**: Clone an existing volume.
- **ListVolumes**: List all volumes.
- **CreateVolumeSnapshot**: Create a snapshot of a volume.
- **ListVolumeSnapshots**: List all snapshots of volumes.
