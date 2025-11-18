# Google Cloud NetApp Volumes (GCNV) - Refactored Module

## Overview

The GCNV functionality has been refactored into a clean, organized module structure for better maintainability and usability.

## New Module Structure

```
netapp_dataops/traditional/gcnv/
├── __init__.py                # Package initialization and exports
├── base.py                    # Common utilities and helper functions
├── volume_management.py       # Volume management functions
├── snapshot_management.py     # Snapshot management functions
└── replication_management.py  # Replication management functions
```

## Usage Examples

### Import Options

You can import the entire GCNV module:
```python
from netapp_dataops.traditional import gcnv

# Use functions with module prefix
result = gcnv.create_volume(...)
snapshots = gcnv.list_snapshots(...)
```

Or import specific functions:
```python
from netapp_dataops.traditional.gcnv import create_volume, list_volumes
from netapp_dataops.traditional.gcnv import create_snapshot, delete_snapshot

# Use functions directly
result = create_volume(...)
snapshots = list_snapshots(...)
```

Or import from specific modules:
```python
from netapp_dataops.traditional.gcnv.volume_management import create_volume, clone_volume
from netapp_dataops.traditional.gcnv.snapshot_management import create_snapshot

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
- `create_volume()` - Create new NetApp volumes
- `clone_volume()` - Clone existing volumes from snapshots  
- `delete_volume()` - Delete volumes
- `list_volumes()` - List all volumes in a location

### Snapshot Operations
- `create_snapshot()` - Create volume snapshots
- `delete_snapshot()` - Delete snapshots
- `list_snapshots()` - List snapshots for a volume

### Replication Operations
- `create_replication()` - Create volume replications

### Utilities
- `_serialize()` - Convert protobuf objects to JSON-serializable structures
