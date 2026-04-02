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

The MCP server uses **Application Default Credentials (ADC)** with **service account impersonation**, Google's recommended secure authentication approach.

This approach eliminates the need for service account key files, which can be leaked or never expire.

---

### Option 1: Manual Setup

#### Step 1: User Authentication

```bash
# Disable any existing impersonation before starting
gcloud config unset auth/impersonate_service_account

# Authenticate with your Google account
gcloud auth login
```

#### Step 2: Set Project

```bash
gcloud config set project YOUR_PROJECT_ID
```

#### Step 3: Enable Required APIs

> **📝 Note:** Must run as your user account, before impersonation is configured.

```bash
gcloud services enable netapp.googleapis.com iamcredentials.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled --filter="name:netapp.googleapis.com"
```

#### Step 4: Application Default Credentials

```bash
# Authenticate application default credentials
gcloud auth application-default login

# Secure the credentials file
# Default location: ~/.config/gcloud/application_default_credentials.json
# If CLOUDSDK_CONFIG env var is set, credentials will be in that directory instead
chmod 600 ~/.config/gcloud/application_default_credentials.json
```

#### Step 5: Create Service Account

```bash
gcloud iam service-accounts create YOUR_SERVICE_ACCOUNT_NAME \
    --display-name="YOUR_DISPLAY_NAME"
```

#### Step 6: Grant NetApp Permissions

> **📝 Note:** Run as your user account (before or without impersonation active).

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT_NAME@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/netappcloudvolumes.admin"
```

#### Step 7: Grant Impersonation Permission

```bash
gcloud iam service-accounts add-iam-policy-binding \
    YOUR_SERVICE_ACCOUNT_NAME@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --member="user:YOUR_EMAIL@YOUR_DOMAIN.com" \
    --role="roles/iam.serviceAccountTokenCreator"
```

#### Step 8: Configure Auto-Impersonation

```bash
gcloud config set auth/impersonate_service_account \
    YOUR_SERVICE_ACCOUNT_NAME@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Verify configuration
gcloud config get-value auth/impersonate_service_account
```

---

### Option 2: Automated Setup Script

Run the provided setup script to configure all steps automatically:

```bash
python3 -m netapp_dataops.traditional.gcnv.setup_gcnv_auth
```

> **📝 Note:** The module name matches the script filename: `setup_gcnv_auth.py`.

The script will prompt for:
- **Project ID** – Your GCP project (e.g., `my-project`)
- **Your email** – Your Google Cloud user account email
- **Service account name** – Name for the service account (default: `gcnv-dataops`)

It will then execute all 8 setup steps automatically:

```
NetApp DataOps Toolkit - GCNV Authentication Setup
====================================================

gcloud CLI exists: Google Cloud SDK 548.0.0

Configuration
-------------
  Enter Project ID: my-project
  Enter Your email: user@example.com
  Enter Service account name [gcnv-dataops]:

Continue? (yes/no): yes

Step 1/8  User authentication (browser will open)...
Authenticated

Step 2/8  Set project...
Project set to 'my-project'

Step 3/8  Enable APIs (running as your user account)...
netapp.googleapis.com enabled
iamcredentials.googleapis.com enabled

Step 4/8  Application Default Credentials (browser will open)...
ADC configured and credentials secured (chmod 600)

Step 5/8  Create service account...
Created: gcnv-dataops@my-project.iam.gserviceaccount.com

Step 6/8  Grant NetApp permissions...
roles/netappcloudvolumes.admin granted

Step 7/8  Grant impersonation permission...
user@example.com can impersonate gcnv-dataops@my-project.iam.gserviceaccount.com

Step 8/8  Configure impersonation...
Impersonation active: gcnv-dataops@my-project.iam.gserviceaccount.com

====================================================
Setup Complete!
====================================================
```

> **📝 Note:** The browser will open twice - once for user authentication (Step 1) and once for Application Default Credentials (Step 4).

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

**Issue:** "Permission denied" errors
```bash
# Verify your impersonation is configured
gcloud config get-value auth/impersonate_service_account

# Check if you have the TokenCreator role
gcloud iam service-accounts get-iam-policy \
    YOUR_SERVICE_ACCOUNT_NAME@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**Issue:** Need to temporarily disable impersonation

> **📝 Note:** Some GCP admin or billing actions require impersonation to be disabled. Re-disable it before running those commands.

```bash
# Disable impersonation
gcloud config unset auth/impersonate_service_account

# Re-enable when needed
gcloud config set auth/impersonate_service_account \
    YOUR_SERVICE_ACCOUNT_NAME@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**Issue:** `gcloud` not found or project ID missing
```bash
# Verify gcloud is installed and in PATH
gcloud --version

# Verify your active project is set (must not be empty)
gcloud config get-value project

# If unset, configure it
gcloud config set project YOUR_PROJECT_ID
```

**Issue:** Module Not Found
```bash
# Ensure the package is properly installed with GCP extras
pip install 'netapp-dataops-traditional[gcp]'
```

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.