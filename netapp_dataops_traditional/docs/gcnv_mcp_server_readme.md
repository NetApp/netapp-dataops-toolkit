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

The MCP server uses **Application Default Credentials (ADC)** with **service account impersonation**, Google's recommended secure authentication approach that eliminates the need for service account key files.

#### Step 1: User Authentication

1. **Install Google Cloud SDK**: Follow the [installation guide](https://cloud.google.com/sdk/docs/install)

2. **Authenticate with your Google account**:
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

#### Step 2: Service Account Setup (One-time Admin Task)

1. **Create a dedicated service account for GCNV operations**:
   ```bash
   gcloud iam service-accounts create gcnv-dataops \
       --display-name="GCNV DataOps Service Account"
   ```

2. **Grant NetApp Cloud Volumes Admin role to the service account**:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
       --member="serviceAccount:gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/netappcloudvolumes.admin"
   ```

3. **Grant impersonation permission to your user account**:
   ```bash
   gcloud iam service-accounts add-iam-policy-binding \
       gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com \
       --member="user:YOUR_EMAIL@company.com" \
       --role="roles/iam.serviceAccountTokenCreator"
   ```

#### Step 3: Configure Auto-Impersonation

1. **Enable automatic service account impersonation**:
   ```bash
   gcloud config set auth/impersonate_service_account \
       gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Verify configuration**:
   ```bash
   gcloud config get-value auth/impersonate_service_account
   ```

#### Step 4: Enable NetApp API

1. **Enable the NetApp API**:
   ```bash
   gcloud services enable netapp.googleapis.com
   ```

2. **Verify API is enabled**:
   ```bash
   gcloud services list --enabled --filter="name:netapp.googleapis.com"
   ```

#### Benefits of Service Account Impersonation

- **No Key Files**: Eliminates security risks from leaked service account keys
- **Automatic Expiration**: Tokens expire automatically (no perpetual credentials)
- **Centralized Access Control**: Manage permissions via IAM, not key files
- **Audit Trail**: All operations traced to your user account
- **Principle of Least Privilege**: Users get only what they need via impersonation

> **Security Warning**: Never use service account key files in production. They can be leaked, never expire, and violate Google Cloud security best practices.

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

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   ```bash
   # Re-authenticate your user account
   gcloud auth login
   gcloud auth application-default login
   
   # Verify impersonation is configured
   gcloud config get-value auth/impersonate_service_account
   ```

2. **Permission Denied Errors**:
   ```bash
   # Verify your user has Token Creator role
   gcloud iam service-accounts get-iam-policy \
       gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com
   
   # Verify service account has NetApp permissions
   gcloud projects get-iam-policy YOUR_PROJECT_ID \
       --flatten="bindings[].members" \
       --filter="bindings.members:serviceAccount:gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com"
   ```

3. **API Not Enabled**:
   ```bash
   gcloud services enable netapp.googleapis.com --project=YOUR_PROJECT_ID
   gcloud services list --enabled --filter="name:netapp.googleapis.com"
   ```

4. **Impersonation Not Working**:
   ```bash
   # Test impersonation
   gcloud projects describe YOUR_PROJECT_ID --impersonate-service-account=gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com
   
   # If it fails, re-grant Token Creator role
   gcloud iam service-accounts add-iam-policy-binding \
       gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com \
       --member="user:YOUR_EMAIL@company.com" \
       --role="roles/iam.serviceAccountTokenCreator"
   ```

5. **Module Not Found**: 
   ```bash
   # Ensure the package is properly installed with GCP extras
   pip install 'netapp-dataops-traditional[gcp]'
   ```

### Security Best Practices

- **Use service account impersonation** (eliminates key file risks)
- **Grant minimal permissions** (principle of least privilege)
- **Enable audit logging** for compliance and security monitoring
- **Regularly review IAM permissions** and remove unnecessary access
- **Never use service account key files** (they can be leaked and never expire)
- **Never commit credentials** to version control

### Validation Commands

Before using the MCP server, validate your setup:

```bash
# Check authentication
gcloud auth list

# Verify project configuration
gcloud config get-value project

# Verify impersonation configuration
gcloud config get-value auth/impersonate_service_account

# Test API access with impersonation
gcloud services list --enabled --filter="name:netapp.googleapis.com"

# Verify service account exists
gcloud iam service-accounts describe gcnv-dataops@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.