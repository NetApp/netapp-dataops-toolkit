# NetApp DataOps Toolkit MCP Server for Azure NetApp Files (ANF)

The NetApp DataOps Toolkit MCP Server for Azure NetApp Files (ANF) is an open-source server component written in Python that provides access to Traditional DataOps Toolkit capabilities through the Model Context Protocol (MCP). The server provides a comprehensive set of tools for managing NetApp volumes in Microsoft Azure, including volume creation, cloning, snapshot management, and cross-region replication relationships.

> [!NOTE]  
> This MCP server uses the stdio transport, as shown in the [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server), making it a "local MCP server".

## Tools

- **Create Volume**: Rapidly provision new Azure NetApp Files volumes with comprehensive configuration options including protocols (NFS/SMB), performance tiers, export policies, and advanced features like encryption and tiering.
- **Clone Volume**: Create near-instantaneous, space-efficient clones of existing volumes from snapshots using NetApp's FlexClone technology.
- **List Volumes**: Retrieve a list of all existing data volumes in a specified capacity pool within your Azure NetApp Files account.
- **Create Snapshot**: Create space-efficient, read-only point-in-time copies of data volumes for versioning, backup, and recovery scenarios.
- **List Snapshots**: Retrieve a list of all snapshots for a specific Azure NetApp Files volume.
- **Create Replication**: Set up cross-region replication relationships for disaster recovery and high availability between Azure regions.
- **Create ANF Config**: Create an ANF configuration file to avoid repetitive parameters and simplify tool usage.

## Prerequisites

