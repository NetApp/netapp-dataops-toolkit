#!/usr/bin/env python3
"""
End-to-End Test Script for Dataset Manager
==========================================

This script verifies all Dataset Manager features by executing real operations
against an ONTAP system. This is NOT a unit test - it performs actual operations
and requires a properly configured ONTAP environment.

Prerequisites:
--------------
1. NetApp DataOps Toolkit must be configured (run: netapp_dataops_cli.py config)
2. Dataset Manager must be enabled with a root volume
3. User must have permissions to create/delete volumes on the ONTAP system
4. Root volume must be properly mounted locally

Test Coverage:
--------------
1. Config file changes - creation of new dataset root volume
2. Config file changes - existing root volume
3. Dataset Class Instantiation
   a. Creating New Dataset
   b. Binding to Existing Dataset
4. Dataset Class Attributes
5. get_files() Method
6. clone() Method
7. snapshot() Method
8. get_snapshots() Method
9. delete() Method
10. get_datasets() Function

Usage:
------
python test_dataset_manager_e2e.py

Author: NetApp DataOps Toolkit Team
Date: February 2026
"""

import os
import sys
import time
import traceback
from datetime import datetime
from typing import List, Dict, Any

# Import Dataset Manager components
try:
    from netapp_dataops.traditional.datasets import Dataset, get_datasets
    from netapp_dataops.traditional.datasets.exceptions import (
        DatasetError,
        DatasetExistsError,
        DatasetConfigError,
        DatasetVolumeError
    )
except ImportError as e:
    print(f"ERROR: Failed to import NetApp DataOps Toolkit modules: {e}")
    print("Please ensure the toolkit is installed: pip install .")
    sys.exit(1)


# Test Configuration
# ==================
# You can modify these values to customize the test
TEST_DATASET_NAME_1 = f"test_dataset_e2e_1_{int(time.time())}"
TEST_DATASET_NAME_2 = f"test_dataset_e2e_2_{int(time.time())}"
TEST_CLONE_NAME = f"test_clone_e2e_{int(time.time())}"
TEST_SNAPSHOT_NAME_1 = "test_snapshot_1"
TEST_SNAPSHOT_NAME_2 = "test_snapshot_2"
TEST_DATASET_SIZE = "5GB"
TEST_DATASET_SIZE_2 = "3GB"

# Track created resources for cleanup
created_datasets = []
cleanup_on_failure = True  # Set to False to keep resources for debugging


# Utility Functions
# =================

def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_header(message):
    """Print a formatted header."""
    print_separator()
    print(f"  {message}")
    print_separator()


def print_subheader(message):
    """Print a formatted subheader."""
    print(f"\n>>> {message}")
    print("-" * 80)


def print_success(message):
    """Print a success message."""
    print(f"✓ SUCCESS: {message}")


def print_error(message):
    """Print an error message."""
    print(f"✗ ERROR: {message}")


def print_info(message):
    """Print an info message."""
    print(f"ℹ INFO: {message}")


def print_test_result(test_name, passed, details=""):
    """Print test result."""
    status = "PASSED" if passed else "FAILED"
    symbol = "✓" if passed else "✗"
    print(f"\n{symbol} Test: {test_name} - {status}")
    if details:
        print(f"   Details: {details}")


def cleanup_resources():
    """Clean up all created datasets."""
    if not created_datasets:
        return
    
    print_subheader("Cleaning up test resources...")
    for dataset_name in created_datasets:
        try:
            dataset = Dataset(name=dataset_name)
            dataset.delete(delete_non_clone=True, force=True)
            print_success(f"Deleted dataset: {dataset_name}")
        except Exception as e:
            print_error(f"Failed to delete dataset '{dataset_name}': {e}")


def write_test_file(filepath, content):
    """Write a test file to the dataset."""
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print_error(f"Failed to write file '{filepath}': {e}")
        return False


