import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from netapp_dataops.traditional.anf.config import (
    create_anf_config,
    _retrieve_anf_config,
    get_config_value,
    InvalidConfigError
)

# Test configuration data
SAMPLE_CONFIG = {
    "subscriptionId": "test-subscription-id",
    "resourceGroupName": "test-rg",
    "accountName": "test-account",
    "poolName": "test-pool",
    "location": "centralus",
    "virtualNetworkName": "test-vnet",
    "subnetName": "default",
    "protocolTypes": ["NFSv3"]
}

# =============================================================================
# CONFIG CREATION TESTS
# =============================================================================

def test_create_anf_config_success():
    """Test successful config creation"""
    with patch('os.path.isfile', return_value=False):  # No existing config file
        with patch('builtins.input', side_effect=[
            '',  # Press Enter to continue
            'test-subscription-id',
            'test-rg',
            'test-account',
            'test-pool',
            'centralus',
            'test-vnet',
            'default',
            'NFSv3',
            'y'  # Save confirmation
        ]):
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.open', mock_open()) as mock_file:
                    with patch('json.dump') as mock_json_dump:
                        create_anf_config()  # Function returns None on success
                        mock_makedirs.assert_called_once()
                        mock_json_dump.assert_called_once()

def test_create_anf_config_with_parameters():
    """Test config creation with custom path and filename"""
    with patch('os.path.isfile', return_value=False):  # No existing config file
        with patch('builtins.input', side_effect=[
            '',  # Press Enter to continue
            'test-subscription-id',
            'test-rg',
            'test-account',
            'test-pool',
            'centralus',
            'test-vnet',
            'default',
            'NFSv3',
            'y'  # Save confirmation
        ]):
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.open', mock_open()) as mock_file:
                    with patch('json.dump') as mock_json_dump:
                        create_anf_config(
                            config_dir_path='/custom/path',
                            config_filename='custom_config.json'
                        )
                        mock_makedirs.assert_called_once()
                        mock_json_dump.assert_called_once()

def test_create_anf_config_overwrite_existing():
    """Test config creation when existing config file exists"""
    with patch('os.path.isfile', return_value=True):
        with patch('builtins.input', side_effect=[
            'yes',  # Proceed with overwrite
            'test-subscription-id',
            'test-rg',
            'test-account',
            'test-pool',
            'centralus',
            'test-vnet',
            'default',
            'NFSv3',
            'y'  # Save confirmation
        ]):
            with patch('os.makedirs'):
                with patch('builtins.open', mock_open()):
                    with patch('json.dump'):
                        create_anf_config()  # Function returns None on success

# =============================================================================
# CONFIG RETRIEVAL TESTS
# =============================================================================

def test_retrieve_anf_config_success():
    """Test successful config retrieval"""
    with patch('os.path.isfile', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(SAMPLE_CONFIG))):
            config = _retrieve_anf_config()
            assert config['subscriptionId'] == 'test-subscription-id'
            assert config['resourceGroupName'] == 'test-rg'

def test_retrieve_anf_config_file_not_found():
    """Test config retrieval when file doesn't exist"""
    with patch('os.path.isfile', return_value=False):
        with pytest.raises(InvalidConfigError) as exc_info:
            _retrieve_anf_config()
        assert "ANF configuration file not found" in str(exc_info.value)

def test_retrieve_anf_config_invalid_json():
    """Test config retrieval with invalid JSON"""
    with patch('os.path.isfile', return_value=True):
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with pytest.raises(InvalidConfigError) as exc_info:
                _retrieve_anf_config()
            assert "Invalid JSON in ANF config file" in str(exc_info.value)

def test_retrieve_anf_config_missing_required_field():
    """Test config retrieval with missing required fields"""
    incomplete_config = {"subscriptionId": "test-id"}  # Missing other required fields
    with patch('os.path.isfile', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(incomplete_config))):
            with pytest.raises(InvalidConfigError) as exc_info:
                _retrieve_anf_config()
            assert "Missing required fields in ANF config" in str(exc_info.value)

# =============================================================================
# CONFIG VALUE RESOLUTION TESTS
# =============================================================================

def test_get_config_value_function_param_provided():
    """Test config value resolution when function parameter is provided"""
    config = SAMPLE_CONFIG.copy()
    value = get_config_value('resource_group_name', 'override-rg', config, False)
    assert value == 'override-rg'

def test_get_config_value_from_config():
    """Test config value resolution from config when function parameter is None"""
    config = SAMPLE_CONFIG.copy()
    value = get_config_value('resource_group_name', None, config, False)
    assert value == 'test-rg'

def test_get_config_value_missing_from_both():
    """Test config value resolution when value is missing from both function and config"""
    config = {"subscriptionId": "test-id"}  # Missing resourceGroupName
    with pytest.raises(InvalidConfigError) as exc_info:
        get_config_value('resource_group_name', None, config, False)
    assert "Parameter 'resource_group_name' not provided in function call and not found in config file" in str(exc_info.value)

def test_get_config_value_protocol_types():
    """Test config value resolution for protocol types list"""
    config = SAMPLE_CONFIG.copy()
    value = get_config_value('protocol_types', None, config, False)
    assert value == ['NFSv3']

def test_get_config_value_subscription_id():
    """Test config value resolution for subscription ID"""
    config = SAMPLE_CONFIG.copy()
    value = get_config_value('subscription_id', None, config, False)
    assert value == 'test-subscription-id'

# =============================================================================
# EDGE CASE TESTS  
# =============================================================================

def test_create_anf_config_directory_creation_fails():
    """Test config creation when directory creation fails"""
    with patch('os.path.isfile', return_value=False):  # No existing config file
        with patch('builtins.input', side_effect=[
            '',  # Press Enter to continue
            'test-subscription-id',
            'test-rg',
            'test-account',
            'test-pool',
            'centralus',
            'test-vnet',
            'default',
            'NFSv3',
            'y'  # Save confirmation
        ]):
            with patch('os.makedirs', side_effect=OSError("Permission denied")):
                with pytest.raises(InvalidConfigError) as exc_info:
                    create_anf_config()
                assert "Failed to create config directory" in str(exc_info.value)

def test_create_anf_config_file_write_fails():
    """Test config creation when file writing fails"""
    with patch('os.path.isfile', return_value=False):  # No existing config file
        with patch('builtins.input', side_effect=[
            '',  # Press Enter to continue
            'test-subscription-id',
            'test-rg',
            'test-account',
            'test-pool',
            'centralus',
            'test-vnet',
            'default',
            'NFSv3',
            'y'  # Save confirmation
        ]):
            with patch('os.makedirs'):
                with patch('builtins.open', side_effect=IOError("Disk full")):
                    with pytest.raises(InvalidConfigError) as exc_info:
                        create_anf_config()
                    assert "Failed to write config file" in str(exc_info.value)

def test_retrieve_anf_config_with_print_output():
    """Test config retrieval with print output enabled"""
    with patch('os.path.isfile', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(SAMPLE_CONFIG))):
            with patch('netapp_dataops.traditional.anf.config.logger') as mock_logger:
                config = _retrieve_anf_config(print_output=True)
                assert config['subscriptionId'] == 'test-subscription-id'
                mock_logger.info.assert_called()
