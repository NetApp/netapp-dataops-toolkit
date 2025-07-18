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

### Usage

Run the MCP server with:

    ```sh
    netapp_dataops_k8s_mcp.py
    ```