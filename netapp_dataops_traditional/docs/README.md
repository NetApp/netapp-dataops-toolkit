# Google Cloud NetApp Volumes (GCNV) Integration for Traditional DataOps Toolkit

## Overview

The [`gcnv.py`](https://bitbucket.ngage.netapp.com/projects/SIE-BB/repos/netapp-dataops-toolkit/browse/netapp_dataops_traditional/netapp_dataops/traditional/gcnv.py?at=refs%2Fheads%2Ffeature%2Fgcnv-traditional) module extends the Traditional DataOps Toolkit to support Google Cloud NetApp Volumes (GCNV). Previously, the toolkit only supported ONTAP storage systems. With this addition, users can now manage NetApp volumes hosted in Google Cloud, leveraging Google’s managed NetApp service.

## Setup

### 1. Prerequisites
   - Python >= 3.7
   - [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
   - NetApp API enabled on GCP project

### 2. Installation

Install the Google Cloud NetApp SDK:

   ```bash
   python3 -m pip install google-cloud-netapp
   ```

### 3. Authentication:
   - Ensure your environment is authenticated to Google Cloud (e.g., via `gcloud auth application-default login` or service account credentials).

## Features

### 1. **Volume Management**
- **Creation:** Users can provision new NetApp volumes in Google Cloud, specifying parameters such as size, protocols (NFS, SMB), storage pools, and access policies.
- **Cloning:** The module supports creating a new volume as a clone of an existing volume, using a specific snapshot as the source. This is useful for rapid environment duplication or testing.
- **Listing:** Users can retrieve a list of all volumes in a given project and location.
- **Deletion:** Volumes can be deleted, with options for forced deletion if necessary.

### 2. **Snapshot Management**
- **Creation:** Snapshots capture the state of a volume at a point in time, enabling backup and recovery scenarios.
- **Listing:** Users can enumerate all snapshots associated with a particular volume.
- **Deletion:** Snapshots can be removed when no longer needed.

### 3. **Replication Management**
- **Setup:** Replication allows data to be mirrored between volumes, supporting disaster recovery and high availability. The module enables configuration of replication schedules and destination parameters.

### 4. **Advanced Configuration**
- **Export Policies:** Define which clients can access a volume and with what permissions.
- **SMB Settings:** Configure SMB protocol options for Windows-based access.
- **Snapshot Policies:** Automate snapshot creation on schedules (hourly, daily, weekly).
- **Backup Configuration:** Integrate with backup vaults and policies for data protection.
- **Tiering:** Manage storage tiering and cooling periods to optimize cost and performance.
- **Security & Permissions:** Set security styles (NTFS, UNIX), enable Kerberos, and configure Unix permissions.

## How It Works

- The module interacts with Google Cloud NetApp Volumes using Google’s official Python SDK.
- Each function corresponds to a specific management operation (e.g., create, clone, delete, list).
- Required parameters ensure correct identification of resources (project, location, volume ID).
- Optional parameters allow for fine-grained control over configuration and behavior.
- Operations are asynchronous, meaning requests may take time to complete and typically return an operation result indicating success or failure.

## Usage Scenarios

- **DevOps Automation:** Integrate GCNV management into CI/CD pipelines for dynamic environment provisioning.
- **Data Protection:** Schedule snapshots and backups for compliance and disaster recovery.
- **Migration:** Clone volumes and set up replications to migrate workloads between environments.
- **Access Control:** Use export policies and SMB settings to enforce security and access requirements.

## References

- [GCNV REST API documentation](https://cloud.google.com/netapp/volumes/docs/reference/rest)
- [GCNV Python SDK documentation](https://cloud.google.com/python/docs/reference/netapp/latest)
- [User guides and sample scripts](https://cloud.google.com/netapp/volumes/docs/discover/overview)


## Support

- Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.