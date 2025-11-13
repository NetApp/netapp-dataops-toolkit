#!/usr/bin/env python3
"""Test script for create_volume function with 1TB volume size."""

import sys
from netapp_dataops.traditional.ontap import create_volume


def test_create_volume():
    """Test creating a 1TB volume."""
    
    # Test parameters
    volume_name = "test_volume_1tb"
    volume_size = "1TB"
    
    print(f"Testing create_volume function...")
    print(f"Volume Name: {volume_name}")
    print(f"Volume Size: {volume_size}")
    print("-" * 50)
    
    try:
        # Create the volume with basic parameters
        create_volume(
            volume_name=volume_name,
            volume_size=volume_size,
            guarantee_space=False,  # Thin provisioned
            volume_type="flexvol",
            unix_permissions="0777",
            unix_uid="0",
            unix_gid="0",
            export_policy="default",
            snapshot_policy="none",
            print_output=True  # Enable detailed output
        )
        
        print("\n" + "=" * 50)
        print("✓ Volume creation test completed successfully!")
        print("=" * 50)
        return 0
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"✗ Volume creation test failed!")
        print(f"Error: {e}")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("NetApp DataOps Toolkit - Volume Creation Test")
    print("=" * 50 + "\n")
    
    exit_code = test_create_volume()
    sys.exit(exit_code)