# Test Functions
# ==============

def test_1_verify_config():
    """Test 1: Verify Dataset Manager Configuration"""
    print_header("TEST 1: Verify Dataset Manager Configuration")
    
    try:
        # Try to import and check config by creating a test instance
        print_info("Checking if Dataset Manager is configured...")
        
        # This will raise DatasetConfigError if not configured
        test_dataset = Dataset(name=f"config_test_{int(time.time())}", max_size="1GB")
        
        print_success("Dataset Manager is properly configured")
        print_info(f"Root volume: Accessible via {test_dataset._root_volume_name}")
        print_info(f"Root mountpoint: {test_dataset._root_mountpoint}")
        
        # Clean up test dataset
        test_dataset.delete(delete_non_clone=True)
        
        print_test_result("Config Verification", True, "Dataset Manager configuration is valid")
        return True
        
    except DatasetConfigError as e:
        print_error(f"Dataset Manager configuration error: {e}")
        print_test_result("Config Verification", False, str(e))
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        traceback.print_exc()
        print_test_result("Config Verification", False, str(e))
        return False


def test_2_create_new_dataset():
    """Test 2: Create New Dataset"""
    print_header("TEST 2: Create New Dataset")
    
    try:
        print_info(f"Creating new dataset: {TEST_DATASET_NAME_1} with size {TEST_DATASET_SIZE}")
        
        # Create a new dataset
        dataset = Dataset(name=TEST_DATASET_NAME_1, max_size=TEST_DATASET_SIZE, print_output=True)
        created_datasets.append(TEST_DATASET_NAME_1)
        
        # Verify attributes
        print_info("Verifying dataset attributes...")
        assert dataset.name == TEST_DATASET_NAME_1, "Dataset name mismatch"
        assert dataset.local_file_path is not None, "Local file path not set"
        assert dataset.max_size is not None, "Max size not set"
        assert dataset.is_clone == False, "New dataset should not be a clone"
        assert dataset.source_dataset_name is None, "New dataset should have no source"
        
        print_success(f"Dataset created: {dataset.name}")
        print_info(f"  - Name: {dataset.name}")
        print_info(f"  - Local file path: {dataset.local_file_path}")
        print_info(f"  - Max size: {dataset.max_size}")
        print_info(f"  - Is clone: {dataset.is_clone}")
        print_info(f"  - Source dataset: {dataset.source_dataset_name}")
        
        # Verify local file path exists
        if os.path.exists(dataset.local_file_path):
            print_success(f"Local file path exists and is accessible: {dataset.local_file_path}")
        else:
            print_error(f"Local file path does not exist: {dataset.local_file_path}")
            print_error("Note: The Dataset Manager should have ensured the path is accessible during creation.")
            return False, None
        
        # Create some test files in the dataset for testing get_files()
        print_info("Creating test files in dataset for get_files() testing...")
        test_files = {
            'readme.txt': 'This is a test dataset created by the E2E test suite.',
            'data.csv': 'id,name,value\n1,test1,100\n2,test2,200\n3,test3,300',
            'config.json': '{"test": true, "dataset": "' + TEST_DATASET_NAME_1 + '"}'
        }
        
        for filename, content in test_files.items():
            filepath = os.path.join(dataset.local_file_path, filename)
            if write_test_file(filepath, content):
                print_success(f"  Created: {filename}")
            else:
                print_error(f"  Failed to create: {filename}")
        
        print_test_result("Create New Dataset", True, f"Created {TEST_DATASET_NAME_1}")
        return True, dataset
        
    except Exception as e:
        print_error(f"Failed to create dataset: {e}")
        traceback.print_exc()
        print_test_result("Create New Dataset", False, str(e))
        return False, None


