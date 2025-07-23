# mcp_server_k8s

## Description

NetApp DataOps Toolkit MCP Server is an open-source, Python-based server component that makes your Kubernetes DataOps environments accessible via the Model Context Protocol (MCP). The MCP server enables standardized, interactive, and programmatic connectivity between DataOps resources and modern ML/ data platforms supporting the MCP standard.

>[!NOTE]
>This MCP server uses the stdio transport, as shown in the [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server), making it a "local MCP server". 

## Quick Start

### Prerequisites

- Python >= 3.10
- Access to a Kubernetes environment with NetApp DataOps Toolkit setup.

Install with pip:

    ```sh
    pip install netapp_dataops_k8s
    ```

After installation, the netapp_dataops_k8s_mcp.py command will be available in your PATH for direct usage.

## Getting Started

To run the MCP tools from the MCP server, a valid kubeconfig file must be present on the local host. Refer [this section from the main README](../README.md#getting-started-standard-usage) of the NetApp DataOps Toolkit for Kubernetes to learn more.

### Usage

Run the MCP server with:

    ```sh
    netapp_dataops_k8s_mcp.py
    ```

## Available Tools

The MCP server provides the following tools for managing JupyterLab workspaces and volumes in a Kubernetes environment:

### Workspace Management Tools

- **CreateJupyterLab**: Create a new JupyterLab workspace.
- **CloneJupyterLab**: Clone an existing JupyterLab workspace.
- **ListJupyterLabs**: List all JupyterLab workspaces.
- **CreateJupyterLabSnapshot**: Create a snapshot of a JupyterLab workspace.
- **ListJupyterLabSnapshots**: List all snapshots of JupyterLab workspaces.

### Volume Management Tools

- **CreateVolume**: Create a new volume.
- **CloneVolume**: Clone an existing volume.
- **ListVolumes**: List all volumes.
- **CreateVolumeSnapshot**: Create a snapshot of a volume.
- **ListVolumeSnapshots**: List all snapshots of volumes.