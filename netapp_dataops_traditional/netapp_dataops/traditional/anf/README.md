# Azure NetApp Files (ANF) - Refactored Module

## Overview

The ANF functionality has been refactored into a clean, organized module structure for better maintainability and usability.

## New Module Structure

```
netapp_dataops/traditional/anf/
├── __init__.py                    # Package initialization and exports
├── base.py                        # Common utilities and helper functions
├── client.py                      # Azure client authentication and management
├── volume_management.py           # Volume management functions
├── snapshot_management.py         # Snapshot management functions
└── replication_management.py      # Replication management functions
```

## Usage Examples

### Import Options

You can import the entire ANF module:
```python
from netapp_dataops.traditional import anf

# Use functions with module prefix
result = anf.create_volume(...)
snapshots = anf.list_snapshots(...)
replications = anf.create_replication(...)
```

Or import specific functions:
```python
from netapp_dataops.traditional.anf import create_volume, list_volumes
from netapp_dataops.traditional.anf import create_snapshot, delete_snapshot

# Use functions directly
result = create_volume(...)
snapshots = list_volumes(...)
```

Or import from specific modules:
```python
from netapp_dataops.traditional.anf.volume_management import create_volume, clone_volume
from netapp_dataops.traditional.anf.snapshot_management import create_snapshot

# Use functions directly
result = create_volume(...)
snapshot_result = create_snapshot(...)
```

## Benefits

1. **Better Organization**: Functions are grouped by domain (volumes, snapshots, replications)
2. **Reduced Code Duplication**: Common patterns centralized in `base.py`
3. **Easier Maintenance**: Smaller, focused files
4. **Cleaner Imports**: Import only what you need
5. **Backward Compatibility**: Existing code continues to work
6. **No Changes to Main Package**: The main `__init__.py` remains untouched

## API Reference

### Volume Operations
- `create_volume()` - Create new Azure NetApp Files volumes
- `clone_volume()` - Clone existing volumes from snapshots  
- `delete_volume()` - Delete volumes
- `list_volumes()` - List all volumes in a capacity pool

### Snapshot Operations
- `create_snapshot()` - Create volume snapshots
- `delete_snapshot()` - Delete snapshots
- `list_snapshots()` - List snapshots for a volume

### Replication Operations
- `create_replication()` - Create cross-region volume replications
- `create_data_protection_volume()` - Create data protection volumes for replication

### Client Management
- `get_anf_client()` - Get authenticated Azure NetApp Files client
- `ANFClientManager` - Singleton class for managing client connections
- `reset_client()` - Clear cached client connections

### Utilities
- `_serialize()` - Convert Azure SDK objects to JSON-serializable structures
- `validate_required_params()` - Validate required parameters are provided

## Configuration

The ANF module supports two configuration approaches for streamlined usage:

### Option 1: Interactive Configuration (Recommended)

Create a configuration file with your Azure infrastructure details to simplify function calls:

```python
from netapp_dataops.traditional.anf.config import create_anf_config

# Run interactive configuration setup
create_anf_config()
```

This will prompt you for:
- Azure subscription ID
- Resource group name
- NetApp account name
- Capacity pool name
- Azure region (location)
- Virtual network name
- Subnet name
- Default protocol types (NFSv3, NFSv4.1, CIFS)

The configuration is saved to `~/.netapp_dataops/anf_config.json` and allows you to call functions with minimal parameters:

```python
# After configuration, you can use simplified calls
volume = anf.create_volume(
    volume_name="my-volume",
    creation_token="my-vol-001",
    usage_threshold=107374182400  # 100 GiB
    # All other parameters loaded from config
)
```

### Option 2: Manual Configuration

You can still pass all parameters explicitly to each function call:

```python
volume = anf.create_volume(
    resource_group_name="my-rg",
    account_name="my-account", 
    pool_name="my-pool",
    volume_name="my-volume",
    location="eastus",
    creation_token="my-vol-001",
    usage_threshold=107374182400,
    protocol_types=["NFSv3"],
    virtual_network_name="my-vnet",
    subscription_id="your-subscription-id"
)
```

