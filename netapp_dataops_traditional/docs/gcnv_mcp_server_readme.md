# NetApp DataOps Toolkit MCP Server for Google Cloud NetApp Volumes (GCNV)

The NetApp DataOps Toolkit MCP Server for Google Cloud NetApp Volumes (GCNV) is an open-source server component written in Python that provides access to Traditional DataOps Toolkit capabilities through the Model Context Protocol (MCP). The server provides a set of tools for managing NetApp volumes in Google Cloud, including volume creation, cloning, snapshot management, and replication relationships.

> [!NOTE]  
> This MCP server uses the stdio transport, as shown in the [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server), making it a "local MCP server".

## Tools

- **Create Volume**: Rapidly provision new NetApp volumes in Google Cloud with customizable configurations including protocols, security settings, and backup policies.
- **Clone Volume**: Create near-instantaneous, space-efficient clones of existing volumes from snapshots using NetApp technology.
- **List Volumes**: Retrieve a list of all existing data volumes in a specified project and location.
- **Create Snapshot**: Create space-efficient, read-only copies of data volumes for versioning and traceability.
- **List Snapshots**: Retrieve a list of all snapshots for a specific volume.
- **Create Replication**: Set up replication relationships for efficient data replication and disaster recovery between volumes.

## Prerequisites

- Python >= 3.9
- [`uv`](https://docs.astral.sh/uv/) or [`pip`](https://pypi.org/project/pip/)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
- NetApp API enabled on GCP project

## Usage Instructions

### Run with `uv` (recommended)

To run the MCP server using `uv`, run the following command. You do not need to install the NetApp DataOps Toolkit package before running this command.

```bash
uvx --from 'netapp-dataops-traditional[gcp]' netapp_dataops_gcnv_mcp.py
```

### Install with `pip` and run from PATH

To install the NetApp DataOps Toolkit for Traditional Environments, run the following command.

```bash
python3 -m pip install 'netapp-dataops-traditional[gcp]'
```

After installation, the `netapp_dataops_gcnv_mcp.py` command will be available in your PATH for direct usage.

## Usage

### Google Cloud Authentication

Before the MCP server can be used to perform GCNV operations, you must authenticate with Google Cloud and ensure proper setup:

1. **Install Google Cloud SDK**: Follow the [installation guide](https://cloud.google.com/sdk/docs/install)

2. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   ```

3. **Set your default project**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **Authenticate application default credentials**:
   ```bash
   gcloud auth application-default login
   ```

4. **Enable the NetApp API**:
   ```bash
   gcloud services enable netapp.googleapis.com
   ```

5. **Verify API is enabled**:
   ```bash
   gcloud services list --enabled --filter="name:netapp.googleapis.com"
   ```

### Example JSON Config

To use the MCP server with an MCP client, you need to configure the client to use the server. For many clients (such as [VS Code](https://code.visualstudio.com/docs/copilot/chat/mcp-servers), [Claude Desktop](https://modelcontextprotocol.io/quickstart/user), and [AnythingLLM](https://docs.anythingllm.com/mcp-compatibility/overview)), this requires editing a config file that is in JSON format. Below is an example. Refer to the documentation for your MCP client for specific formatting details.

```json
{
  "mcpServers": {
    "netapp_dataops_gcnv_mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "'netapp-dataops-traditional[gcp]'",
        "netapp_dataops_gcnv_mcp.py"
      ]
    }
  }
}
```

### Alternative: Using `pip` installation

If you've installed the package with `pip`, you can use:

```json
{
  "mcpServers": {
    "netapp_dataops_gcnv_mcp": {
      "type": "stdio",
      "command": "netapp_dataops_gcnv_mcp.py"
    }
  }
}
```

### Alternative: Direct Python execution

For development or testing purposes:

```json
{
  "mcpServers": {
    "netapp_dataops_gcnv_mcp": {
      "type": "stdio",
      "command": "python",
      "args": [
        "/path/to/netapp_dataops_gcnv_mcp.py"
      ]
    }
  }
}
```

## Environment Variables

You can optionally set these environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key file (if not using default credentials)
- `GOOGLE_CLOUD_PROJECT`: Default project ID to use

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   ```bash
   gcloud auth login
   ```

2. **API Not Enabled**:
   ```bash
   gcloud services enable netapp.googleapis.com --project=YOUR_PROJECT_ID
   ```

3. **Module Not Found**: Ensure the package is properly installed or use the full path

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.