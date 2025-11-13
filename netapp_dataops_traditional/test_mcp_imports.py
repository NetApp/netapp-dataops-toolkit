#!/usr/bin/env python3
"""Test script to verify MCP server imports are working correctly."""

import sys


def test_ontap_mcp_imports():
    """Test ONTAP MCP server imports."""
    print("\n" + "=" * 60)
    print("Testing ONTAP MCP Server Imports")
    print("=" * 60)
    
    try:
        print("\n1. Testing netapp_dataops.traditional.ontap imports...")
        from netapp_dataops.traditional.ontap import (
            create_volume, 
            clone_volume, 
            list_volumes, 
            mount_volume, 
            create_snapshot, 
            list_snapshots, 
            create_snap_mirror_relationship, 
            list_snap_mirror_relationships,
            create_flexcache
        )
        print("   ✓ All ONTAP functions imported successfully!")
        print(f"   - create_volume: {create_volume}")
        print(f"   - clone_volume: {clone_volume}")
        print(f"   - list_volumes: {list_volumes}")
        print(f"   - mount_volume: {mount_volume}")
        print(f"   - create_snapshot: {create_snapshot}")
        print(f"   - list_snapshots: {list_snapshots}")
        print(f"   - create_snap_mirror_relationship: {create_snap_mirror_relationship}")
        print(f"   - list_snap_mirror_relationships: {list_snap_mirror_relationships}")
        print(f"   - create_flexcache: {create_flexcache}")
        
        print("\n2. Testing MCP server module import...")
        # Just import, don't run
        from netapp_dataops.mcp_server import netapp_dataops_ontap_mcp
        print("   ✓ ONTAP MCP server module imported successfully!")
        
        return True
        
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False


def test_gcnv_mcp_imports():
    """Test GCNV MCP server imports."""
    print("\n" + "=" * 60)
    print("Testing GCNV MCP Server Imports")
    print("=" * 60)
    
    try:
        print("\n1. Testing netapp_dataops.traditional.gcnv imports...")
        from netapp_dataops.traditional.gcnv import (
            create_volume,
            clone_volume,
            list_volumes,
            create_snapshot,
            list_snapshots,
            create_replication
        )
        print("   ✓ All GCNV functions imported successfully!")
        print(f"   - create_volume: {create_volume}")
        print(f"   - clone_volume: {clone_volume}")
        print(f"   - list_volumes: {list_volumes}")
        print(f"   - create_snapshot: {create_snapshot}")
        print(f"   - list_snapshots: {list_snapshots}")
        print(f"   - create_replication: {create_replication}")
        
        print("\n2. Testing MCP server module import...")
        # Just import, don't run
        from netapp_dataops.mcp_server import netapp_dataops_gcnv_mcp
        print("   ✓ GCNV MCP server module imported successfully!")
        
        return True
        
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False


def test_mcp_dependencies():
    """Test MCP server dependencies."""
    print("\n" + "=" * 60)
    print("Testing MCP Dependencies")
    print("=" * 60)
    
    dependencies = {
        "fastmcp": "FastMCP framework",
        "netapp_dataops.logging_utils": "Logging utilities",
        "netapp_dataops.mcp_server.config": "MCP configuration"
    }
    
    all_ok = True
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"   ✓ {description}: {module}")
        except ImportError as e:
            print(f"   ✗ {description}: {module} - {e}")
            all_ok = False
    
    return all_ok


def main():
    """Run all import tests."""
    print("\n" + "=" * 60)
    print("NetApp DataOps Toolkit - MCP Server Import Test")
    print("=" * 60)
    
    results = []
    
    # Test ONTAP MCP imports
    results.append(("ONTAP MCP", test_ontap_mcp_imports()))
    
    # Test GCNV MCP imports
    results.append(("GCNV MCP", test_gcnv_mcp_imports()))
    
    # Test MCP dependencies
    results.append(("MCP Dependencies", test_mcp_dependencies()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All import tests passed! MCP servers are ready to use.")
        return 0
    else:
        print("\n⚠️  Some import tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