def test_3_bind_to_existing_dataset():
    """Test 3: Bind to Existing Dataset"""
    print_header("TEST 3: Bind to Existing Dataset")
    
    try:
        print_info(f"Binding to existing dataset: {TEST_DATASET_NAME_1}")
        
        # Bind to the existing dataset (without max_size parameter)
        dataset = Dataset(name=TEST_DATASET_NAME_1)
        
        # Verify attributes are populated from existing volume
        print_info("Verifying dataset attributes...")
        assert dataset.name == TEST_DATASET_NAME_1, "Dataset name mismatch"
        assert dataset.local_file_path is not None, "Local file path not set"
        assert dataset.max_size is not None, "Max size not set"
        
        print_success(f"Bound to existing dataset: {dataset.name}")
        print_info(f"  - Name: {dataset.name}")
        print_info(f"  - Local file path: {dataset.local_file_path}")
        print_info(f"  - Max size: {dataset.max_size}")
        print_info(f"  - Is clone: {dataset.is_clone}")
        
        print_test_result("Bind to Existing Dataset", True, f"Bound to {TEST_DATASET_NAME_1}")
        return True, dataset
        
    except Exception as e:
        print_error(f"Failed to bind to existing dataset: {e}")
        traceback.print_exc()
        print_test_result("Bind to Existing Dataset", False, str(e))
        return False, None


def test_4_dataset_attributes():
    """Test 4: Verify Dataset Class Attributes"""
    print_header("TEST 4: Verify Dataset Class Attributes")
    
    try:
        dataset = Dataset(name=TEST_DATASET_NAME_1)
        
        print_info("Checking all required attributes...")
        
        # Check all required attributes
        attributes_to_check = {
            'name': TEST_DATASET_NAME_1,
            'local_file_path': str,
            'max_size': str,
            'is_clone': bool,
            'source_dataset_name': (str, type(None))
        }
        
        all_passed = True
        for attr_name, expected_type in attributes_to_check.items():
            if hasattr(dataset, attr_name):
                attr_value = getattr(dataset, attr_name)
                if attr_name == 'name':
                    # Check exact value for name
                    if attr_value == expected_type:
                        print_success(f"✓ {attr_name}: {attr_value}")
                    else:
                        print_error(f"✗ {attr_name}: Expected '{expected_type}', got '{attr_value}'")
                        all_passed = False
                else:
                    # Check type for other attributes
                    if isinstance(attr_value, expected_type):
                        print_success(f"✓ {attr_name}: {attr_value} (type: {type(attr_value).__name__})")
                    else:
                        print_error(f"✗ {attr_name}: Expected type {expected_type}, got {type(attr_value)}")
                        all_passed = False
            else:
                print_error(f"✗ {attr_name}: Attribute missing")
                all_passed = False
        
        print_test_result("Dataset Attributes", all_passed, "All attributes verified")
        return all_passed
        
    except Exception as e:
        print_error(f"Failed to verify attributes: {e}")
        traceback.print_exc()
        print_test_result("Dataset Attributes", False, str(e))
        return False