- Python >= 3.9
- [`uv`](https://docs.astral.sh/uv/) or [`pip`](https://pypi.org/project/pip/)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and authenticated
- Azure NetApp Files resources (NetApp Account, Capacity Pool, delegated subnet)
- Appropriate IAM permissions (NetApp Contributor role or equivalent)

## Usage Instructions

### Run with `uv` (recommended)

To run the MCP server using `uv`, run the following command. You do not need to install the NetApp DataOps Toolkit package before running this command.

```bash
uvx --from 'netapp-dataops-traditional[azure]' netapp_dataops_anf_mcp.py
```

### Install with `pip` and run from PATH

To install the NetApp DataOps Toolkit for Traditional Environments with Azure support, run the following command.

```bash
python3 -m pip install 'netapp-dataops-traditional[azure]'
```

After installation, the `netapp_dataops_anf_mcp.py` command will be available in your PATH for direct usage.

## Usage

### Azure Authentication

Before the MCP server can be used to perform ANF operations, you must authenticate with Azure and ensure proper setup:

#### Option 1: Azure CLI Authentication (Recommended)

1. **Install Azure CLI**: Follow the [installation guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

2. **Login to Azure**:
   ```bash
   az login
   ```

3. **Set your default subscription**:
   ```bash
   az account set --subscription "YOUR_SUBSCRIPTION_ID"
   ```

4. **Register NetApp resource provider** (if not already registered):
   ```bash
   az provider register --namespace Microsoft.NetApp
   ```

5. **Verify NetApp provider is registered**:
   ```bash
   az provider show --namespace Microsoft.NetApp --query "registrationState"
   ```

#### Option 2: Service Principal Authentication

1. **Create a service principal**:
   ```bash
   az ad sp create-for-rbac --name "netapp-dataops-sp" --role "NetApp Contributor" --scopes /subscriptions/YOUR_SUBSCRIPTION_ID
   ```

2. **Set environment variables**:
   ```bash
   export AZURE_CLIENT_ID="service-principal-app-id"
   export AZURE_CLIENT_SECRET="service-principal-password"
   export AZURE_TENANT_ID="your-tenant-id"
   export AZURE_SUBSCRIPTION_ID="your-subscription-id"
   ```

### ANF Configuration (Optional)

The MCP server supports an **optional configuration file** that simplifies ANF operations by storing common Azure infrastructure details. This reduces the complexity of tool usage and provides consistent defaults.

#### Setting up ANF Configuration

**Option 1: Interactive Setup (Recommended)**

```python
# Run this once to set up your ANF infrastructure defaults
from netapp_dataops.traditional.anf.config import create_anf_config
create_anf_config()
```

This interactive setup will prompt you for:
- Azure Subscription ID
- Resource Group Name
- NetApp Account Name
- Capacity Pool Name
- Azure Region/Location
- Virtual Network Name
- Subnet Name
- Default Protocol Types (NFSv3, NFSv4.1, SMB)

The configuration file will be automatically created at `~/.netapp_dataops/anf_config.json`.

#### Configuration File Location and Format

The configuration file is stored at `~/.netapp_dataops/anf_config.json` and contains your Azure NetApp Files infrastructure defaults. This file is automatically created by the interactive setup or can be manually created.

**Configuration File Structure:**

```json
{
  "subscriptionId": "your-azure-subscription-id",
  "resourceGroupName": "your-resource-group",
  "accountName": "your-netapp-account", 
  "poolName": "your-capacity-pool",
  "location": "eastus",
  "virtualNetworkName": "your-vnet",
  "subnetName": "default",
  "protocolTypes": ["NFSv3"]
}
```

#### Configuration Benefits and Usage

**Simplified Tool Usage:**

**Without Configuration:**
```
Create a volume in my-resource-group using my-netapp-account in the premium-pool located in eastus with virtual network my-vnet and subnet netapp-subnet. Name it data-volume with creation token data-vol-001 and size 500 GiB using NFSv3 protocol.
```

**With Configuration:**  
```
Create a volume named data-volume with creation token data-vol-001 and size 500 GiB.
```

The MCP server automatically uses configuration defaults for:
- Resource group name
- NetApp account name  
- Capacity pool name
- Azure region/location
- Virtual network name
- Subnet name
- Default protocol types

#### Parameter Precedence Rules

The MCP server uses the following precedence for parameter resolution:

1. **Tool parameters** (highest priority) - Parameters explicitly provided in tool calls
2. **Configuration file values** - Defaults from `~/.netapp_dataops/anf_config.json`
3. **Error** if required parameter missing from both sources

**Example Parameter Resolution:**
- If you specify `resource_group_name` in a tool call, it overrides the config file value
- If you don't specify it in the tool call, the config file value is used  
- If it's missing from both, an error is returned

This allows you to:
- Set common defaults in the configuration file
- Override specific parameters on a per-operation basis
- Maintain flexibility while reducing repetitive parameter entry

### Example JSON Config

To use the MCP server with an MCP client, you need to configure the client to use the server. For many clients (such as [VS Code](https://code.visualstudio.com/docs/copilot/chat/mcp-servers), [Claude Desktop](https://modelcontextprotocol.io/quickstart/user), and [AnythingLLM](https://docs.anythingllm.com/mcp-compatibility/overview)), this requires editing a config file that is in JSON format. Below is an example. Refer to the documentation for your MCP client for specific formatting details.

```json
{
  "mcpServers": {
    "netapp_dataops_anf_mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "'netapp-dataops-traditional[azure]'",
        "netapp_dataops_anf_mcp.py"
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
    "netapp_dataops_anf_mcp": {
      "type": "stdio",
      "command": "netapp_dataops_anf_mcp.py"
    }
  }
}
```

### Alternative: Direct Python execution

For development or testing purposes:

```json
{
  "mcpServers": {
    "netapp_dataops_anf_mcp": {
      "type": "stdio",
      "command": "python",
      "args": [
        "/path/to/netapp_dataops_anf_mcp.py"
      ]
    }
  }
}
```

## Environment Variables

You can optionally set these environment variables for authentication:

### Azure CLI Authentication
- `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID

### Service Principal Authentication
- `AZURE_CLIENT_ID`: Service principal application (client) ID
- `AZURE_CLIENT_SECRET`: Service principal password/secret
- `AZURE_TENANT_ID`: Azure Active Directory tenant ID
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID

## Tool Examples

### Creating a Volume

The MCP server exposes Azure NetApp Files operations through tools. Here are some example use cases:

```
Create a 500 GiB Premium NFS volume:
- Resource Group: "my-resource-group"
- Account: "my-netapp-account"
- Pool: "premium-pool"
- Volume Name: "data-volume-001"
- Location: "eastus"
- Creation Token: "data-vol-001"
- Virtual Network: "my-vnet"
- Subnet: "netapp-subnet"
- Size: 536870912000 bytes (500 GiB)
- Protocol: "NFSv3"
```

### Cloning a Volume

```
Clone from an existing snapshot:
- Source Volume: "production-data"
- Clone Name: "dev-environment"
- Snapshot: "daily-backup-001"
- Size can be larger than source volume
```

### Creating Cross-Region Replication

```
Set up disaster recovery:
- Source: eastus region
- Destination: westus region
- Automatic destination volume creation
- Continuous data synchronization
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**:
   ```bash
   az login
   # or check service principal credentials
   az account show
   ```

2. **NetApp Provider Not Registered**:
   ```bash
   az provider register --namespace Microsoft.NetApp
   az provider show --namespace Microsoft.NetApp --query "registrationState"
   ```

3. **Insufficient Permissions**:
   - Ensure your account has "NetApp Contributor" role
   - Verify permissions on the resource group and subscription
   ```bash
   az role assignment list --assignee YOUR_USER_ID --output table
   ```

4. **Resource Not Found**:
   - Verify NetApp Account exists and is accessible
   - Check that Capacity Pool has available space
   - Ensure delegated subnet is properly configured

5. **Configuration File Issues**:
   - Run the interactive setup to recreate the configuration:
   ```python
   from netapp_dataops.traditional.anf.config import create_anf_config
   create_anf_config()
   ```
   - Verify the configuration file format and location (`~/.netapp_dataops/anf_config.json`)
   - Check file permissions and ensure the directory is writable

6. **Module Not Found**: 
   - Ensure the package is properly installed with Azure extras
   ```bash
   pip install 'netapp-dataops-traditional[azure]'
   ```

7. **Network Configuration Issues**:
   - Verify virtual network and subnet exist in the target region
   - Check that subnet is properly delegated to Microsoft.NetApp/volumes
   - Ensure network security groups allow required traffic

### Debug Mode

For troubleshooting, you can enable debug logging by setting:

```bash
export PYTHONPATH=/path/to/netapp-dataops-toolkit
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import netapp_dataops_anf_mcp
"
```

### Validation Commands

Before using the MCP server, validate your setup:

```bash
# Check Azure authentication
az account show

# Verify NetApp resources
az netappfiles account list --resource-group YOUR_RG

# Check capacity pools
az netappfiles pool list --resource-group YOUR_RG --account-name YOUR_ACCOUNT

# Verify subnet delegation
az network vnet subnet show --resource-group YOUR_RG --vnet-name YOUR_VNET --name YOUR_SUBNET

# Test ANF configuration (if using config file)
python -c "
from netapp_dataops.traditional.anf.config import get_config_value
print('Config test:', get_config_value('subscriptionId'))
"
```

## Limitations and Considerations

### Azure NetApp Files Limits
- Volumes per capacity pool: Varies by service level and region
- Minimum volume size: 100 GiB for regular volumes
- Maximum volume size: 100 TiB for regular volumes, 500 TiB for large volumes
- Snapshot retention: Up to 255 snapshots per volume

### Performance Considerations
- Service levels affect throughput: Standard (16 MiB/s per TiB), Premium (64 MiB/s per TiB), Ultra (128 MiB/s per TiB)
- Cross-region replication introduces latency based on distance between regions
- Volume cloning is near-instantaneous but requires snapshots

### Security Best Practices
- Use service principals for production environments
- Implement proper network security groups and access controls
- Enable encryption at rest and in transit where required
- Regularly rotate authentication credentials

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.