### Configuration File Format

The configuration file (`~/.netapp_dataops/anf_config.json`) contains:

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

### Parameter Precedence

When both config file and function parameters are available:
1. **Function parameters** take precedence (override config values)
2. **Config file values** are used when function parameters are `None` or not provided
3. **Error** is raised if parameter is required but not found in either location

### Environment Variables

**Required for Service Principal Authentication:**
```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"  # Optional default
```

**Alternative Authentication:**
- Azure CLI: `az login`
- Managed Identity (when running on Azure)
- Visual Studio Code Azure Account
- Azure PowerShell

### Complete Usage Examples

#### Basic Volume Management with Configuration
```python
from netapp_dataops.traditional import anf
from netapp_dataops.traditional.anf.config import create_anf_config

# First-time setup: create configuration
create_anf_config()

# After configuration, simplified usage
volume = anf.create_volume(
    volume_name="data-volume",
    creation_token="data-vol-01",
    usage_threshold=107374182400  # 100 GiB
    # Other parameters loaded from config: resource_group_name, account_name, 
    # pool_name, location, virtual_network_name, protocol_types
)

# Create a snapshot
snapshot = anf.create_snapshot(
    volume_name="data-volume",
    snapshot_name="backup-001"
    # location, resource_group_name, account_name, pool_name from config
)

# Clone the volume
clone = anf.clone_volume(
    source_volume_name="data-volume",
    volume_name="data-clone",
    creation_token="data-clone-01",
    snapshot_name="backup-001"
    # Other parameters from config
)
```

#### Usage Without Configuration (Manual Parameters)
```python
from netapp_dataops.traditional import anf

# Manual parameter specification
volume = anf.create_volume(
    resource_group_name="my-rg",
    account_name="my-account",
    pool_name="my-pool",
    volume_name="data-volume",
    location="eastus",
    creation_token="data-vol-01",
    usage_threshold=107374182400,  # 100 GiB
    protocol_types=["NFSv3"],
    virtual_network_name="my-vnet"
)

snapshot = anf.create_snapshot(
    resource_group_name="my-rg",
    account_name="my-account",
    pool_name="my-pool",
    volume_name="data-volume",
    snapshot_name="backup-001",
    location="eastus"
)
```

### Cross-Region Replication
```python
from netapp_dataops.traditional import anf

# Create a new volume
volume = anf.create_volume(
    resource_group_name="my-rg",
    account_name="my-account",
    pool_name="my-pool",
    volume_name="data-volume",
    location="eastus",
    creation_token="data-vol-01",
    usage_threshold=107374182400,  # 100 GiB
    protocol_types=["NFSv3"],
    virtual_network_name="my-vnet"
)

# Create a snapshot
snapshot = anf.create_snapshot(
    resource_group_name="my-rg",
    account_name="my-account",
    pool_name="my-pool",
    volume_name="data-volume",
    snapshot_name="backup-001",
    location="eastus"
)

# Clone the volume
clone = anf.clone_volume(
    resource_group_name="my-rg",
    account_name="my-account",
    pool_name="my-pool",
    source_volume_name="data-volume",
    volume_name="data-clone",
    location="eastus",
    creation_token="data-clone-01",
    snapshot_name="backup-001",
    virtual_network_name="my-vnet"
)
```

### Cross-Region Replication
```python
# Set up disaster recovery replication
replication = anf.create_replication(
    # Source (East US)
    resource_group_name="prod-eastus-rg",
    account_name="prod-account",
    pool_name="prod-pool",
    volume_name="critical-data",
    
    # Destination (West US) - will be created
    destination_resource_group_name="dr-westus-rg",
    destination_account_name="dr-account",
    destination_pool_name="dr-pool",
    destination_volume_name="critical-data-replica",
    destination_location="westus",
    destination_creation_token="critical-data-dr",
    destination_virtual_network_name="dr-vnet"
)
```