def test_5_get_files():
    """Test 5: Test get_files() Method"""
    print_header("TEST 5: Test get_files() Method")
    
    try:
        dataset = Dataset(name=TEST_DATASET_NAME_1)
        
        # Files were already created in test_2, but let's add a few more
        print_info("Adding additional test files to dataset...")
        additional_files = {
            'test_file_1.txt': 'This is test file 1 - added in test 5',
            'test_file_2.txt': 'This is test file 2 - added in test 5',
            'test_data.csv': 'col1,col2,col3\n1,2,3\n4,5,6'
        }
        
        for filename, content in additional_files.items():
            filepath = os.path.join(dataset.local_file_path, filename)
            if write_test_file(filepath, content):
                print_success(f"Created file: {filename}")
        
        # Wait a moment for file system to sync
        time.sleep(1)
        
        # Get files using the method
        print_info("Retrieving file list using get_files()...")
        files = dataset.get_files()
        
        print_info(f"Found {len(files)} files:")
        for file_info in files:
            print_info(f"  - {file_info['filename']}: {file_info['size_human']} ({file_info['filepath']})")
        
        # Verify we found at least the files we just created
        found_filenames = [f['filename'] for f in files]
        
        # Should have at least the files from test_2 (3 files) + test_5 (3 files) = 6 files minimum
        expected_files = ['readme.txt', 'data.csv', 'config.json', 
                         'test_file_1.txt', 'test_file_2.txt', 'test_data.csv']
        all_found = all(filename in found_filenames for filename in expected_files)
        
        if all_found:
            print_success(f"All expected files found ({len(expected_files)} files)")
        else:
            missing = [f for f in expected_files if f not in found_filenames]
            print_error(f"Some test files not found: {missing}")
        
        # Verify file info structure
        has_all_keys = True
        if files and len(files) > 0:
            required_keys = ['filename', 'filepath', 'size', 'size_human']
            first_file = files[0]
            has_all_keys = all(key in first_file for key in required_keys)
            
            if has_all_keys:
                print_success("File info has all required keys")
            else:
                print_error("File info missing required keys")
        
        # Verify we have at least 6 files
        has_enough_files = len(files) >= 6
        if not has_enough_files:
            print_error(f"Expected at least 6 files, found {len(files)}")
        
        test_passed = all_found and has_all_keys and has_enough_files
        print_test_result("get_files() Method", test_passed, 
                         f"Found {len(files)} files with correct structure")
        return test_passed
        
    except Exception as e:
        print_error(f"Failed to test get_files(): {e}")
        traceback.print_exc()
        print_test_result("get_files() Method", False, str(e))
        return False


def test_6_snapshot():
    """Test 6: Test snapshot() Method"""
    print_header("TEST 6: Test snapshot() Method")
    
    try:
        dataset = Dataset(name=TEST_DATASET_NAME_1)
        
        # Create snapshot with custom name
        print_info(f"Creating snapshot with custom name: {TEST_SNAPSHOT_NAME_1}")
        snapshot_name_1 = dataset.snapshot(name=TEST_SNAPSHOT_NAME_1)
        print_success(f"Created snapshot: {snapshot_name_1}")
        
        # Verify returned snapshot name matches
        assert snapshot_name_1 == TEST_SNAPSHOT_NAME_1, "Snapshot name mismatch"
        
        # Wait a moment
        time.sleep(2)
        
        # Create snapshot with auto-generated name
        print_info("Creating snapshot with auto-generated name...")
        snapshot_name_2 = dataset.snapshot()
        print_success(f"Created snapshot: {snapshot_name_2}")
        
        # Verify auto-generated name is returned
        assert snapshot_name_2 is not None, "Snapshot name not returned"
        assert len(snapshot_name_2) > 0, "Snapshot name is empty"
        
        print_test_result("snapshot() Method", True, 
                         f"Created snapshots: {snapshot_name_1}, {snapshot_name_2}")
        return True
        
    except Exception as e:
        print_error(f"Failed to test snapshot(): {e}")
        traceback.print_exc()
        print_test_result("snapshot() Method", False, str(e))
        return False


