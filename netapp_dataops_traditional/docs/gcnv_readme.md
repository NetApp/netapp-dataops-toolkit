# NetApp DataOps Toolkit – GCNV Module

The **GCNV module** extends the NetApp DataOps Toolkit – Traditional with support for **Google Cloud NetApp Volumes (GCNV)**.

This module provides simple Python APIs to:
- 🚀 Provision and manage NetApp volumes in Google Cloud
- 📸 Create and restore snapshots for data protection
- 🔄 Clone volumes for rapid environment duplication
- 🔗 Manage replication relationships for disaster recovery

Built on the [Google Cloud NetApp Python SDK](https://cloud.google.com/python/docs/reference/netapp/latest).


## Table of Contents

- [Overview](#overview)
  - [Key Capabilities](#key-capabilities)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installation Instructions](#installation-instructions)
- [Authentication](#authentication)
  - [Option 1: Application Default Credentials (Recommended)](#option-1-application-default-credentials-recommended)
  - [Option 2: Service Account JSON](#option-2-service-account-json)
- [Available Functions](#available-functions)
  - [Function Categories](#function-categories)
- [API Reference](#api-reference)
- [1. Volume Management](#1-volume-management)
  - [🚀 Create a New Data Volume](#-create-a-new-data-volume)
  - [🔄 Clone an Existing Data Volume](#-clone-an-existing-data-volume)
  - [🗑️ Delete an Existing Data Volume](#️-delete-an-existing-data-volume)
  - [📋 List All Data Volumes](#-list-all-data-volumes)
- [2. Snapshot Management](#2-snapshot-management)
  - [📸 Create a New Snapshot for a Data Volume](#-create-a-new-snapshot-for-a-data-volume)
  - [🗑️ Delete an Existing Snapshot for a Data Volume](#️-delete-an-existing-snapshot-for-a-data-volume)
  - [📋 List All Snapshots for a Data Volume](#-list-all-snapshots-for-a-data-volume)
- [3. Replication Management](#3-replication-management)
  - [🔗 Create a Replication of a Data Volume](#-create-a-replication-of-a-data-volume)
- [Reference Links](#reference-links)
- [Support](#support)

## Overview

This module simplifies programmatic interaction with Google Cloud NetApp Volumes, designed for:
- 🤖 **Automation pipelines**
- 🧠 **ML workflows**
- 🔄 **CI/CD systems**

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Volume Management** | Provision, clone, and delete NetApp volumes |
| **Snapshot Operations** | Create point-in-time snapshots for data protection |
| **Volume Cloning** | Rapidly duplicate environments from snapshots |
| **Replication** | Set up cross-region disaster recovery |

## Installation

### Prerequisites

Before getting started, ensure you have:

| Requirement | Details |
|-------------|---------|
| **Python** | Version ≥3.9, <3.13 |
| **Google Cloud SDK** | [Install and authenticate](https://cloud.google.com/sdk/docs/install) |
| **NetApp API** | Enabled in your GCP project |
| **IAM Permissions** | NetApp Volume Admin role |

### Installation Instructions

Install the toolkit with pip:

```bash
python3 -m pip install netapp-dataops-traditional
```

## Authentication

Choose one of the following authentication methods:

### Option 1: Application Default Credentials (Recommended)

```bash
# Authenticate with your Google account
gcloud auth application-default login

# Set your default project
gcloud config set project YOUR_PROJECT_ID

# Enable the NetApp API
gcloud services enable netapp.googleapis.com
```

### Option 2: Service Account JSON

```bash
# Set the path to your service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
```

> **💡 Tip:** For production environments, use Option 2 with a dedicated service account.
 
## Available Functions

Import the GCNV module functions into your Python project:

```python
from netapp_dataops.traditional.gcnv import (
    create_volume,
    clone_volume,
    delete_volume,
    list_volumes,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    create_replication
)
```

> **📝 Note:** All prerequisite authentication steps must be completed before using these functions.

### Function Categories

1. [Volume Management](#1-volume-management)
    - [Create a New Data Volume](#-create-a-new-data-volume)
    - [Clone an Existing Data Volume](#-clone-an-existing-data-volume)
    - [Delete an Existing Data Volume](#️-delete-an-existing-data-volume)
    - [List All Data Volumes](#-list-all-data-volumes)
2. [Snapshot Management](#2-snapshot-management)
    - [Create a New Snapshot for a Data Volume](#-create-a-new-snapshot-for-a-data-volume)
    - [Delete an Existing Snapshot for a Data Volume](#️-delete-an-existing-snapshot-for-a-data-volume)
    - [List All Snapshots for a Data Volume](#-list-all-snapshots-for-a-data-volume)
3. [Replication Management](#3-replication-management)
    - [Create a Replication of a Data Volume](#-create-a-replication-of-a-data-volume)

## API Reference

## 1. Volume Management

### 🚀 Create a New Data Volume

Provision new NetApp volumes with customizable parameters including size, protocols (NFS/SMB), storage pools, and access policies.

#### Function Definition
```python
def create_volume(
    project_id: str,                        # Required. The ID of the project.
    location: str,                          # Required. The location for the volume.
    volume_id: str,                         # Required. The ID for the new volume.
    share_name: str,                        # Required. Share name of the volume.
    storage_pool: str,                      # Required. StoragePool name of the volume.
    capacity_gib: int,                      # Required. The capacity of the volume in GiB.
    protocols: list,                        # Required. List of protocols to enable on the volume. Allowed values within list: NFSV3, NFSV4, SMB.
    export_policy_rules: list = None,       # Export policy rules for the volume to construct google.cloud.netapp_v1.types.ExportPolicy.
    smb_settings: list = None,              # SMB share settings for the volume.
    unix_permissions: str = None,           # Default unix style permission (e.g.777) the mount point will be created with. Applicable for NFS protocol types only.
    labels: dict = None,                    # Labels as key value pairs.
    description: str = None,                # Description of the volume.
    snapshot_policy: dict = None,           # Snapshot policy for the volume. If enabled, make snapshots automatically according to the schedules.
    snap_reserve: float = None,             # Snap_reserve specifies percentage of volume storage reserved for snapshot storage.
    snapshot_directory: bool = None,        # Snapshot_directory if enabled (true) the volume will contain a read-only .snapshot directory which provides access to each of the volume's snapshots.
    security_style: str = None,             # Security style of the volume. Allowed values: NTFS, UNIX.
    kerberos_enabled: bool = None,          # Flag indicating if the volume is a kerberos volume or not, export policy rules control kerberos security modes (krb5, krb5i, krb5p).
    backup_policies: list = None,           # Backup policies for the volume. When specified, schedule backups will be created based on the policy configuration.
    backup_vault: str = None,               # Name of backup vault.
    scheduled_backup_enabled: bool = None,  # When set to true, scheduled backup is enabled on the volume. This field should be nil when there's no backup policy attached.
    block_deletion_when_clients_connected: bool = None, # Block deletion when clients are connected.
    large_capacity: bool = None,            # Flag indicating if the volume will be a large capacity volume or a regular volume. If set to True, the volume will be a large capacity volume.
    multiple_endpoints: bool = None,        # Flag indicating if the volume will have an IP address per node for volumes supporting multiple IP endpoints. Only the volume with large_capacity will be allowed to have multiple endpoints.
    tiering_enabled: bool = None,           # Flag indicating if the volume has tiering policy enable/pause.
    cooling_threshold_days: int = None      # Time in days to mark the volume's data block as cold and make it eligible for tiering. It can be range from 2-183.
):
```

#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': API response object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError      # If required parameters are missing.
Exception       # If there is an error while creating the NetApp client.
Exception       # If there is an error during the volume creation process.
```

#### Example Usage

Create a new NetApp volume with NFS protocol support:

```python
from netapp_dataops.traditional import gcnv

# Create a 100 GiB NFS volume
response = gcnv.create_volume(
    project_id="my-gcp-project",
    location="us-central1",
    volume_id="demo-volume",
    share_name="demo-share",
    storage_pool="my-storage-pool",
    capacity_gib=100,
    protocols=["NFSV3"],
    export_policy_rules=[{
        "allowed_clients": "10.0.0.0/24",
        "access_type": "READ_WRITE",
        "has_root_access": True,
        "nfsv3": True,
        "nfsv4": False
    }],
    description="Demo volume for testing"
)
```

**Expected Output:**
```json
{
  "status": "success",
  "details": "projects/my-gcp-project/locations/us-central1/volumes/demo-volume"
}
```

### 🔄 Clone an Existing Data Volume

The module supports creating a new volume as a clone of an existing volume, using a specific snapshot as the source. This is useful for rapid environment duplication or testing.

#### Function Definition

```python
def clone_volume(
    project_id: str,                        # Required. The ID of the project.
    location: str,                          # Required. The location for the volume.
    volume_id: str,                         # Required. The ID for the new volume
    source_volume: str,                     # Required. The ID of the source volume to clone from.
    source_snapshot: str,                   # Required. The snapshot to clone from.
    share_name: str,                        # Required. Share name of the volume.
    storage_pool: str,                      # Required. StoragePool name of the volume.
    protocols: list,                        # Required. List of protocols to enable on the volume. Allowed values within list: NFSV3, NFSV4, SMB.
    export_policy_rules: list = None,       # Export policy rules for the volume to construct google.cloud.netapp_v1.types.ExportPolicy.
    smb_settings: list = None,              # SMB share settings for the volume.
    unix_permissions: str = None,           # Default unix style permission (e.g.777) the mount point will be created with. Applicable for NFS protocol types only.
    labels: dict = None,                    # Labels as key value pairs.
    description: str = None,                # Description of the volume.
    snapshot_policy: dict = None,           # Snapshot policy for the volume. If enabled, make snapshots automatically according to the schedules.
    snap_reserve: float = None,             # Snap_reserve specifies percentage of volume storage reserved for snapshot storage.
    snapshot_directory: bool = None,        # Snapshot_directory if enabled (true) the volume will contain a read-only .snapshot directory which provides access to each of the volume's snapshots.
    security_style: str = None,             # Security style of the volume. Allowed values: NTFS, UNIX.
    kerberos_enabled: bool = None,          # Flag indicating if the volume is a kerberos volume or not, export policy rules control kerberos security modes (krb5, krb5i, krb5p).
    backup_policies: list = None,           # Backup policies for the volume. When specified, schedule backups will be created based on the policy configuration.
    backup_vault: str = None,               # Name of backup vault.
    scheduled_backup_enabled: bool = None,  # When set to true, scheduled backup is enabled on the volume. This field should be nil when there's no backup policy attached.
    block_deletion_when_clients_connected: bool = None, # Block deletion when clients are connected.
    large_capacity: bool = None,            # Flag indicating if the volume will be a large capacity volume or a regular volume. If set to True, the volume will be a large capacity volume.
    multiple_endpoints: bool = None,        # Flag indicating if the volume will have an IP address per node for volumes supporting multiple IP endpoints. Only the volume with large_capacity will be allowed to have multiple endpoints.
    tiering_enabled: bool = None,           # Flag indicating if the volume has tiering policy enable/pause.
    cooling_threshold_days: int = None      # Time in days to mark the volume's data block as cold and make it eligible for tiering. It can be range from 2-183.
):
```

#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': API response object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError      # If required parameters are missing.
Exception       # If there is an error while creating the NetApp client.
Exception       # If there is an error while fetching the source volume.
Exception       # If there is an error during the cloning process.
```

#### Example Usage

Create a clone from an existing snapshot:

```python
from netapp_dataops.traditional import gcnv

# Clone volume from snapshot
clone_result = gcnv.clone_volume(
    project_id="my-gcp-project",
    location="us-central1",
    volume_id="demo-volume-clone",
    source_volume="demo-volume",
    source_snapshot="snapshot-001",
    share_name="clone-share",
    storage_pool="my-storage-pool",
    protocols=["NFSV3"],
    description="Cloned volume for development"
)
```

### 🗑️ Delete an Existing Data Volume

Volumes can be deleted, with options for forced deletion if necessary.

#### Function Definition
```python
def delete_volume(
        project_id: str,          # Required. The ID of the project.
        location: str,            # Required. The location of the volume.
        volume_id: str,           # Required. The ID of the volume to delete.
        force: bool = False):     # If set to True, the volume will be deleted even if it is not empty.
```
#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': API response object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError        # If required parameters are missing.
Exception         # If there is an error while creating the NetApp client.
Exception         # If there is an error during the volume deletion process.
```

#### Example Usage
Remove a volume (with force option):

```python
from netapp_dataops.traditional import gcnv

# Delete volume
delete_result = gcnv.delete_volume(
    project_id="my-gcp-project",
    location="us-central1",
    volume_id="demo-volume",
    force=True
)
```


### 📋 List All Data volumes

Retrieve all volumes in a project/location.

#### Function Definition
```python
from netapp_dataops.traditional import gcnv
        project_id: str,          # Required. The ID of the project.
        location: str):           # Required. The location to list volumes from.
```
#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': List of volumes (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError        # If required parameters are missing.
Exception         # If there is an error while creating the NetApp client.
Exception         # If there is an error during the volume listing process.
```

#### Example Usage

Get all volumes in a project/region:

```python
from netapp_dataops.traditional import gcnv

# List all volumes
volumes = gcnv.list_volumes(
    project_id="my-gcp-project",
    location="us-central1"
)
```

## 2. Snapshot Management
### 📸 Create a New Snapshot for a Data Volume

Snapshots capture the state of a volume at a point in time, enabling backup and recovery scenarios.

#### Function Definition
```python
def create_snapshot(
    project_id: str,            # Required. The ID of the project.
    location: str,              # Required. The location to list volumes from.
    volume_id: str,             # Required. The ID of the volume to delete.
    snapshot_id: str,           # Required. The ID of the snapshot to create.
    description: str = None,    # The description of the snapshot.
    labels: dict = None         # The labels to assign to the snapshot.
):
```
#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': API response object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError        # If required parameters are missing.
Exception         # If there is an error while creating the NetApp client.
Exception         # If there is an error during the snapshot creation process.
```

#### Example Usage
Create a point-in-time snapshot:

```python
from netapp_dataops.traditional import gcnv

# Create snapshot
snapshot_result = gcnv.create_snapshot(
    project_id="my-gcp-project",
    location="us-central1",
    volume_id="demo-volume",
    snapshot_id="daily-backup-001",
    description="Daily backup snapshot",
    labels={"backup_type": "daily", "environment": "production"}
)
```

### 🗑️ Delete an Existing Snapshot for a Data Volume

Snapshots can be removed when no longer needed.

#### Function Definition
```python
def delete_snapshot(
    project_id: str,          # Required. The ID of the project.
    location: str,            # Required. The location of the volume.
    volume_id: str,           # Required. The ID of the volume.
    snapshot_id: str          # Required. The ID of the snapshot to delete.
):
```

#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': API response object (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError        # If required parameters are missing.
Exception         # If there is an error while creating the NetApp client.
Exception         # If there is an error during the snapshot deletion process.
```

#### Example Usage

Remove an unnecessary snapshot:

```python
from netapp_dataops.traditional import gcnv

# Delete snapshot
delete_snap = gcnv.delete_snapshot(
    project_id="my-gcp-project",
    location="us-central1",
    volume_id="demo-volume",
    snapshot_id="daily-backup-001"
)
```

### 📋 List All Snapshots for a Data Volume

Users can enumerate all snapshots associated with a particular volume.

#### Function Definition
```python
def list_snapshots(
    project_id: str,        # Required. The ID of the project.
    location: str,          # Required. The location to list volumes from.
    volume_id: str          # Required. The ID of the volume to list snapshots for.
):
```

#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': List of snapshots (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError        # If required parameters are missing.
Exception         # If there is an error while creating the NetApp client.
Exception         # If there is an error during the snapshot listing process.
```

#### Example Usage
Get all snapshots for a volume:

```python
from netapp_dataops.traditional import gcnv

# List snapshots
snapshots = gcnv.list_snapshots(
    project_id="my-gcp-project",
    location="us-central1",
    volume_id="demo-volume"
)
```

## 3. Replication Management

### 🔗 Create a Replication of a Data Volume

Set up cross-region replication for disaster recovery and high availability.

#### Function Definition
```python
def create_replication(
    source_project_id: str,                           # Required. The ID of the source project.
    source_location: str,                             # Required. The location of the source volume.
    source_volume_id: str,                            # Required. The ID of the source volume to replicate.
    replication_id: str,                              # Required. The ID for the new replication.
    replication_schedule: str,                        # Required. Indicates the schedule for replication.
    destination_storage_pool: str,                    # Required. The storage pool for the destination volume.
    destination_volume_id: str = None,                # Desired destination volume resource id. If not specified, source volume's resource id will be used. 
    destination_share_name: str = None,               # Destination volume's share name. If not specified, source volume's share name will be used.
    destination_volume_description: str = None,       # Description for the destination volume.
    tiering_enabled: bool = None,                     # Whether tiering is enabled on the destination volume.
    cooling_threshold_days: int = None,               # Time in days to mark the volume's data block as cold and make it eligible for tiering. It can be range from 2-183.
    description: str = None,                          # A description about this replication relationship.
    labels: dict = None                               # Resource labels to represent user provided metadata
):
```

#### Return Values
```
dict: Dictionary with keys
  - 'status': 'success' or 'error'
  - 'details': List of snapshots (if successful)
  - 'message': Error message (if failed)
```

#### Error Handling

If an error is encountered, the function will raise an exception of one of the following types.
```
ValueError        # If required parameters are missing.
Exception         # If there is an error while creating the NetApp client.
Exception         # If there is an error during the replication creation process.
```

 
#### Example Usage
Set up cross-region replication for disaster recovery:

```python
from netapp_dataops.traditional import gcnv

# Create replication
replication_result = gcnv.create_replication(
    source_project_id="my-gcp-project",
    source_location="us-central1",
    source_volume_id="demo-volume",
    replication_id="dr-replication-001",
    replication_schedule="HOURLY",
    destination_storage_pool="dr-storage-pool",
    destination_volume_id="demo-volume-replica",
    destination_share_name="replica-share",
    description="Disaster recovery replication",
    labels={"purpose": "disaster_recovery", "schedule": "hourly"}
)

print(f"✅ Replication created: {replication_result['status']}")
```
 
## Reference Links

| Resource | Description |
|----------|-------------|
| 📚 [GCNV REST API Documentation](https://cloud.google.com/netapp/volumes/docs/reference/rest) | Official Google Cloud NetApp Volumes API reference |
| 🐍 [GCNV Python SDK](https://cloud.google.com/python/docs/reference/netapp/latest) | Google Cloud NetApp Python client library |
| 🧰 [NetApp DataOps Toolkit](https://github.com/NetApp/netapp-dataops-toolkit) | Main project repository on GitHub |
| ☁️ [Google Cloud Console](https://console.cloud.google.com/netapp) | Web interface for managing GCNV resources |
| 🔧 [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) | Command-line tools for Google Cloud |

---

### Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
