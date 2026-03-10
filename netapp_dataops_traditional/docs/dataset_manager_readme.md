# NetApp DataOps Toolkit - Dataset Manager

## Table of Contents

- [Introduction](#introduction)
- [What is Dataset Manager?](#what-is-dataset-manager)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Getting Started](#getting-started)
  - [Initial Configuration](#initial-configuration)
  - [Creating Your First Dataset](#creating-your-first-dataset)
- [Working with Datasets](#working-with-datasets)
  - [Creating a New Dataset](#creating-a-new-dataset)
  - [Accessing an Existing Dataset](#accessing-an-existing-dataset)
  - [Listing All Datasets](#listing-all-datasets)
  - [Managing Files](#managing-files)
  - [Creating Snapshots](#creating-snapshots)
  - [Cloning Datasets](#cloning-datasets)
  - [Deleting Datasets](#deleting-datasets)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## Introduction

The Dataset Manager is a powerful feature of the NetApp DataOps Toolkit that provides a simplified, intuitive interface for managing datasets backed by NetApp ONTAP storage. It abstracts away the complexities of ONTAP volume management and presents data scientists, data engineers, and developers with a familiar, filesystem-based approach to working with large datasets.

## What is Dataset Manager?

Dataset Manager transforms ONTAP volumes into easy-to-use "datasets" that appear as simple directories on your local filesystem. Each dataset is actually an ONTAP volume with all the enterprise-grade capabilities of NetApp storage—including instant cloning, snapshots, and space efficiency—but accessed through a familiar directory structure.

**Traditional approach (without Dataset Manager):**
```python
# Manually manage ONTAP volumes
from netapp_dataops.traditional import create_volume, clone_volume, mount_volume

# Create volume
create_volume(volume_name="my_data", volume_size="500GB", junction="/my_data")

# Mount it
mount_volume(volume_name="my_data", mountpoint="/mnt/my_data")

# Work with data...
# Later: unmount, manage snapshots separately, etc.
```

**Dataset Manager approach:**
```python
# Simple, intuitive dataset operations
from netapp_dataops.traditional.datasets import Dataset

# Create dataset - automatically creates volume and makes it accessible
dataset = Dataset(name="my_data", max_size="500GB")

# Access files immediately through a simple path
print(f"Dataset location: {dataset.local_file_path}")

# Work with data using standard Python file operations
with open(f"{dataset.local_file_path}/experiment1.csv", "w") as f:
    f.write("data,label\n1,a\n2,b")
```

## Key Features

### 🎯 **Simplified Access**
- **No manual mounting required**: Datasets are immediately accessible through a pre-mounted root volume
- **Standard file operations**: Use Python's built-in file I/O, pandas, or any other tools
- **Automatic namespace management**: New datasets appear instantly in your local filesystem

### ⚡ **Near-Instantaneous Operations**
- **Space-efficient clones**: Create full copies in seconds that share data with the source
- **Instant snapshots**: Capture point-in-time copies with zero performance impact
- **Zero data movement**: Clones and snapshots leverage NetApp's FlexClone technology

### 🔬 **ML/Data Science Friendly**
- **Experiment tracking**: Snapshot datasets before and after training runs
- **Model versioning**: Clone datasets to preserve data states for specific model versions
- **Reproducibility**: Restore exact data states from snapshots
- **Collaboration**: Share datasets instantly through clones

### 🏢 **Enterprise-Grade Storage**
- **Powered by NetApp ONTAP**: Benefit from enterprise reliability, performance, and efficiency
- **NFS-based**: Works with Linux and macOS hosts
- **Scalable**: Manage datasets from gigabytes to petabytes
- **Data protection**: Built-in snapshot and replication capabilities

## Architecture Overview

Dataset Manager uses a hierarchical structure with a single "root volume" that serves as the parent for all datasets:

```
Root Volume (e.g., "dataset_mgr_root")
    └── Mounted at: /mnt/datasets (or your chosen location)
        ├── training_data_v1/          ← Dataset 1 (ONTAP volume)
        │   ├── images/
        │   └── labels.csv
        ├── training_data_v2/          ← Dataset 2 (ONTAP volume)
        │   ├── images/
        │   └── labels.csv
        └── inference_data/            ← Dataset 3 (ONTAP volume)
            └── input_data.parquet
```

**How it works:**
1. **Root Volume**: A single ONTAP volume mounted permanently on your local system
2. **Datasets as Volumes**: Each dataset is a separate ONTAP volume, automatically junctioned under the root volume
3. **Transparent Access**: The NFS client sees one continuous directory tree
4. **Automatic Discovery**: New datasets appear immediately without manual mounting

**Technical Details:**
- Uses ONTAP junction paths to create the hierarchy: `/<root_volume>/<dataset_name>`
- Inherits export policy from root volume for consistent NFS access permissions
- Supports all ONTAP volume features: snapshots, clones, efficiency features
- Compatible with FlexVol and FlexGroup volumes

## Prerequisites

### System Requirements

**Operating Systems:**
- Linux (RHEL, CentOS, Ubuntu, Debian, etc.)
- macOS

**Storage System:**
- NetApp AFF, FAS, or ONTAP Select (ONTAP 9.7+)
- NetApp Cloud Volumes ONTAP (ONTAP 9.7+)
- Amazon FSx for NetApp ONTAP

**Python:**
- Python 3.8–3.13
- `pip` (usually bundled with Python; verify with `pip --version`)

**Required Utilities:**
- `mount` (for checking mount status)
- `mountpoint` (for validating mount points)
- On Linux: `nfs-common` (Debian/Ubuntu) or `nfs-utils` (RHEL/CentOS)

### Permissions

**ONTAP Permissions:**
Your ONTAP user account needs permissions to:
- Create and delete volumes
- Create and delete snapshots
- Clone volumes
- Modify junction paths

**Local System Permissions:**
- `root` or `sudo` access for:
  - Adding entries to `/etc/fstab` (during setup)
  - Initial mounting operations (if not using fstab)
- Read/write access to the root volume mountpoint

### Network Requirements

- Network connectivity from your host to the ONTAP data LIF
- NFS protocol enabled on the ONTAP SVM
- Appropriate export policy rules for your host's IP address

## Installation

### Step 1: Install NFS Client Utilities (if not already installed)

Dataset Manager mounts ONTAP volumes via NFS, so the NFS client utilities must be installed on your system.

**Ubuntu / Debian:**
```bash
sudo apt-get update && sudo apt-get install -y nfs-common
```

**RHEL / CentOS / Fedora:**
```bash
sudo dnf install -y nfs-utils
```

**macOS:**

NFS client support is built in to macOS — no additional installation is required.

### Step 2: Install the Package

It is recommended to install the toolkit inside a Python virtual environment to keep dependencies isolated.

**Create and activate a virtual environment:**
```bash
python3 -m venv ~/netapp-dataops-venv
source ~/netapp-dataops-venv/bin/activate
```

**Install the toolkit:**
```bash
pip install netapp-dataops-traditional
```

This installs the package with support for NetApp ONTAP (AFF, FAS, Cloud Volumes ONTAP, Amazon FSx for NetApp ONTAP, and ONTAP Select).

> **Tip:** Add `source ~/netapp-dataops-venv/bin/activate` to your shell's startup file (e.g., `~/.bashrc` or `~/.zshrc`) so the environment is activated automatically in new terminal sessions.

### Step 3: Verify Installation

Confirm that the toolkit was installed correctly:

```bash
netapp_dataops_cli.py --help
```

You should see the toolkit's help output. If the command is not found, ensure the virtual environment is activated and that its `bin` directory is on your `PATH`.

You can also verify the Python library is importable:

```python
from netapp_dataops.traditional.datasets import Dataset
print("Installation successful!")
```

> **Note:** Python 3.8–3.13 is required.

---

## Getting Started

### Initial Configuration

Dataset Manager is configured as part of the NetApp DataOps Toolkit setup process. If you haven't configured the toolkit yet, run:

```bash
netapp_dataops_cli.py config
```

During configuration, you'll be asked about Dataset Manager setup. You have two options:

#### Option 1: Create a New Root Volume (Recommended for new setups)

If you don't have an existing root volume, the toolkit can create one for you:

```
=== Dataset Manager Configuration ===
Do you have a pre-existing Dataset Manager 'root' volume? (yes/no) [no]: no

Would you like to create a new Dataset Manager 'root' volume now? (yes/no) [yes]: yes

Enter desired Dataset Manager "root" volume name [dataset_mgr_root]: dataset_mgr_root

Enter desired local mountpoint for Dataset Manager "root" volume: /mnt/datasets

Creating Dataset Manager root volume 'dataset_mgr_root'...
Root volume 'dataset_mgr_root' created successfully

Would you like to add your Dataset Manager "root" volume to /etc/fstab now? (yes/no) [yes]: yes

Elevated privileges required to modify /etc/fstab...
[sudo] password for user:
Successfully added entry to /etc/fstab
```

**What happens:**
1. A small (1GB) ONTAP volume is created named `dataset_mgr_root`
2. The volume is junctioned at `/dataset_mgr_root`
3. An entry is added to `/etc/fstab` for automatic mounting on reboot
4. The volume is mounted at your specified mountpoint

#### Option 2: Use an Existing Root Volume

If you already have a root volume created:

```
=== Dataset Manager Configuration ===
Do you have a pre-existing Dataset Manager 'root' volume? (yes/no) [no]: yes

Enter Dataset Manager "root" volume name (or 'abort' to cancel): my_existing_root

Enter desired local mountpoint for Dataset Manager "root" volume: /mnt/datasets

Would you like to add your Dataset Manager "root" volume to /etc/fstab now? (yes/no) [yes]: yes
```

**Requirements for existing volumes:**
- Volume must exist in ONTAP
- Junction path should be `/<volume_name>` (e.g., `/my_existing_root`)
- Volume should have an appropriate export policy for your host

### Verifying Your Setup

After configuration, verify that Dataset Manager is ready:

```python
from netapp_dataops.traditional.datasets import Dataset, get_datasets

# This should work without errors if configuration is correct
datasets = get_datasets()
print(f"Dataset Manager is configured. Found {len(datasets)} existing datasets.")
```

You can also check that the root volume is mounted:

```bash
# Check mount status
mount | grep dataset_mgr_root

# Check directory exists and is accessible
ls -la /mnt/datasets
```

### Creating Your First Dataset

Once configured, creating a dataset is simple:

```python
from netapp_dataops.traditional.datasets import Dataset

# Create a new dataset with 100GB maximum size
my_dataset = Dataset(name="my_first_dataset", max_size="100GB")

print(f"Dataset created!")
print(f"Location: {my_dataset.local_file_path}")
print(f"Size: {my_dataset.max_size}")

# Start working with your data immediately
import pandas as pd

# Create a sample CSV file
df = pd.DataFrame({
    'feature1': [1, 2, 3],
    'feature2': [4, 5, 6],
    'label': ['a', 'b', 'c']
})

# Save to your dataset
df.to_csv(f"{my_dataset.local_file_path}/training_data.csv", index=False)

print(f"Data saved to dataset!")
```

**What just happened:**
1. An ONTAP volume named `my_first_dataset` was created with 100GB capacity
2. The volume was automatically junctioned at `/dataset_mgr_root/my_first_dataset`
3. The dataset is immediately accessible at `/mnt/datasets/my_first_dataset`
4. You can use standard file operations to work with the data

## Working with Datasets

### Creating a New Dataset

Create a new dataset by specifying a name and maximum size:

```python
from netapp_dataops.traditional.datasets import Dataset

# Create dataset - various size formats supported
dataset = Dataset(name="training_data_v1", max_size="500GB")

# Size can be specified in different units
dataset2 = Dataset(name="small_dataset", max_size="10GB")
dataset3 = Dataset(name="large_dataset", max_size="5TB")
dataset4 = Dataset(name="tiny_dataset", max_size="100MB")
```

**Size format options:**
- `GB` - Gigabytes (e.g., "100GB")
- `TB` - Terabytes (e.g., "5TB")
- `MB` - Megabytes (e.g., "500MB")
- `PB` - Petabytes (e.g., "2PB")

**Important notes:**
- Dataset names must be unique within your ONTAP system
- Names follow ONTAP volume naming conventions
- The `max_size` is the thin-provisioned maximum; actual space consumption grows as you add data
- Use `print_output=True` to see detailed operation messages:
  ```python
  dataset = Dataset(name="my_data", max_size="100GB", print_output=True)
  ```

### Accessing an Existing Dataset

To work with an existing dataset, simply create a Dataset instance without specifying `max_size`:

```python
from netapp_dataops.traditional.datasets import Dataset

# Bind to existing dataset - no max_size needed
dataset = Dataset(name="training_data_v1")

print(f"Dataset: {dataset.name}")
print(f"Size: {dataset.max_size}")
print(f"Location: {dataset.local_file_path}")
print(f"Is Clone: {dataset.is_clone}")

if dataset.is_clone:
    print(f"Source: {dataset.source_dataset_name}")
```

**Attributes available:**
- `name` - Dataset name
- `max_size` - Maximum provisioned size (e.g., "500GB")
- `local_file_path` - Full path to the dataset directory
- `is_clone` - Boolean indicating if this is a cloned dataset
- `source_dataset_name` - Original dataset name (for clones)

### Listing All Datasets

Retrieve all existing datasets with a single function call:

```python
from netapp_dataops.traditional.datasets import get_datasets

# Get all datasets
datasets = get_datasets()

print(f"Found {len(datasets)} datasets:")
for ds in datasets:
    print(f"  - {ds.name} ({ds.max_size})")
    if ds.is_clone:
        print(f"    └─ Clone of: {ds.source_dataset_name}")

# With verbose output
datasets = get_datasets(print_output=True)
```

**Example output:**
```
Found 3 datasets:
  - training_data_v1 (500GB)
  - inference_data (50GB)
  - training_data_v2 (500GB)
    └─ Clone of: training_data_v1
```

### Managing Files

Datasets appear as regular directories, so you can use standard file operations:

```python
from netapp_dataops.traditional.datasets import Dataset
import os
import shutil

dataset = Dataset(name="my_data")

# Create directories
os.makedirs(f"{dataset.local_file_path}/raw", exist_ok=True)
os.makedirs(f"{dataset.local_file_path}/processed", exist_ok=True)

# Write files
with open(f"{dataset.local_file_path}/raw/data.txt", "w") as f:
    f.write("Important data")

# Copy files
shutil.copy("local_file.csv", f"{dataset.local_file_path}/raw/")

# Use with pandas
import pandas as pd
df = pd.read_csv("source.csv")
df.to_parquet(f"{dataset.local_file_path}/processed/data.parquet")

# Use with any library
import numpy as np
np.save(f"{dataset.local_file_path}/arrays/features.npy", some_array)
```

#### Getting File Lists

Use the `get_files()` method to retrieve information about all files in a dataset:

```python
dataset = Dataset(name="my_data")

# Get list of all files with metadata
files = dataset.get_files()

print(f"Dataset contains {len(files)} files:")
for file_info in files:
    print(f"  {file_info['filename']}")
    print(f"    Path: {file_info['filepath']}")
    print(f"    Size: {file_info['size_human']}")
    print(f"    Bytes: {file_info['size']}")
```

**Example output:**
```
Dataset contains 3 files:
  training_data.csv
    Path: /mnt/datasets/my_data/training_data.csv
    Size: 245.3 MB
    Bytes: 257234567
  model_config.json
    Path: /mnt/datasets/my_data/model_config.json
    Size: 2.1 KB
    Bytes: 2148
  features.npy
    Path: /mnt/datasets/my_data/arrays/features.npy
    Size: 1.2 GB
    Bytes: 1288490188
```

**Use cases:**
- Auditing dataset contents
- Calculating total data size
- Finding specific files
- Generating reports

### Creating Snapshots

Snapshots provide point-in-time copies of your dataset. They're instant, consume minimal space initially, and are perfect for tracking dataset versions.

```python
dataset = Dataset(name="training_data")

# Create snapshot with automatic timestamp-based name
snapshot_name = dataset.snapshot()
print(f"Created snapshot: {snapshot_name}")
# Output: Created snapshot: training_data_20240212_143022

# Create snapshot with custom name
snapshot_name = dataset.snapshot(name="before_cleaning")
print(f"Created snapshot: {snapshot_name}")
# Output: Created snapshot: before_cleaning
```

#### Viewing Snapshots

List all snapshots for a dataset:

```python
dataset = Dataset(name="training_data")

# Get all snapshots
snapshots = dataset.get_snapshots()

print(f"Dataset has {len(snapshots)} snapshots:")
for snap in snapshots:
    print(f"  - {snap['name']}")
    print(f"    Created: {snap['create_time']}")
```

**Example output:**
```
Dataset has 3 snapshots:
  - before_cleaning
    Created: 2024-02-12 14:30:22
  - after_cleaning
    Created: 2024-02-12 15:45:10
  - final_version
    Created: 2024-02-12 18:20:00
```

#### Common Snapshot Workflows

**1. Before/After Snapshots:**
```python
# Before making changes
dataset.snapshot(name="before_transform")

# Make your changes
transform_data(dataset.local_file_path)

# After changes complete
dataset.snapshot(name="after_transform")
```

**2. Experiment Tracking:**
```python
# Snapshot before each training run
experiment_id = "exp_001"
dataset.snapshot(name=f"before_{experiment_id}")

# Train your model
train_model(dataset.local_file_path, experiment_id)

# Snapshot after training
dataset.snapshot(name=f"after_{experiment_id}")
```

**3. Daily/Periodic Snapshots:**
```python
from datetime import datetime

# Daily snapshot
date_str = datetime.now().strftime("%Y%m%d")
dataset.snapshot(name=f"daily_{date_str}")
```

### Cloning Datasets

Cloning creates a new dataset that's an exact copy of the source dataset. Thanks to NetApp FlexClone technology, clones:
- Are created in seconds (regardless of dataset size)
- Initially consume almost no additional storage space
- Share unchanged data blocks with the source
- Become independent as you modify data

```python
source_dataset = Dataset(name="training_data_v1")

# Create a clone
cloned_dataset = source_dataset.clone(name="training_data_v2")

print(f"Clone created: {cloned_dataset.name}")
print(f"Location: {cloned_dataset.local_file_path}")
print(f"Is Clone: {cloned_dataset.is_clone}")
print(f"Source: {cloned_dataset.source_dataset_name}")

# Modify clone without affecting source
with open(f"{cloned_dataset.local_file_path}/new_file.txt", "w") as f:
    f.write("This only exists in the clone")
```

**Common cloning scenarios:**

**1. Experimentation:**
```python
# Clone production data for testing
prod_data = Dataset(name="production_dataset")
test_data = prod_data.clone(name="test_dataset")

# Experiment freely without risk
run_experimental_pipeline(test_data.local_file_path)

# Delete test dataset when done
test_data.delete()
```

**2. Team Collaboration:**
```python
# Each team member gets their own copy
base_dataset = Dataset(name="shared_data")

alice_data = base_dataset.clone(name="alice_working_copy")
bob_data = base_dataset.clone(name="bob_working_copy")

# Each person can work independently
```

**3. Model Training Variants:**
```python
# Create clones for different preprocessing approaches
raw_data = Dataset(name="raw_training_data")

# Clone for each variant
normalized = raw_data.clone(name="normalized_training")
standardized = raw_data.clone(name="standardized_training")
augmented = raw_data.clone(name="augmented_training")

# Apply different transformations to each
apply_normalization(normalized.local_file_path)
apply_standardization(standardized.local_file_path)
apply_augmentation(augmented.local_file_path)
```

**4. Clone from Snapshot:**
While the Dataset API doesn't directly support cloning from a snapshot, you can use the underlying volume operations:

```python
from netapp_dataops.traditional import clone_volume

# Clone from a specific snapshot
clone_volume(
    new_volume_name="restored_data",
    source_volume_name="training_data",
    source_snapshot_name="before_cleaning",
    junction="/dataset_mgr_root/restored_data"
)

# Access as a dataset
restored = Dataset(name="restored_data")
```

### Deleting Datasets

Permanently delete datasets when they're no longer needed:

```python
dataset = Dataset(name="temporary_data")

# Delete the dataset (both clones and originals can be deleted by default)
dataset.delete()
```

**Safety features:**

By default, `delete()` allows deletion of both clones and original datasets. To restrict deletion to clones only, set `delete_non_clone=False`:

```python
# This will work (both clones and originals can be deleted by default)
clone = Dataset(name="my_clone")
clone.delete()  # ✓ Works

original = Dataset(name="my_original_data")
original.delete()  # ✓ Also works (delete_non_clone defaults to True)

# To restrict deletion to clones only:
original.delete(delete_non_clone=False)  # ✗ Will raise error if not a clone
```

**Complete cleanup example:**

```python
from netapp_dataops.traditional.datasets import Dataset, get_datasets

# Find and delete all datasets matching a pattern
all_datasets = get_datasets()

for ds in all_datasets:
    if ds.name.startswith("temp_"):
        print(f"Deleting temporary dataset: {ds.name}")
        ds.delete(delete_non_clone=True)
```

**Important warnings:**
- ⚠️ Deletion is permanent and cannot be undone
- ⚠️ All data in the dataset will be lost
- ⚠️ Snapshots of the dataset will also be deleted
- ⚠️ Ensure you have backups if data is important


## Best Practices

### 1. Naming Conventions

Use clear, descriptive names for datasets:

```python
# ✓ Good (imports omitted for brevity - use: from netapp_dataops.traditional.datasets import Dataset)
Dataset(name="customer_data_2024", max_size="1TB")
Dataset(name="training_images_v1", max_size="500GB")
Dataset(name="model_inference_cache", max_size="50GB")

# ✗ Avoid
Dataset(name="data", max_size="1TB")  # Too generic
Dataset(name="test123", max_size="1TB")  # Not descriptive
Dataset(name="my-dataset", max_size="1TB")  # Hyphens may cause issues
```

**Recommended patterns:**
- `{project}_{purpose}_{version}` - e.g., "fraud_detection_training_v3"
- `{team}_{dataset_type}` - e.g., "ml_team_feature_store"
- `{timestamp}_{description}` - e.g., "20240212_experiment_data"

### 2. Snapshot Strategy

Develop a consistent snapshotting strategy:

```python
# Assuming: from netapp_dataops.traditional.datasets import Dataset
# Before major operations
dataset.snapshot(name="before_preprocessing")
preprocess_data(dataset.local_file_path)

# After major milestones
dataset.snapshot(name="after_preprocessing")
dataset.snapshot(name="before_training")
train_model(dataset.local_file_path)
dataset.snapshot(name="after_training")

# For experiments
dataset.snapshot(name=f"exp_{experiment_id}_start")
# ... experiment ...
dataset.snapshot(name=f"exp_{experiment_id}_end")
```

### 3. Clone Management

Keep clones organized and clean up when finished:

```python
from netapp_dataops.traditional.datasets import Dataset, get_datasets

# Prefix clones with purpose
base_data = Dataset(name="production_data")
test_clone = base_data.clone(name="test_experiment_1")

# Clean up temporary clones regularly
all_datasets = get_datasets()
for ds in all_datasets:
    if ds.name.startswith("test_") and ds.is_clone:
        print(f"Cleaning up test clone: {ds.name}")
        ds.delete()  # Safe - clones can be deleted by default
```

### 4. Size Planning

Choose appropriate sizes based on your data growth:

```python
# Assuming: from netapp_dataops.traditional.datasets import Dataset
# Add headroom for growth
current_data_size = "50GB"
max_size = "200GB"  # 4x current size for growth

dataset = Dataset(name="my_data", max_size=max_size)

# For dynamic workloads, go larger
dynamic_dataset = Dataset(
    name="streaming_data",
    max_size="2TB"  # Room for accumulation
)
```

### 5. Error Handling

Implement proper error handling:

```python
from netapp_dataops.traditional.datasets import (
    Dataset,
    DatasetError,
    DatasetExistsError,
    DatasetConfigError,
    DatasetVolumeError
)

try:
    dataset = Dataset(name="my_data", max_size="100GB")
except DatasetExistsError:
    print("Dataset already exists, binding to existing...")
    dataset = Dataset(name="my_data")
except DatasetConfigError as e:
    print(f"Configuration error: {e}")
    print("Please run: netapp_dataops_cli.py config")
except DatasetVolumeError as e:
    print(f"Volume operation failed: {e}")
except DatasetError as e:
    print(f"Dataset error: {e}")
```

### 6. Monitoring Dataset Usage

Track your datasets and their usage:

```python
from netapp_dataops.traditional.datasets import get_datasets

def audit_datasets():
    """Generate a report of all datasets and their file counts."""
    datasets = get_datasets()
    
    print(f"\n{'Dataset Name':<30} {'Size':<15} {'Files':<10} {'Type':<10}")
    print("-" * 70)
    
    for ds in datasets:
        files = ds.get_files()
        total_size = sum(f['size'] for f in files)
        ds_type = "Clone" if ds.is_clone else "Original"
        
        print(f"{ds.name:<30} {ds.max_size:<15} {len(files):<10} {ds_type:<10}")

# Run regularly
audit_datasets()
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Dataset manager is not enabled"

**Error message:**
```
DatasetConfigError: Dataset manager is not enabled. Run 'netapp_dataops_cli.py config' to configure.
```

**Solution:**
```bash
# Run configuration wizard
netapp_dataops_cli.py config

# Follow prompts to enable Dataset Manager
```

---

#### Issue: Root volume not accessible

**Error message:**
```
DatasetConfigError: Root mountpoint '/mnt/datasets' is not accessible.
```

**Diagnosis:**
```bash
# Check if mountpoint exists
ls -la /mnt/datasets

# Check if it's mounted
mount | grep datasets

# Check fstab entry
cat /etc/fstab | grep dataset_mgr_root
```

**Solution:**
```bash
# If not mounted, mount it manually
sudo mount -a

# Or mount specifically
sudo mount -t nfs data_lif:/dataset_mgr_root /mnt/datasets

# Verify
df -h /mnt/datasets
```

---

#### Issue: "Junction path is already in use"

**Error message:**
```
Error: Junction path '/dataset_mgr_root/my_data' is already in use by another volume.
```

**Solution:**
Use a different dataset name or investigate the conflicting volume:

```python
from netapp_dataops.traditional import list_volumes

# List all volumes to find the conflict
volumes = list_volumes(print_output=True)

# Choose a different name
dataset = Dataset(name="my_data_v2", max_size="100GB")
```

---

#### Issue: Dataset exists but not accessible

**Error message:**
```
Volume 'my_data' already exists but is not managed by the Dataset Manager
```

**Explanation:**
The volume exists but isn't junctioned under the root volume.

**Solution:**
Either:
1. Use a different name for your dataset
2. Manually fix the existing volume's junction path in ONTAP
3. Delete the conflicting volume (if safe to do so)

```python
# Option 1: Different name
dataset = Dataset(name="my_data_new", max_size="100GB")

# Option 3: Delete conflicting volume (careful!)
from netapp_dataops.traditional import delete_volume
delete_volume(volume_name="my_data", delete_non_clone=True)
```

---

#### Issue: NFS mount is stale

**Symptoms:**
- Commands hang when accessing dataset
- "Stale file handle" errors

**Diagnosis:**
```bash
# Check mount status
mount | grep dataset_mgr_root

# Try to access
ls /mnt/datasets  # May hang
```

**Solution:**
```bash
# Force unmount (may require root)
sudo umount -f /mnt/datasets

# Remount
sudo mount -a

# Verify
ls /mnt/datasets
```

---

#### Issue: Permission denied when accessing dataset

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/mnt/datasets/my_data/file.txt'
```

**Diagnosis:**
```bash
# Check permissions
ls -la /mnt/datasets/my_data/

# Check NFS mount options
mount | grep datasets
```

**Solution:**
1. Check ONTAP export policy rules
2. Verify NFS mount options
3. Check local file permissions

```bash
# Check current user ID
id

# Verify export policy in ONTAP allows your host
# Update export policy if needed (in ONTAP CLI):
# vserver export-policy rule create -vserver svm_name -policyname default -clientmatch your_ip -rorule sys -rwrule sys -superuser sys
```

---

#### Issue: Cannot create snapshot

**Error message:**
```
DatasetVolumeError: Failed to create snapshot for dataset 'my_data'
```

**Common causes:**
1. Maximum snapshot count reached
2. Snapshot with same name already exists
3. Insufficient ONTAP permissions

**Solution:**
```python
# List existing snapshots
dataset = Dataset(name="my_data")
snapshots = dataset.get_snapshots()
print(f"Current snapshot count: {len(snapshots)}")

# Delete old snapshots if needed
from netapp_dataops.traditional.ontap import delete_snapshot
for snap in snapshots[:10]:  # Delete oldest 10
    delete_snapshot(volume_name="my_data", snapshot_name=snap['name'])

# Use unique snapshot names
from datetime import datetime
unique_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
dataset.snapshot(name=unique_name)
```

---

### Getting Help

#### Enable Verbose Output

Get detailed information about operations:

```python
# Enable output for all operations
dataset = Dataset(name="my_data", max_size="100GB", print_output=True)
dataset.snapshot(name="debug_snap")
cloned = dataset.clone(name="debug_clone")
```

#### Check Configuration

Verify your configuration file:

```python
from netapp_dataops.traditional.core import _retrieve_config

config = _retrieve_config(print_output=True)
print("Dataset Manager enabled:", config.get('datasetManagerEnabled'))
print("Root volume:", config.get('datasetManagerRootVolume'))
print("Root mountpoint:", config.get('datasetManagerRootMountpoint'))
```

#### Verify ONTAP Connectivity

Test connection to ONTAP:

```python
from netapp_dataops.traditional import list_volumes

# This will fail if ONTAP connection is broken
try:
    volumes = list_volumes(print_output=True)
    print("ONTAP connection successful")
except Exception as e:
    print(f"ONTAP connection failed: {e}")
```

## API Reference

### Dataset Class

#### Constructor

```python
Dataset(name: str, max_size: Optional[str] = None, print_output: bool = False)
```

Create or access a dataset.

**Parameters:**
- `name` (str): Dataset name (ONTAP volume name)
- `max_size` (str, optional): Maximum size for new datasets (e.g., "100GB"). Required when creating new datasets, omit when accessing existing ones.
- `print_output` (bool): Whether to print detailed operation messages. Default: False

**Returns:**
- Dataset instance

**Raises:**
- `DatasetExistsError`: Dataset name already exists (when creating new)
- `DatasetConfigError`: Dataset Manager not configured or configuration invalid
- `DatasetVolumeError`: ONTAP volume operation failed
- `DatasetError`: General dataset error

**Examples:**
```python
# Create new dataset
dataset = Dataset(name="my_data", max_size="500GB")

# Access existing dataset
dataset = Dataset(name="my_data")

# With verbose output
dataset = Dataset(name="my_data", max_size="100GB", print_output=True)
```

---

#### Attributes

```python
dataset.name              # str: Dataset name
dataset.max_size          # str: Maximum provisioned size (e.g., "500GB")
dataset.local_file_path   # str: Full path to dataset directory
dataset.is_clone          # bool: True if dataset is a clone
dataset.source_dataset_name  # str: Source dataset name (if clone), else None
```

---

#### get_files()

```python
dataset.get_files() -> List[Dict[str, Any]]
```

Get list of all files in the dataset.

**Returns:**
List of dictionaries with keys:
- `filename` (str): File name
- `filepath` (str): Full path to file
- `size` (int): File size in bytes
- `size_human` (str): Human-readable size (e.g., "1.2 GB")

**Raises:**
- `DatasetError`: Failed to list files

**Example:**
```python
files = dataset.get_files()
for f in files:
    print(f"{f['filename']}: {f['size_human']}")
```

---

#### snapshot()

```python
dataset.snapshot(name: Optional[str] = None) -> str
```

Create a snapshot of the dataset.

**Parameters:**
- `name` (str, optional): Snapshot name. If not provided, automatic timestamp-based name is used.

**Returns:**
- str: Name of created snapshot

**Raises:**
- `DatasetVolumeError`: Snapshot creation failed

**Example:**
```python
# Auto-generated name
snap_name = dataset.snapshot()
print(snap_name)  # "my_data_20240212_143022"

# Custom name
snap_name = dataset.snapshot(name="before_training")
```

---

#### get_snapshots()

```python
dataset.get_snapshots() -> List[Dict[str, Any]]
```

Get list of all snapshots for the dataset.

**Returns:**
List of dictionaries with keys:
- `name` (str): Snapshot name
- `create_time` (str): Snapshot creation timestamp

**Raises:**
- `DatasetVolumeError`: Failed to list snapshots

**Example:**
```python
snapshots = dataset.get_snapshots()
for snap in snapshots:
    print(f"{snap['name']} created at {snap['create_time']}")
```

---

#### clone()

```python
dataset.clone(name: str) -> Dataset
```

Create a space-efficient clone of the dataset.

**Parameters:**
- `name` (str): Name for the cloned dataset

**Returns:**
- Dataset: New Dataset instance representing the clone

**Raises:**
- `DatasetExistsError`: Clone name already exists
- `DatasetVolumeError`: Clone operation failed

**Example:**
```python
source = Dataset(name="training_data")
clone = source.clone(name="test_data")
print(f"Clone created at: {clone.local_file_path}")
```

---

#### delete()

```python
dataset.delete(delete_non_clone: bool = True)
```

Permanently delete the dataset.

**Parameters:**
- `delete_non_clone` (bool): If True, allows deletion of non-clone datasets. If False, only clones can be deleted. Default: True

**Raises:**
- `DatasetVolumeError`: Deletion failed

**Warning:**
Deletion is permanent and cannot be undone. All data and snapshots will be lost.

**Example:**
```python
# Delete clone (safe by default)
clone_dataset.delete()

# Delete original dataset (must explicitly allow)
original_dataset.delete(delete_non_clone=True)
```

---

### Module-Level Functions

#### get_datasets()

```python
get_datasets(print_output: bool = False) -> List[Dataset]
```

Get all existing datasets managed by Dataset Manager.

**Parameters:**
- `print_output` (bool): Whether to print detailed information. Default: False

**Returns:**
- List[Dataset]: List of all Dataset instances

**Raises:**
- `DatasetConfigError`: Dataset Manager not configured
- `DatasetVolumeError`: Failed to retrieve datasets

**Example:**
```python
from netapp_dataops.traditional.datasets import get_datasets

# Get all datasets
datasets = get_datasets()
print(f"Found {len(datasets)} datasets")

# With verbose output
datasets = get_datasets(print_output=True)
```

---

### Exceptions

#### DatasetError
Base exception for all Dataset Manager errors.

#### DatasetExistsError
Raised when attempting to create a dataset that already exists.

#### DatasetConfigError
Raised when Dataset Manager configuration is invalid or missing.

#### DatasetVolumeError
Raised when an ONTAP volume operation fails.

**Example usage:**
```python
from netapp_dataops.traditional.datasets import (
    DatasetError,
    DatasetExistsError,
    DatasetConfigError,
    DatasetVolumeError
)

try:
    dataset = Dataset(name="my_data", max_size="100GB")
except DatasetExistsError:
    print("Dataset already exists")
except DatasetConfigError:
    print("Please run: netapp_dataops_cli.py config")
except DatasetVolumeError as e:
    print(f"ONTAP operation failed: {e}")
except DatasetError as e:
    print(f"General error: {e}")
```

---

## Complete Example Workflow

Here's a complete workflow demonstrating Dataset Manager capabilities:

```python
#!/usr/bin/env python3
"""
Complete Dataset Manager workflow example.
Demonstrates dataset creation, file management, snapshots, cloning, and cleanup.
"""

from netapp_dataops.traditional.datasets import Dataset, get_datasets, DatasetError
import pandas as pd
import numpy as np

def main():
    print("=== Dataset Manager Workflow Demo ===\n")
    
    # Step 1: Create initial dataset
    print("Step 1: Creating initial dataset...")
    try:
        training_data = Dataset(
            name="ml_training_data_v1",
            max_size="200GB",
            print_output=True
        )
        print(f"✓ Dataset created at: {training_data.local_file_path}\n")
    except DatasetError as e:
        print(f"✗ Error: {e}\n")
        return
    
    # Step 2: Add some data
    print("Step 2: Adding training data...")
    df = pd.DataFrame({
        'feature1': np.random.rand(1000),
        'feature2': np.random.rand(1000),
        'label': np.random.randint(0, 2, 1000)
    })
    df.to_csv(f"{training_data.local_file_path}/training_data.csv", index=False)
    print("✓ Data added\n")
    
    # Step 3: Create snapshot before training
    print("Step 3: Creating snapshot before training...")
    snap_name = training_data.snapshot(name="before_training")
    print(f"✓ Snapshot created: {snap_name}\n")
    
    # Step 4: Simulate model training and add results
    print("Step 4: Simulating training and adding results...")
    results = pd.DataFrame({
        'epoch': range(10),
        'loss': np.random.rand(10),
        'accuracy': np.random.rand(10)
    })
    results.to_csv(f"{training_data.local_file_path}/training_results.csv", index=False)
    print("✓ Training results added\n")
    
    # Step 5: Create post-training snapshot
    print("Step 5: Creating snapshot after training...")
    snap_name = training_data.snapshot(name="after_training")
    print(f"✓ Snapshot created: {snap_name}\n")
    
    # Step 6: Clone for experimentation
    print("Step 6: Creating clone for experimentation...")
    experiment_data = training_data.clone(name="ml_experiment_v1")
    print(f"✓ Clone created at: {experiment_data.local_file_path}\n")
    
    # Step 7: Modify clone
    print("Step 7: Modifying cloned dataset...")
    with open(f"{experiment_data.local_file_path}/experiment_notes.txt", "w") as f:
        f.write("Experiment with modified hyperparameters\n")
    print("✓ Experiment data modified\n")
    
    # Step 8: List all files in datasets
    print("Step 8: Listing files in original dataset...")
    files = training_data.get_files()
    print(f"Original dataset has {len(files)} files:")
    for f in files:
        print(f"  - {f['filename']}: {f['size_human']}")
    print()
    
    print("Listing files in cloned dataset...")
    files = experiment_data.get_files()
    print(f"Cloned dataset has {len(files)} files:")
    for f in files:
        print(f"  - {f['filename']}: {f['size_human']}")
    print()
    
    # Step 9: List all snapshots
    print("Step 9: Listing all snapshots...")
    snapshots = training_data.get_snapshots()
    print(f"Dataset has {len(snapshots)} snapshots:")
    for snap in snapshots:
        print(f"  - {snap['name']} ({snap['create_time']})")
    print()
    
    # Step 10: List all datasets
    print("Step 10: Listing all datasets...")
    all_datasets = get_datasets()
    print(f"Found {len(all_datasets)} total datasets:")
    for ds in all_datasets:
        ds_type = "clone" if ds.is_clone else "original"
        print(f"  - {ds.name} ({ds.max_size}) [{ds_type}]")
        if ds.is_clone:
            print(f"    └─ Source: {ds.source_dataset_name}")
    print()
    
    # Step 11: Cleanup (optional)
    print("Step 11: Cleanup...")
    response = input("Delete experiment clone? (yes/no): ")
    if response.lower() == 'yes':
        experiment_data.delete()
        print("✓ Experiment clone deleted\n")
    else:
        print("✓ Experiment clone preserved\n")
    
    print("=== Workflow Complete ===")

if __name__ == "__main__":
    main()
```

Save this script and run it to see Dataset Manager in action!

**Happy dataset managing! 🚀**