def test_7_get_snapshots():
    """Test 7: Test get_snapshots() Method"""
    print_header("TEST 7: Test get_snapshots() Method")
    
    try:
        dataset = Dataset(name=TEST_DATASET_NAME_1)
        
        print_info("Retrieving snapshots using get_snapshots()...")
        snapshots = dataset.get_snapshots()
        
        print_info(f"Found {len(snapshots)} snapshots:")
        for snap in snapshots:
            print_info(f"  - {snap['name']}: {snap['create_time']}")
        
        # Verify we have at least the snapshots we created
        assert len(snapshots) >= 2, "Expected at least 2 snapshots"
        
        # Verify snapshot structure
        has_all_keys = True
        if snapshots and len(snapshots) > 0:
            required_keys = ['name', 'create_time']
            first_snap = snapshots[0]
            has_all_keys = all(key in first_snap for key in required_keys)
            
            if has_all_keys:
                print_success("Snapshot info has all required keys")
            else:
                print_error("Snapshot info missing required keys")
        
        # Verify we can find our custom-named snapshot
        snapshot_names = [s['name'] for s in snapshots]
        found_custom_snapshot = TEST_SNAPSHOT_NAME_1 in snapshot_names
        
        if found_custom_snapshot:
            print_success(f"Found custom snapshot: {TEST_SNAPSHOT_NAME_1}")
        else:
            print_error(f"Custom snapshot not found: {TEST_SNAPSHOT_NAME_1}")
        
        test_passed = has_all_keys and found_custom_snapshot
        print_test_result("get_snapshots() Method", test_passed,
                         f"Found {len(snapshots)} snapshots with correct structure")
        return test_passed
        
    except Exception as e:
        print_error(f"Failed to test get_snapshots(): {e}")
        traceback.print_exc()
        print_test_result("get_snapshots() Method", False, str(e))
        return False


def test_8_clone():
    """Test 8: Test clone() Method"""
    print_header("TEST 8: Test clone() Method")
    
    try:
        dataset = Dataset(name=TEST_DATASET_NAME_1)
        
        print_info(f"Cloning dataset '{TEST_DATASET_NAME_1}' to '{TEST_CLONE_NAME}'...")
        cloned_dataset = dataset.clone(name=TEST_CLONE_NAME)
        created_datasets.append(TEST_CLONE_NAME)
        
        # Verify clone attributes
        print_info("Verifying cloned dataset attributes...")
        assert cloned_dataset.name == TEST_CLONE_NAME, "Clone name mismatch"
        assert cloned_dataset.is_clone == True, "Cloned dataset should have is_clone=True"
        assert cloned_dataset.source_dataset_name == TEST_DATASET_NAME_1, "Source dataset name mismatch"
        assert cloned_dataset.local_file_path is not None, "Clone local file path not set"
        
        print_success(f"Cloned dataset created: {cloned_dataset.name}")
        print_info(f"  - Name: {cloned_dataset.name}")
        print_info(f"  - Local file path: {cloned_dataset.local_file_path}")
        print_info(f"  - Is clone: {cloned_dataset.is_clone}")
        print_info(f"  - Source dataset: {cloned_dataset.source_dataset_name}")
        
        # Verify clone contains the same files as source
        print_info("Verifying clone contains source files...")
        clone_files = cloned_dataset.get_files()
        source_files = dataset.get_files()
        
        clone_filenames = sorted([f['filename'] for f in clone_files])
        source_filenames = sorted([f['filename'] for f in source_files])
        
        files_match = clone_filenames == source_filenames
        if files_match:
            print_success("Clone contains the same files as source")
        else:
            print_error("Clone files do not match source files")
        
        # Verify clone local path exists
        path_exists = os.path.exists(cloned_dataset.local_file_path)
        if path_exists:
            print_success(f"Clone local path exists: {cloned_dataset.local_file_path}")
        else:
            print_error(f"Clone local path does not exist: {cloned_dataset.local_file_path}")
        
        test_passed = files_match and path_exists
        print_test_result("clone() Method", test_passed, f"Created clone {TEST_CLONE_NAME}")
        return test_passed
        
    except Exception as e:
        print_error(f"Failed to test clone(): {e}")
        traceback.print_exc()
        print_test_result("clone() Method", False, str(e))
        return False


