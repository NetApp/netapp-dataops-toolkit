#!/usr/bin/env python3
"""
Configuration Test Script for Dataset Manager

This script demonstrates how to check and configure the Dataset Manager.
"""

import sys
import os

# Add the netapp_dataops package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_configuration():
    """Test Dataset Manager configuration."""
    print("🔧 Dataset Manager Configuration Test")
    print("=" * 50)
    
    try:
        from netapp_dataops.traditional.datasets.dataset import Dataset
        from netapp_dataops.traditional.datasets.exceptions import DatasetConfigError
        
        print("✅ Dataset Manager components imported successfully")
        
        # Test configuration by attempting to create a dataset
        try:
            print("\n🧪 Testing configuration by creating a test dataset...")
            test_dataset = Dataset(name="config_test", max_size="1GB", print_output=False)
            print("✅ Configuration is working! Dataset created successfully.")
            
            # Clean up
            try:
                test_dataset.delete()
                print("✅ Test dataset cleaned up")
            except:
                pass
                
        except DatasetConfigError as e:
            print(f"⚠️  Configuration required: {e}")
            print("\n📋 To configure Dataset Manager:")
            print("   1. Run the configuration command:")
            print("      python -m netapp_dataops.netapp_dataops_cli config")
            print("\n   2. When prompted, answer 'yes' to:")
            print("      'Do you intend to use the toolkit's Dataset Manager functionality?'")
            print("\n   3. Follow the prompts to:")
            print("      - Configure ONTAP connection settings")
            print("      - Set up or create the root volume")
            print("      - Configure local mounting")
            print("\n   4. After configuration, run this test again")
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Please ensure you're in the correct directory")
        
if __name__ == "__main__":
    test_configuration()
