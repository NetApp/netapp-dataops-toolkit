import pytest
from unittest.mock import patch, MagicMock, Mock
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from netapp_dataops.traditional.anf import replication_management

# Required arguments for testing
REPLICATION_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-source-volume',
    'destination_resource_group_name': 'test-dest-rg',
    'destination_account_name': 'test-dest-account',
    'destination_pool_name': 'test-dest-pool',
    'destination_volume_name': 'test-dest-volume',
    'destination_location': 'westus',
    'destination_creation_token': 'test-dest-token',
    'destination_usage_threshold': 107374182400,  # 100 GiB
    'destination_protocol_types': ['NFSv3'],
    'destination_virtual_network_name': 'test-dest-vnet',
    'destination_subnet_name': 'default'
}


# =============================================================================
# CREATE REPLICATION TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_create_replication_success():
    """Test successful replication creation"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            
            # Mock volume authorization
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'success'


def test_create_replication_with_service_level():
    """Test replication creation with specific service level"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_service_level'] = 'Premium'
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_with_optional_params():
    """Test replication creation with optional parameters"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args.update({
        'destination_service_level': 'Premium',
        'destination_zones': ['1']
    })
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_with_zones():
    """Test replication creation with specific zones"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_zones'] = ['2']
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_create_replication_already_exists():
    """Test replication creation when replication already exists"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = ResourceExistsError("Replication already exists")
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'error'
            assert 'already exists' in result['details'].lower()


def test_create_replication_source_not_found():
    """Test replication creation when source volume doesn't exist"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.side_effect = ResourceNotFoundError("Source volume not found")
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'error'
            assert 'not found' in result['details'].lower()


def test_create_replication_client_exception():
    """Test replication creation with general client exception"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = Exception("Client error")
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'error'
            assert 'Client error' in result['details']

def test_create_replication_quota_exceeded():
    """Test replication creation when quota is exceeded"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = Exception("Quota exceeded for region")
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'error'
            assert 'quota exceeded' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_create_replication_network_error():
    """Test replication creation with network connectivity issues"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = Exception("Network timeout")
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'error'
            assert 'network timeout' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_create_replication_capacity_pool_not_found():
    """Test replication creation when destination capacity pool doesn't exist"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = ResourceNotFoundError("Capacity pool not found")
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'error'
            assert 'not found' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_create_replication_account_not_found():
    """Test replication creation when destination account doesn't exist"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = ResourceNotFoundError("NetApp account not found")
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            assert result['status'] == 'error'
            assert 'not found' in result['details'].lower() or 'failed to create' in result['details'].lower()

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_create_replication_missing_required_params():
    """Test replication creation with missing required parameters"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    del args['destination_account_name']
    with pytest.raises(TypeError):  # Python raises TypeError for missing positional args
        replication_management.create_replication(**args)


def test_create_replication_invalid_params():
    """Test replication creation with invalid parameters"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_usage_threshold'] = -1  # Invalid threshold
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = Exception("Invalid usage threshold")
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'error'


def test_create_replication_empty_destination_location():
    """Test replication creation with empty destination location"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_location'] = ""
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        
        result = replication_management.create_replication(**args)
        assert result['status'] == 'error'
        assert 'destination_location' in result['details'] or 'required' in result['details'].lower()

def test_create_replication_invalid_protocol_type():
    """Test replication creation with invalid protocol type"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_protocol_types'] = ['InvalidProtocol']
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = Exception("Invalid protocol type")
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'error'


def test_create_replication_invalid_service_level():
    """Test replication creation with invalid service level"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_service_level'] = 'InvalidLevel'
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = Exception("Invalid service level")
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'error'


def test_create_replication_invalid_zone():
    """Test replication creation with invalid availability zone"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_zones'] = ['99']  # Invalid zone
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.side_effect = Exception("Invalid availability zone")
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'error'


def test_create_replication_whitespace_destination_location():
    """Test replication creation with whitespace-only destination location"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_location'] = '   '
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        
        result = replication_management.create_replication(**args)
        assert result['status'] == 'error'