def test_9_get_datasets():
    """Test 9: Test get_datasets() Function"""
    print_header("TEST 9: Test get_datasets() Function")
    
    try:
        print_info("Retrieving all datasets using get_datasets()...")
        all_datasets = get_datasets(print_output=True)
        
        print_info(f"Found {len(all_datasets)} datasets:")
        for ds in all_datasets:
            print_info(f"  - {ds.name}: {ds.max_size} at {ds.local_file_path}")
        
        # Verify we can find our test datasets
        dataset_names = [ds.name for ds in all_datasets]
        
        found_dataset_1 = TEST_DATASET_NAME_1 in dataset_names
        found_clone = TEST_CLONE_NAME in dataset_names
        
        if found_dataset_1:
            print_success(f"Found test dataset: {TEST_DATASET_NAME_1}")
        else:
            print_error(f"Test dataset not found: {TEST_DATASET_NAME_1}")
        
        if found_clone:
            print_success(f"Found test clone: {TEST_CLONE_NAME}")
        else:
            print_error(f"Test clone not found: {TEST_CLONE_NAME}")
        
        # Verify each dataset object has correct attributes
        all_have_attributes = True
        for ds in all_datasets:
            if not all(hasattr(ds, attr) for attr in ['name', 'local_file_path', 'max_size', 'is_clone']):
                all_have_attributes = False
                print_error(f"Dataset {ds.name} missing required attributes")
        
        if all_have_attributes:
            print_success("All datasets have required attributes")
        
        test_passed = found_dataset_1 and found_clone and all_have_attributes
        print_test_result("get_datasets() Function", test_passed,
                         f"Found {len(all_datasets)} datasets including test datasets")
        return test_passed
        
    except Exception as e:
        print_error(f"Failed to test get_datasets(): {e}")
        traceback.print_exc()
        print_test_result("get_datasets() Function", False, str(e))
        return False


def test_10_delete():
    """Test 10: Test delete() Method"""
    print_header("TEST 10: Test delete() Method")
    
    try:
        # Create a temporary dataset for deletion test
        temp_dataset_name = f"test_delete_e2e_{int(time.time())}"
        print_info(f"Creating temporary dataset for deletion test: {temp_dataset_name}")
        
        temp_dataset = Dataset(name=temp_dataset_name, max_size="1GB", print_output=True)
        
        # Verify it exists
        all_datasets = get_datasets()
        dataset_names = [ds.name for ds in all_datasets]
        assert temp_dataset_name in dataset_names, "Temporary dataset not found after creation"
        print_success(f"Temporary dataset created: {temp_dataset_name}")
        
        # Delete it
        print_info(f"Deleting dataset: {temp_dataset_name}")
        temp_dataset.delete(delete_non_clone=True)
        print_success(f"Dataset deleted: {temp_dataset_name}")
        
        # Wait a moment for deletion to complete
        time.sleep(3)
        
        # Verify it no longer exists
        print_info("Verifying dataset was deleted...")
        all_datasets_after = get_datasets()
        dataset_names_after = [ds.name for ds in all_datasets_after]
        
        not_in_list = temp_dataset_name not in dataset_names_after
        if not_in_list:
            print_success("Dataset successfully deleted and no longer appears in get_datasets()")
        else:
            print_error("Dataset still appears in get_datasets() after deletion")
            return False
        
        # Try to bind to deleted dataset (should fail)
        print_info("Attempting to bind to deleted dataset (should fail)...")
        try:
            deleted_dataset = Dataset(name=temp_dataset_name)
            print_error("ERROR: Was able to bind to deleted dataset (should have failed)")
            return False
        except DatasetError:
            print_success("Correctly failed to bind to deleted dataset")
        
        print_test_result("delete() Method", True, f"Successfully deleted {temp_dataset_name}")
        return True
        
    except Exception as e:
        print_error(f"Failed to test delete(): {e}")
        traceback.print_exc()
        print_test_result("delete() Method", False, str(e))
        return False


