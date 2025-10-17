# NetApp DataOps Toolkit – ANF Module

The **ANF module** extends the NetApp DataOps Toolkit – Traditional with support for **Azure NetApp Files (ANF)**.

This module provides simple Python APIs to:
- 🚀 Provision and manage NetApp volumes in Microsoft Azure
- 📸 Create and restore snapshots for data protection
- 🔄 Clone volumes for rapid environment duplication
- 🔗 Manage cross-region replication relationships for disaster recovery

Built on the [Azure NetApp Files Python SDK](https://docs.microsoft.com/en-us/python/api/azure-mgmt-netapp/).

## Table of Contents

- [Overview](#overview)
  - [Key Capabilities](#key-capabilities)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installation Instructions](#installation-instructions)
- [Authentication](#authentication)
  - [Option 1: Azure CLI (Recommended)](#option-1-azure-cli-recommended)
  - [Option 2: Service Principal](#option-2-service-principal)
  - [Option 3: Environment Variables](#option-3-environment-variables)
- [Available Functions](#available-functions)
  - [Function Categories](#function-categories)
- [API Reference](#api-reference)
- [1. Volume Management](#1-volume-management)
  - [🚀 Create a New Data Volume](#create-a-new-data-volume)
  - [🔄 Clone an Existing Data Volume](#clone-an-existing-data-volume)
  - [🗑️ Delete an Existing Data Volume](#delete-an-existing-data-volume)
  - [📋 List All Data Volumes](#list-all-data-volumes)
- [2. Snapshot Management](#2-snapshot-management)
  - [📸 Create a New Snapshot for a Data Volume](#create-a-new-snapshot-for-a-data-volume)
  - [🗑️ Delete an Existing Snapshot for a Data Volume](#delete-an-existing-snapshot-for-a-data-volume)
  - [📋 List All Snapshots for a Data Volume](#list-all-snapshots-for-a-data-volume)
- [3. Replication Management](#3-replication-management)
  - [🔗 Create a Cross-Region Replication](#create-a-cross-region-replication)
  - [📊 Create a Data Protection Volume](#create-a-data-protection-volume)
- [Reference Links](#reference-links)
- [Support](#support)

<a name="overview"></a>

## Overview

This module simplifies programmatic interaction with Azure NetApp Files, designed for:
- 🤖 **Automation pipelines**
- 🧠 **ML workflows**
- 🔄 **CI/CD systems**
- ☁️ **Multi-cloud data strategies**

<a name="key-capabilities"></a>

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Volume Management** | Provision, clone, and delete NetApp volumes with full configuration support |
| **Snapshot Operations** | Create point-in-time snapshots for data protection and recovery |
| **Volume Cloning** | Rapidly duplicate environments from snapshots with flexible sizing |
| **Cross-Region Replication** | Set up disaster recovery across Azure regions |
| **Advanced Features** | Support for SMB, NFS protocols, export policies, and performance tiers |

<a name="installation"></a>

## Installation

<a name="prerequisites"></a>

### Prerequisites

Before getting started, ensure you have:

| Requirement | Details |
|-------------|---------|
| **Python** | Version ≥3.9, <3.13 |
| **Azure CLI** | [Install and authenticate](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) |
| **ANF Resources** | NetApp Account, Capacity Pool, and delegated subnet |
| **IAM Permissions** | NetApp Contributor role or custom permissions |

<a name="installation-instructions"></a>

### Installation Instructions

#### With Azure Support
Installs the toolkit **with Azure NetApp Files integration** (installs `azure-mgmt-netapp`):

```bash
python3 -m pip install 'netapp-dataops-traditional[azure]'
```

> **Note:** The `[azure]` extra is required for ANF functionality and will install `azure-mgmt-netapp`, `azure-identity`, and `azure-core`.

**Benefits:**
- Faster installations – Download only what you need
- Smaller base package – Core functionality remains lightweight
- Flexible deployment – Choose cloud integrations per environment
- Compatible with pip and uv

<a name="authentication"></a>

## Authentication

Choose one of the following authentication methods:

<a name="option-1-azure-cli-recommended"></a>

### Option 1: Azure CLI (Recommended)

```bash
# Install Azure CLI (if not already installed)
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Login to Azure
az login

# Set your default subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Register NetApp resource provider (if not already registered)
az provider register --namespace Microsoft.NetApp

# Verify NetApp provider is registered
az provider show --namespace Microsoft.NetApp --query "registrationState"
```

<a name="option-2-service-principal"></a>

### Option 2: Service Principal

```bash
# Create a service principal
az ad sp create-for-rbac --name "netapp-dataops-sp" --role "NetApp Contributor" --scopes /subscriptions/YOUR_SUBSCRIPTION_ID

# Set environment variables
export AZURE_CLIENT_ID="service-principal-app-id"
export AZURE_CLIENT_SECRET="service-principal-password"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

<a name="option-3-environment-variables"></a>

### Option 3: Environment Variables

```bash
# Set required environment variables
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

> **💡 Tip:** For production environments, use Option 2 with a dedicated service principal.

<a name="available-functions"></a>

## Available Functions

Import the ANF module functions into your Python project:

```python
from netapp_dataops.traditional.anf import (
    create_volume,
    clone_volume,
    delete_volume,
    list_volumes,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    create_replication,
    create_data_protection_volume
)
```

> **📝 Note:** All prerequisite authentication steps must be completed before using these functions.

<a name="function-categories"></a>

### Function Categories

1. [Volume Management](#1-volume-management)
    - [Create a New Data Volume](#create-a-new-data-volume)
    - [Clone an Existing Data Volume](#clone-an-existing-data-volume)
    - [Delete an Existing Data Volume](#delete-an-existing-data-volume)
    - [List All Data Volumes](#list-all-data-volumes)
2. [Snapshot Management](#2-snapshot-management)
    - [Create a New Snapshot for a Data Volume](#create-a-new-snapshot-for-a-data-volume)
    - [Delete an Existing Snapshot for a Data Volume](#delete-an-existing-snapshot-for-a-data-volume)
    - [List All Snapshots for a Data Volume](#list-all-snapshots-for-a-data-volume)
3. [Replication Management](#3-replication-management)
    - [Create a Cross-Region Replication](#create-a-cross-region-replication)
    - [Create a Data Protection Volume](#create-a-data-protection-volume)

<a name="api-reference"></a>

## API Reference

<a name="1-volume-management"></a>

## 1. Volume Management

<a name="create-a-new-data-volume"></a>

### 🚀 Create a New Data Volume

Provision new Azure NetApp Files volumes with comprehensive configuration options including protocols (NFS/SMB), performance tiers, export policies, and advanced features.

#### Function Definition
```python
def create_volume(
    resource_group_name: str,                         # Required. The name of the resource group.
    account_name: str,                                # Required. The name of the NetApp account.
    pool_name: str,                                   # Required. The name of the capacity pool.
    volume_name: str,                                 # Required. The name of the volume.
    location: str,                                    # Required. Azure region (e.g., "eastus").
    creation_token: str,                              # Required. A unique file path for the volume.
    usage_threshold: int,                             # Required. Volume quota in bytes.
    protocol_types: list,                             # Required. List of protocol types (NFSv3, NFSv4.1, CIFS).
    virtual_network_name: str,                        # Required. The name of the virtual network.
    subnet_name: str = "default",                     # Optional. The name of a delegated Azure subnet.
    service_level: str = None,                        # Optional. Service level (Standard, Premium, Ultra).
    tags: dict = None,                                # Optional. Resource tags.
    zones: list = None,                               # Optional. Availability zones.
    export_policy_rules: list = None,                 # Optional. Export policy rules.
    security_style: str = None,                       # Optional. Security style (ntfs, unix).
    smb_encryption: bool = None,                      # Optional. Enables SMB3 encryption.
    smb_continuously_available: bool = None,          # Optional. Enables SMB continuous availability.
    throughput_mibps: float = None,                   # Optional. Maximum throughput in MiB/s.
    volume_type: str = None,                          # Optional. Volume type for data protection.
    data_protection: list = None,                     # Optional. Data protection settings.
    is_default_quota_enabled: bool = None,            # Optional. Enables default quota.
    default_user_quota_in_ki_bs: int = None,          # Optional. Default user quota in KiBs.
    default_group_quota_in_ki_bs: int = None,         # Optional. Default group quota in KiBs.
    unix_permissions: str = None,                     # Optional. UNIX permissions (e.g., "0777").
    avs_data_store: str = None,                       # Optional. AVS datastore enablement.
    is_large_volume: bool = None,                     # Optional. Large volume flag.
    kerberos_enabled: bool = None,                    # Optional. Kerberos enablement.
    ldap_enabled: bool = None,                        # Optional. LDAP enablement.
    cool_access: bool = None,                         # Optional. Cool Access (tiering) enablement.
    coolness_period: int = None,                      # Optional. Days before tiering data.
    snapshot_directory_visible: bool = None,          # Optional. Snapshot directory visibility.
    network_features: str = None,                     # Optional. Network features (Basic, Standard).
    encryption_key_source: str = None,               # Optional. Encryption key source.
    enable_subvolumes: str = None,                    # Optional. Subvolume operations flag.
    subscription_id: str = None,                      # Optional. Azure subscription ID.
    print_output: bool = False                        # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': Volume object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ResourceExistsError    # If the volume already exists
ValueError             # If required parameters are missing or invalid
Exception              # If there is an error during the volume creation process
```

#### Example Usage

Create a new Azure NetApp Files volume with NFS protocol support:

```python
from netapp_dataops.traditional import anf

# Create a 500 GiB Premium NFS volume
response = anf.create_volume(
    resource_group_name="my-resource-group",
    account_name="my-netapp-account",
    pool_name="my-capacity-pool",
    volume_name="demo-volume",
    location="eastus",
    creation_token="demo-volume-path",
    usage_threshold=536870912000,  # 500 GiB in bytes
    protocol_types=["NFSv3", "NFSv4.1"],
    virtual_network_name="my-vnet",
    subnet_name="netapp-subnet",
    service_level="Premium",
    tags={"environment": "development", "project": "demo"},
    unix_permissions="0755",
    print_output=True
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": {
    "id": "/subscriptions/.../resourceGroups/my-resource-group/providers/Microsoft.NetApp/netAppAccounts/my-netapp-account/capacityPools/my-capacity-pool/volumes/demo-volume",
    "name": "demo-volume",
    "location": "eastus",
    "provisioning_state": "Succeeded"
    ...
  }
}
```

<a name="clone-an-existing-data-volume"></a>

### 🔄 Clone an Existing Data Volume

Create a new volume as a clone of an existing volume using a specific snapshot. This is ideal for rapid environment duplication, testing, and development workflows.

#### Function Definition

```python
def clone_volume(
    resource_group_name: str,                         # Required. The name of the resource group.
    account_name: str,                                # Required. The name of the NetApp account.
    pool_name: str,                                   # Required. The name of the capacity pool.
    source_volume_name: str,                          # Required. The name of the source volume to clone.
    volume_name: str,                                 # Required. The name of the new clone volume.
    location: str,                                    # Required. Azure region (e.g., "eastus").
    creation_token: str,                              # Required. A unique file path for the clone.
    snapshot_name: str,                               # Required. The snapshot to clone from.
    virtual_network_name: str,                        # Required. The name of the virtual network.
    subnet_name: str = "default",                     # Optional. The name of a delegated Azure subnet.
    service_level: str = None,                        # Optional. Service level (Standard, Premium, Ultra).
    protocol_types: list = None,                      # Optional. List of protocol types.
    tags: dict = None,                                # Optional. Resource tags.
    zones: list = None,                               # Optional. Availability zones.
    export_policy_rules: list = None,                 # Optional. Export policy rules.
    security_style: str = None,                       # Optional. Security style (ntfs, unix).
    smb_encryption: bool = None,                      # Optional. Enables SMB3 encryption.
    smb_continuously_available: bool = None,          # Optional. Enables SMB continuous availability.
    throughput_mibps: float = None,                   # Optional. Maximum throughput in MiB/s.
    volume_type: str = None,                          # Optional. Volume type.
    data_protection: list = None,                     # Optional. Data protection settings.
    is_default_quota_enabled: bool = None,            # Optional. Enables default quota.
    default_user_quota_in_ki_bs: int = None,          # Optional. Default user quota in KiBs.
    default_group_quota_in_ki_bs: int = None,         # Optional. Default group quota in KiBs.
    unix_permissions: str = None,                     # Optional. UNIX permissions.
    avs_data_store: str = None,                       # Optional. AVS datastore enablement.
    is_large_volume: bool = None,                     # Optional. Large volume flag.
    kerberos_enabled: bool = None,                    # Optional. Kerberos enablement.
    ldap_enabled: bool = None,                        # Optional. LDAP enablement.
    cool_access: bool = None,                         # Optional. Cool Access (tiering) enablement.
    coolness_period: int = None,                      # Optional. Days before tiering data.
    snapshot_directory_visible: bool = None,          # Optional. Snapshot directory visibility.
    network_features: str = None,                     # Optional. Network features.
    encryption_key_source: str = None,               # Optional. Encryption key source.
    enable_subvolumes: str = None,                    # Optional. Subvolume operations flag.
    subscription_id: str = None,                      # Optional. Azure subscription ID.
    print_output: bool = False                        # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': Volume object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ResourceExistsError    # If the clone volume already exists
ResourceNotFoundError  # If the source volume or snapshot does not exist
ValueError             # If required parameters are missing or invalid
Exception              # If there is an error during the cloning process
```

#### Example Usage

Create a clone from an existing snapshot:

```python
from netapp_dataops.traditional import anf

# Clone volume from snapshot
clone_result = anf.clone_volume(
    resource_group_name="my-resource-group",
    account_name="my-netapp-account",
    pool_name="my-capacity-pool",
    source_volume_name="production-volume",
    volume_name="development-clone",
    location="eastus",
    creation_token="dev-clone-path",
    virtual_network_name="my-vnet",
    snapshot_name="daily-backup-001",
    tags={"environment": "development", "source": "production-clone"},
    print_output=True
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": {
    "id": "/subscriptions/.../resourceGroups/my-resource-group/providers/Microsoft.NetApp/netAppAccounts/my-netapp-account/capacityPools/my-capacity-pool/volumes/development-clone",
    "name": "development-clone",
    "location": "eastus",
    "provisioning_state": "Succeeded",
    "creation_token": "dev-clone-path",
    "service_level": "Premium",
    "usage_threshold": 107374182400,
    "volume_type": "DataProtection"
  }
}
```

<a name="delete-an-existing-data-volume"></a>

### 🗑️ Delete an Existing Data Volume

Remove Azure NetApp Files volumes with options for forced deletion when necessary.

#### Function Definition
```python
def delete_volume(
    resource_group_name: str,                    # Required. The name of the resource group.
    account_name: str,                           # Required. The name of the NetApp account.
    pool_name: str,                              # Required. The name of the capacity pool.
    volume_name: str,                            # Required. The name of the volume.
    force_delete: Optional[bool] = None,         # Optional. Force delete even if volume has dependencies.
    subscription_id: Optional[str] = None,       # Optional. Azure subscription ID.
    print_output: Optional[bool] = False         # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': Operation result (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ResourceNotFoundError  # If the volume does not exist
ValueError            # If required parameters are missing
Exception            # If there is an error during the volume deletion process
```

#### Example Usage
Remove a volume with force option:

```python
from netapp_dataops.traditional import anf

# Delete volume with force to clean up dependencies
delete_result = anf.delete_volume(
    resource_group_name="my-resource-group",
    account_name="my-netapp-account",
    pool_name="my-capacity-pool",
    volume_name="demo-volume",
    force_delete=True,
    print_output=True
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": {
    "message": "Volume 'demo-volume' deleted successfully",
    "volume_name": "demo-volume",
    "resource_group": "my-resource-group"
  }
}
```

<a name="list-all-data-volumes"></a>

### 📋 List All Data Volumes

Retrieve all volumes within a specific capacity pool.

#### Function Definition
```python
def list_volumes(
    resource_group_name: str,               # Required. The name of the resource group.
    account_name: str,                      # Required. The name of the NetApp account.
    pool_name: str,                         # Required. The name of the capacity pool.
    subscription_id: Optional[str] = None,  # Optional. Azure subscription ID.
    print_output: Optional[bool] = False    # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': List of volumes (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ValueError   # If required parameters are missing
Exception   # If there is an error during the volume listing process
```

#### Example Usage

Get all volumes in a capacity pool:

```python
from netapp_dataops.traditional import anf

# List all volumes in the pool
volumes = anf.list_volumes(
    resource_group_name="my-resource-group",
    account_name="my-netapp-account",
    pool_name="my-capacity-pool",
    print_output=True
)

print(f"Found {len(volumes['details'])} volumes")
for volume in volumes['details']:
    print(f"- {volume.name}: {volume.usage_threshold / (1024**3):.1f} GiB")
```

**Expected Output:**
```json
{
  "status": "success",
  "details": [
    {
      "id": "/subscriptions/.../volumes/production-volume",
      "name": "production-volume",
      "location": "eastus",
      "service_level": "Premium",
      "usage_threshold": 107374182400,
      "provisioning_state": "Succeeded",
      "creation_token": "prod-vol-01"
    },
    {
      "id": "/subscriptions/.../volumes/development-volume",
      "name": "development-volume", 
      "location": "eastus",
      "service_level": "Standard",
      "usage_threshold": 53687091200,
      "provisioning_state": "Succeeded",
      "creation_token": "dev-vol-01"
    }
  ]
}
```

<a name="2-snapshot-management"></a>

## 2. Snapshot Management

<a name="create-a-new-snapshot-for-a-data-volume"></a>

### 📸 Create a New Snapshot for a Data Volume

Create point-in-time snapshots of Azure NetApp Files volumes for backup, recovery, and cloning operations.

#### Function Definition
```python
def create_snapshot(
    resource_group_name: str,                    # Required. The name of the resource group.
    account_name: str,                           # Required. The name of the NetApp account.
    pool_name: str,                              # Required. The name of the capacity pool.
    volume_name: str,                            # Required. The name of the volume.
    snapshot_name: str,                          # Required. The name of the snapshot.
    location: str,                               # Required. Azure region.
    tags: dict = None,                           # Optional. Resource tags.
    subscription_id: str = None,                 # Optional. Azure subscription ID.
    print_output: bool = False                   # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': Snapshot object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ResourceExistsError    # If the snapshot already exists
ResourceNotFoundError  # If the volume does not exist
ValueError             # If required parameters are missing
Exception              # If there is an error during the snapshot creation process
```

#### Example Usage
Create a point-in-time snapshot:

```python
from netapp_dataops.traditional import anf

# Create snapshot for backup
snapshot_result = anf.create_snapshot(
    resource_group_name="my-resource-group",
    account_name="my-netapp-account",
    pool_name="my-capacity-pool",
    volume_name="production-volume",
    snapshot_name="weekly-backup-2024-10-15",
    location="eastus",
    tags={
        "backup_type": "weekly",
        "environment": "production",
        "created_by": "automated_backup"
    },
    print_output=True
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": {
    "id": "/subscriptions/.../snapshots/weekly-backup-2024-10-15",
    "name": "weekly-backup-2024-10-15",
    "location": "eastus",
    "provisioning_state": "Succeeded",
    "created": "2024-10-15T14:30:00Z",
    "size": 5368709120,
    "volume_name": "production-volume"
  }
}
```

<a name="delete-an-existing-snapshot-for-a-data-volume"></a>

### 🗑️ Delete an Existing Snapshot for a Data Volume

Remove snapshots when they are no longer needed for space management and cleanup.

#### Function Definition
```python
def delete_snapshot(
    resource_group_name: str,                    # Required. The name of the resource group.
    account_name: str,                           # Required. The name of the NetApp account.
    pool_name: str,                              # Required. The name of the capacity pool.
    volume_name: str,                            # Required. The name of the volume.
    snapshot_name: str,                          # Required. The name of the snapshot.
    subscription_id: str = None,                 # Optional. Azure subscription ID.
    print_output: bool = False                   # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': Operation result (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ResourceNotFoundError  # If the snapshot or volume does not exist
ValueError            # If required parameters are missing
Exception            # If there is an error during the snapshot deletion process
```

#### Example Usage

Remove an old snapshot:

```python
from netapp_dataops.traditional import anf

# Delete old snapshot
delete_snap = anf.delete_snapshot(
    resource_group_name="my-resource-group",
    account_name="my-netapp-account",
    pool_name="my-capacity-pool",
    volume_name="production-volume",
    snapshot_name="daily-backup-2024-10-01",
    print_output=True
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": {
    "message": "Snapshot 'daily-backup-2024-10-01' deleted successfully",
    "snapshot_name": "daily-backup-2024-10-01",
    "volume_name": "production-volume"
  }
}
```

<a name="list-all-snapshots-for-a-data-volume"></a>

### 📋 List All Snapshots for a Data Volume

Enumerate all snapshots associated with a specific Azure NetApp Files volume.

#### Function Definition
```python
def list_snapshots(
    resource_group_name: str,                    # Required. The name of the resource group.
    account_name: str,                           # Required. The name of the NetApp account.
    pool_name: str,                              # Required. The name of the capacity pool.
    volume_name: str,                            # Required. The name of the volume.
    subscription_id: Optional[str] = None,       # Optional. Azure subscription ID.
    print_output: Optional[bool] = False         # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': List of snapshots (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ValueError   # If required parameters are missing
Exception   # If there is an error during the snapshot listing process
```

#### Example Usage
Get all snapshots for a volume:

```python
from netapp_dataops.traditional import anf

# List all snapshots
snapshots = anf.list_snapshots(
    resource_group_name="my-resource-group",
    account_name="my-netapp-account",
    pool_name="my-capacity-pool",
    volume_name="production-volume",
    print_output=True
)

print(f"Found {len(snapshots['details'])} snapshots")
for snapshot in snapshots['details']:
    print(f"- {snapshot.name}: Created {snapshot.created}")
```

**Expected Output:**
```json
{
  "status": "success",
  "details": [
    {
      "id": "/subscriptions/.../snapshots/daily-backup-2024-10-15",
      "name": "daily-backup-2024-10-15",
      "created": "2024-10-15T14:30:00Z",
      "size": 5368709120,
      "provisioning_state": "Succeeded"
    },
    {
      "id": "/subscriptions/.../snapshots/weekly-backup-2024-10-14",
      "name": "weekly-backup-2024-10-14", 
      "created": "2024-10-14T02:00:00Z",
      "size": 5368709120,
      "provisioning_state": "Succeeded"
    }
  ]
}
```

<a name="3-replication-management"></a>

## 3. Replication Management

<a name="create-a-cross-region-replication"></a>

### 🔗 Create a Cross-Region Replication

Set up cross-region replication relationships between Azure NetApp Files volumes for disaster recovery and high availability. This function can either create a new data protection volume or use an existing one.

#### Function Definition
```python
def create_replication(
    # Source volume parameters
    resource_group_name: str,                           # Required. Source volume resource group name.
    account_name: str,                                  # Required. Source volume NetApp account name.
    pool_name: str,                                     # Required. Source volume capacity pool name.
    volume_name: str,                                   # Required. Source volume name.
    
    # For creating new destination volume:
    destination_resource_group_name: str = None,       # Optional. Destination resource group name.
    destination_account_name: str = None,              # Optional. Destination NetApp account name.
    destination_pool_name: str = None,                 # Optional. Destination capacity pool name.
    destination_volume_name: str = None,               # Optional. Destination volume name.
    destination_location: str = None,                  # Optional. Destination Azure region.
    destination_creation_token: str = None,            # Optional. Destination volume file path.
    destination_usage_threshold: int = None,           # Optional. Destination volume quota in bytes.
    destination_virtual_network_name: str = None,      # Optional. Destination virtual network.
    destination_subnet_name: str = "default",          # Optional. Destination subnet name.
    destination_zones: list = None,                    # Optional. Destination availability zones.
    destination_service_level: str = None,             # Optional. Destination service level.
    
    # For existing destination volume:
    remote_volume_resource_id: str = None,             # Optional. Resource ID of existing data protection volume.
    
    # Common parameters
    subscription_id: str = None,                       # Optional. Azure subscription ID.
    print_output: bool = False                         # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': Replication setup result (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ValueError            # If required parameters are missing or invalid
ResourceNotFoundError # If source volume does not exist
Exception             # If there is an error during the replication setup process
```

#### Example Usage
Set up cross-region replication for disaster recovery:

```python
from netapp_dataops.traditional import anf

# Create replication with new destination volume
replication_result = anf.create_replication(
    # Source volume (East US)
    resource_group_name="prod-eastus-rg",
    account_name="prod-netapp-account",
    pool_name="prod-capacity-pool",
    volume_name="critical-data-volume",
    
    # Destination volume (West US) - will be created
    destination_resource_group_name="dr-westus-rg",
    destination_account_name="dr-netapp-account", 
    destination_pool_name="dr-capacity-pool",
    destination_volume_name="critical-data-replica",
    destination_location="westus",
    destination_creation_token="critical-data-dr-path",
    destination_virtual_network_name="dr-vnet",
    destination_subnet_name="netapp-dr-subnet",
    destination_usage_threshold=214748364800,  # 200 GiB
    
    print_output=True
)

# Or use existing destination volume
replication_existing = anf.create_replication(
    resource_group_name="prod-eastus-rg",
    account_name="prod-netapp-account",
    pool_name="prod-capacity-pool", 
    volume_name="critical-data-volume",
    remote_volume_resource_id="/subscriptions/.../volumes/existing-dr-volume",
    print_output=True
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": {
    "replication_id": "/subscriptions/.../replicationVolumeReplication",
    "source_volume": "critical-data-volume",
    "destination_volume": "critical-data-replica",
    "replication_schedule": "daily",
    "mirror_state": "Mirrored",
    "relationship_status": "Idle",
    "destination_location": "westus"
  }
}
```

<a name="create-a-data-protection-volume"></a>

### 📊 Create a Data Protection Volume

Create a destination volume specifically configured for cross-region replication (data protection type).

#### Function Definition
```python
def create_data_protection_volume(
    resource_group_name: str,                           # Required. The name of the resource group.
    account_name: str,                                  # Required. The name of the NetApp account.
    pool_name: str,                                     # Required. The name of the capacity pool.
    volume_name: str,                                   # Required. The name of the volume.
    location: str,                                      # Required. Azure region.
    creation_token: str,                                # Required. A unique file path for the volume.
    usage_threshold: int,                               # Required. Volume quota in bytes.
    virtual_network_name: str,                          # Required. The name of the virtual network.
    subnet_name: str,                                   # Required. The name of a delegated Azure subnet.
    source_volume_resource_id: str,                     # Required. Resource ID of the source volume.
    zones: list = None,                                 # Optional. Availability zones.
    service_level: str = None,                          # Optional. Service level.
    subscription_id: str = None,                        # Optional. Azure subscription ID.
    print_output: bool = False                          # Optional. Print log messages to console.
) -> Dict[str, Any]:
```

#### Return Values
```python
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': Data protection volume object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types:
```python
ValueError            # If required parameters are missing or invalid
ResourceExistsError   # If the volume already exists
Exception            # If there is an error during volume creation
```

#### Example Usage

Create a data protection volume for replication:

```python
from netapp_dataops.traditional import anf

# Create data protection volume in disaster recovery region
dp_volume = anf.create_data_protection_volume(
    resource_group_name="dr-westus-rg",
    account_name="dr-netapp-account",
    pool_name="dr-capacity-pool",
    volume_name="production-data-replica",
    location="westus",
    creation_token="prod-data-dr-path",
    virtual_network_name="dr-vnet",
    subnet_name="netapp-dr-subnet",
    source_volume_id="/subscriptions/.../volumes/production-data-volume",
    usage_threshold=536870912000,  # 500 GiB
    service_level="Standard",  # Can use lower service level for DR
    print_output=True
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": {
    "id": "/subscriptions/.../volumes/production-data-replica",
    "name": "production-data-replica",
    "location": "westus",
    "volume_type": "DataProtection",
    "provisioning_state": "Succeeded",
    "creation_token": "prod-data-dr-path",
    "service_level": "Standard",
    "usage_threshold": 536870912000,
    "data_protection": {
      "replication": {
        "endpoint_type": "dst",
        "remote_volume_resource_id": "/subscriptions/.../volumes/production-data-volume"
      }
    }
  }
}
```

<a name="reference-links"></a>

## Reference Links

| Resource | Description |
|----------|-------------|
| 📚 [Azure NetApp Files REST API Documentation](https://docs.microsoft.com/en-us/rest/api/netapp/) | Official Azure NetApp Files API reference |
| 🐍 [Azure NetApp Files Python SDK](https://docs.microsoft.com/en-us/python/api/azure-mgmt-netapp/) | Azure NetApp Files management client library |
| 🔧 [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/) | Command-line tools for Azure |
| 🏗️ [Azure NetApp Files Architecture](https://docs.microsoft.com/en-us/azure/azure-netapp-files/azure-netapp-files-solution-architectures) | Solution architectures and best practices |
| 🔐 [Azure Identity Documentation](https://docs.microsoft.com/en-us/python/api/azure-identity/) | Azure authentication methods |

---

<a name="support"></a>

### Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.

**Common Issues:**
- **Authentication failures**: Ensure Azure CLI is logged in or service principal credentials are correct
- **Permission denied**: Verify NetApp Contributor role is assigned to your account/service principal
- **Resource not found**: Check that NetApp Account, Capacity Pool, and delegated subnet exist
- **Region limitations**: Verify Azure NetApp Files is available in your target region