def test_create_replication_whitespace_creation_token():
    """Test replication creation with whitespace-only creation token"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_creation_token'] = '   '
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        
        result = replication_management.create_replication(**args)
        assert result['status'] == 'error'

# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

def test_create_replication_with_subscription_id():
    """Test replication creation with explicit subscription ID"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['subscription_id'] = 'different-subscription-id'
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'different-subscription-id')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_different_region():
    """Test replication creation with different region"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_location'] = 'eastus2'  # Different from westus
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_standard_service_level():
    """Test replication creation with Standard service level"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_service_level'] = 'Standard'
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_ultra_service_level():
    """Test replication creation with Ultra service level"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_service_level'] = 'Ultra'
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_with_multiple_zones():
    """Test replication creation with multiple availability zones"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_zones'] = ['1', '2', '3']
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_large_volume():
    """Test replication creation with large volume size"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_usage_threshold'] = 10995116277760  # 10 TiB
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_nfsv4_protocol():
    """Test replication creation with NFSv4.1 protocol"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_protocol_types'] = ['NFSv4.1']
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_smb_protocol():
    """Test replication creation with SMB protocol"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_protocol_types'] = ['CIFS']
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_dual_protocol():
    """Test replication creation with dual protocol (NFS + SMB)"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_protocol_types'] = ['NFSv3', 'CIFS']
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'

def test_create_replication_minimal_usage_threshold():
    """Test replication creation with minimal usage threshold"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_usage_threshold'] = 4398046511104  # 4 TiB minimum
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_special_characters_in_names():
    """Test replication creation with special characters in resource names"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_volume_name'] = 'test-volume_123'
    args['destination_creation_token'] = 'test-token_123'
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_long_resource_names():
    """Test replication creation with long resource names"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_volume_name'] = 'a' * 64  # Maximum length
    args['destination_creation_token'] = 'b' * 80  # Long token
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_unicode_characters():
    """Test replication creation with Unicode characters in names"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_volume_name'] = 'test-volume-🔄'
    args['destination_creation_token'] = 'test-token-αβγ'
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_different_subnet():
    """Test replication creation with different subnet configuration"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['destination_subnet_name'] = 'anf-subnet'
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_print_output_enabled():
    """Test replication creation with print output enabled"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    args['print_output'] = True
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_create_replication_end_to_end_workflow():
    """Test complete replication creation workflow"""
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            
            # Mock successful volume creation
            mock_create_volume.return_value = {
                'status': 'success', 
                'volume': MagicMock(),
                'message': 'Volume created successfully'
            }
            
            # Mock successful replication authorization
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**REPLICATION_REQUIRED_ARGS)
            
            # Verify the complete workflow
            assert result['status'] == 'success'
            mock_create_volume.assert_called_once()
            mock_client.volumes.begin_authorize_replication.assert_called_once()


def test_create_replication_resource_hierarchy_validation():
    """Test replication creation validates Azure resource hierarchy"""
    args = REPLICATION_REQUIRED_ARGS.copy()
    
    with patch('netapp_dataops.traditional.anf.replication_management.get_anf_client') as mock_client_func:
        with patch('netapp_dataops.traditional.anf.volume_management.create_volume') as mock_create_volume:
            mock_client = MagicMock()
            mock_client_func.return_value = (mock_client, 'test-subscription')
            mock_create_volume.return_value = {'status': 'success', 'volume': MagicMock()}
            mock_client.volumes.begin_authorize_replication.return_value.result.return_value = MagicMock()
            
            result = replication_management.create_replication(**args)
            
            # Verify resource hierarchy is properly constructed
            assert result['status'] == 'success'
            
            # Verify create_volume was called with correct hierarchy parameters
            call_args = mock_create_volume.call_args
            assert call_args[1]['resource_group_name'] == args['destination_resource_group_name']
            assert call_args[1]['account_name'] == args['destination_account_name']
            assert call_args[1]['pool_name'] == args['destination_pool_name']
            assert call_args[1]['volume_name'] == args['destination_volume_name']