def test_11_error_handling():
    """Test 11: Test Error Handling"""
    print_header("TEST 11: Test Error Handling")
    
    try:
        all_passed = True
        
        # Test 1: Creating dataset without max_size
        print_info("Test 11a: Creating new dataset without max_size (should fail)...")
        try:
            bad_dataset = Dataset(name=f"bad_dataset_{int(time.time())}")
            print_error("ERROR: Dataset creation succeeded without max_size")
            all_passed = False
        except DatasetError as e:
            print_success(f"Correctly raised DatasetError: {e}")
        
        # Test 2: Binding with mismatched max_size
        print_info("Test 11b: Binding to existing dataset with wrong max_size (should fail)...")
        try:
            bad_dataset = Dataset(name=TEST_DATASET_NAME_1, max_size="999GB")
            print_error("ERROR: Dataset binding succeeded with wrong max_size")
            all_passed = False
        except DatasetError as e:
            print_success(f"Correctly raised DatasetError: {e}")
        
        # Test 3: Creating duplicate clone
        print_info("Test 11c: Creating duplicate clone (should fail)...")
        try:
            dataset = Dataset(name=TEST_DATASET_NAME_1)
            duplicate_clone = dataset.clone(name=TEST_CLONE_NAME)
            print_error("ERROR: Duplicate clone creation succeeded")
            all_passed = False
        except DatasetExistsError as e:
            print_success(f"Correctly raised DatasetExistsError: {e}")
        
        print_test_result("Error Handling", all_passed, "All error cases handled correctly")
        return all_passed
        
    except Exception as e:
        print_error(f"Failed to test error handling: {e}")
        traceback.print_exc()
        print_test_result("Error Handling", False, str(e))
        return False


# Main Test Runner
# ================

def main():
    """Main test runner."""
    print_separator("=", 80)
    print("  NetApp DataOps Toolkit - Dataset Manager E2E Test")
    print("  " + "=" * 76)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator("=", 80)
    print()
    
    # Track test results
    test_results = {}
    
    try:
        # Run all tests
        test_results['Config Verification'] = test_1_verify_config()
        
        if not test_results['Config Verification']:
            print_error("\nConfiguration verification failed. Cannot proceed with tests.")
            print_info("Please run: netapp_dataops_cli.py config")
            print_info("And ensure Dataset Manager is enabled with a root volume.")
            return False
        
        # Continue with remaining tests
        success, _ = test_2_create_new_dataset()
        test_results['Create New Dataset'] = success
        
        success, _ = test_3_bind_to_existing_dataset()
        test_results['Bind to Existing'] = success
        
        test_results['Dataset Attributes'] = test_4_dataset_attributes()
        test_results['get_files()'] = test_5_get_files()
        test_results['snapshot()'] = test_6_snapshot()
        test_results['get_snapshots()'] = test_7_get_snapshots()
        test_results['clone()'] = test_8_clone()
        test_results['get_datasets()'] = test_9_get_datasets()
        test_results['delete()'] = test_10_delete()
        test_results['Error Handling'] = test_11_error_handling()
        
    except KeyboardInterrupt:
        print_error("\n\nTest interrupted by user")
        if cleanup_on_failure:
            cleanup_resources()
        return False
    except Exception as e:
        print_error(f"\n\nUnexpected error during test execution: {e}")
        traceback.print_exc()
        if cleanup_on_failure:
            cleanup_resources()
        return False
    finally:
        # Print summary
        print_header("TEST SUMMARY")
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print()
        
        for test_name, result in test_results.items():
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"  {status}: {test_name}")
        
        print()
        
        # Cleanup
        if created_datasets:
            cleanup_choice = input("\nCleanup created test datasets? (y/n): ").lower()
            if cleanup_choice == 'y':
                cleanup_resources()
            else:
                print_info("Skipping cleanup. Please manually delete the following datasets:")
                for ds_name in created_datasets:
                    print_info(f"  - {ds_name}")
        
        print_separator("=", 80)
        
        if failed_tests == 0:
            print_success("ALL TESTS PASSED!")
            return True
        else:
            print_error(f"{failed_tests} TEST(S) FAILED")
            return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
