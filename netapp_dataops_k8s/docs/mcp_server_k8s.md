# NetApp DataOps Toolkit for Kubernetes MCP Server

## Description

NetApp DataOps Toolkit MCP Server is an open-source, Python-based server component that makes your Kubernetes DataOps environments accessible via the Model Context Protocol (MCP). The MCP server enables standardized, interactive, and programmatic connectivity between DataOps resources and modern ML/ data platforms supporting the MCP standard.

>[!NOTE]
>This MCP server uses the stdio transport, as shown in the [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server), making it a "local MCP server". 

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
- **CreateFlexCache**: Create a new FlexCache volume.

## Quick Start

### Prerequisites

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) or [pip](https://pypi.org/project/pip/)
- Access to a Kubernetes environment with NetApp Trident installed and configured. Refer to [the main README](../README.md) for full compatibility details.

To run the MCP tools from the MCP server, a valid kubeconfig file must be present on the local host. Refer to [the "Getting Started: Standard Usage" section from the main README](../README.md#getting-started) of the NetApp DataOps Toolkit for Kubernetes to learn more.

### Usage Instructions

#### Run with uv (recommended)

To run the MCP server using uv, run the following command. You do not need to install the NetApp DataOps Toolkit package before running this command.

```sh
uvx --from netapp-dataops-k8s netapp_dataops_k8s_mcp.py
```

#### Install with pip and run from PATH

To install the NetApp DataOps Toolkit for Kubernetes, run the following command.

```sh
python3 -m pip install netapp-dataops-k8s
```

After installation, the netapp_dataops_k8s_mcp.py command will be available in your PATH for direct usage.

#### Usage

##### Example JSON Config

To use the MCP server with an MCP client, you need to configure the client to use the server. For many clients (such as [VS Code](https://code.visualstudio.com/docs/copilot/chat/mcp-servers), [Claude Desktop](https://modelcontextprotocol.io/quickstart/user), and [AnythingLLM](https://docs.anythingllm.com/mcp-compatibility/overview)), this requires editing a config file that is in JSON format. Below is an example. Refer to the documentation for your MCP client for specific formatting details.

```json
{
  "mcpServers": {
    "netapp_dataops_k8s_mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "netapp-dataops-k8s",
        "netapp_dataops_k8s_mcp.py"
      ]
    }
  }
}
```
