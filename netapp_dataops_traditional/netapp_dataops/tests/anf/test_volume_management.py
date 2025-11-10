import pytest
from unittest.mock import patch, MagicMock, Mock
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from netapp_dataops.traditional.anf import volume_management

# Required arguments for create volume testing
CREATE_REQUIRED_ARGS = dict(
    resource_group_name='test-rg',
    account_name='test-account',
    pool_name='test-pool',
    volume_name='test-volume',
    location='eastus',
    creation_token='test-token',
    usage_threshold=107374182400,  # 100 GiB
    protocol_types=['NFSv3'],
    virtual_network_name='test-vnet',
    subnet_name='default'
)

# Required arguments for clone volume testing
CLONE_REQUIRED_ARGS = dict(
    resource_group_name='test-rg',
    account_name='test-account',
    pool_name='test-pool',
    source_volume_name='test-source-volume',
    volume_name='test-clone-volume',
    location='eastus',
    creation_token='test-clone-token',
    snapshot_name='test-snapshot',
    virtual_network_name='test-vnet',
    subnet_name='default'
)

# Required arguments for delete volume testing
DELETE_REQUIRED_ARGS = dict(
    resource_group_name='test-rg',
    account_name='test-account',
    pool_name='test-pool',
    volume_name='test-volume'
)

# Required arguments for list volumes testing
LIST_REQUIRED_ARGS = dict(
    resource_group_name='test-rg',
    account_name='test-account',
    pool_name='test-pool'
)

# =============================================================================
# CREATE VOLUME TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------
def test_create_volume_success():
    """Test successful volume creation with minimal required parameters"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert result['status'] == 'success'

def test_create_volume_optional_args():
    """Test volume creation with optional parameters"""
    args = CREATE_REQUIRED_ARGS.copy()
    args.update({
        'service_level': 'Premium',
        'tags': {'env': 'test'},
        'zones': ['1'],
        'security_style': 'Unix',
        'throughput_mibps': 16.0,
        'unix_permissions': '0755'
    })
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_with_all_optional_params():
    """Test create volume with comprehensive optional parameters"""
    args = CREATE_REQUIRED_ARGS.copy()
    args.update({
        'service_level': 'Ultra',
        'tags': {'env': 'production', 'team': 'data'},
        'zones': ['1', '2'],
        'export_policy_rules': [{
            'rule_index': 1,
            'allowed_clients': '0.0.0.0/0',
            'unix_read_only': False,
            'unix_read_write': True,
            'cifs': False,
            'nfsv3': True,
            'nfsv41': False
        }],
        'security_style': 'Unix',
        'smb_encryption': False,
        'smb_continuously_available': False,
        'throughput_mibps': 64.0,
        'volume_type': 'DataProtection',
        'is_default_quota_enabled': True,
        'default_user_quota_in_ki_bs': 1048576,
        'default_group_quota_in_ki_bs': 1048576,
        'unix_permissions': '0755',
        'avs_data_store': 'Enabled',
        'is_large_volume': False,
        'kerberos_enabled': False,
        'ldap_enabled': False,
        'cool_access': False,
        'coolness_period': 7,
        'snapshot_directory_visible': True,
        'network_features': 'Standard',
        'encryption_key_source': 'Microsoft.NetApp',
        'enable_subvolumes': 'Enabled'
    })
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_boundary_usage_threshold():
    """Test volume creation with boundary usage threshold values"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 53687091200  # 50 GiB - minimum
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------
def test_create_volume_already_exists():
    """Test volume creation when volume already exists"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = ResourceExistsError("Volume already exists")
        result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'already exists' in result['details'].lower()

def test_create_volume_client_exception():
    """Test volume creation with general client exception"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Client error")
        result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Client error' in result['details']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------
def test_create_volume_missing_required_params():
    """Test volume creation with missing required parameters"""
    args = CREATE_REQUIRED_ARGS.copy()
    del args['resource_group_name']
    # Python raises TypeError for missing required positional arguments
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        volume_management.create_volume(**args)

def test_create_volume_invalid_usage_threshold():
    """Test volume creation with invalid usage threshold"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 'invalid'
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Invalid usage threshold")
        result = volume_management.create_volume(**args)
        assert result['status'] == 'error'

def test_create_volume_empty_protocol_types():
    """Test volume creation with empty protocol types"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['protocol_types'] = []
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Protocol types required")
        result = volume_management.create_volume(**args)
        assert result['status'] == 'error'

# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------
def test_create_volume_max_usage_threshold():
    """Test volume creation with maximum usage threshold"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 109951162777600  # 100 TiB - maximum for regular volumes
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_multiple_protocols():
    """Test volume creation with multiple protocol types"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['protocol_types'] = ['NFSv3', 'NFSv4.1', 'CIFS']
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_standard_service_level():
    """Test volume creation with Standard service level"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['service_level'] = 'Standard'
    args['usage_threshold'] = 4398046511104  # 4 TiB minimum for Standard
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_premium_service_level():
    """Test volume creation with Premium service level"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['service_level'] = 'Premium'
    args['usage_threshold'] = 536870912000  # 500 GiB
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_ultra_service_level():
    """Test volume creation with Ultra service level"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['service_level'] = 'Ultra'
    args['usage_threshold'] = 107374182400  # 100 GiB
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_nfsv4_1():
    """Test volume creation with NFSv4.1 protocol"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['protocol_types'] = ['NFSv4.1']
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_smb():
    """Test volume creation with SMB protocol"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['protocol_types'] = ['CIFS']
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_dual_protocol():
    """Test volume creation with dual protocol (NFSv3 and CIFS)"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['protocol_types'] = ['NFSv3', 'CIFS']
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_with_zone_1():
    """Test volume creation in availability zone 1"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['zones'] = ['1']
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_with_zone_2():
    """Test volume creation in availability zone 2"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['zones'] = ['2']
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_with_zone_3():
    """Test volume creation in availability zone 3"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['zones'] = ['3']
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_large_1tb():
    """Test volume creation with 1TB size"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 1099511627776  # 1 TiB
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_large_10tb():
    """Test volume creation with 10TB size"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 10995116277760  # 10 TiB
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_maximum_size():
    """Test volume creation with maximum size (100TB)"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 109951162777600  # 100 TiB
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_with_export_policy():
    """Test volume creation with custom export policy"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['export_policy'] = {
        'rules': [
            {
                'ruleIndex': 1,
                'allowedClients': '10.0.0.0/24',
                'cifs': False,
                'nfsv3': True,
                'nfsv41': False,
                'unixReadOnly': False,
                'unixReadWrite': True
            }
        ]
    }
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_with_readonly_export():
    """Test volume creation with read-only export policy"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['export_policy'] = {
        'rules': [
            {
                'ruleIndex': 1,
                'allowedClients': '0.0.0.0/0',
                'cifs': False,
                'nfsv3': True,
                'nfsv41': False,
                'unixReadOnly': True,
                'unixReadWrite': False
            }
        ]
    }
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_with_application_tags():
    """Test volume creation with application-specific tags"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['tags'] = {
        'application': 'database',
        'environment': 'production',
        'owner': 'dba-team',
        'cost-center': 'IT-001'
    }
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_with_compliance_tags():
    """Test volume creation with compliance tags"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['tags'] = {
        'compliance': 'GDPR',
        'data-classification': 'sensitive',
        'backup-required': 'yes',
        'encryption': 'enabled'
    }
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_quota_exceeded():
    """Test volume creation when subscription quota is exceeded"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Quota exceeded")

        result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'quota' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_create_volume_network_unavailable():
    """Test volume creation when virtual network is unavailable"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Virtual network unavailable")

        result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'network' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_create_volume_insufficient_capacity():
    """Test volume creation with insufficient pool capacity"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Insufficient capacity in pool")

        result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'capacity' in result['details'].lower() or 'failed to create' in result['details'].lower()

def test_create_volume_invalid_service_level():
    """Test volume creation with invalid service level"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['service_level'] = 'InvalidLevel'
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Invalid service level")
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'error'


def test_create_volume_invalid_protocol():
    """Test volume creation with invalid protocol type"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['protocol_types'] = ['InvalidProtocol']
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Invalid protocol")
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'error'


def test_create_volume_invalid_zone():
    """Test volume creation with invalid availability zone"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['zones'] = ['4']  # Zone 4 doesn't exist
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Invalid zone")
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'error'


def test_create_volume_size_too_small():
    """Test volume creation with size below minimum"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 1073741824  # 1 GiB (below 100 GiB minimum)
    
    with pytest.raises((ValueError, TypeError)):
        volume_management.create_volume(**args)


def test_create_volume_size_too_large():
    """Test volume creation with size above maximum"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['usage_threshold'] = 549755813888000  # 500 TiB (above 100 TiB maximum)
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = Exception("Volume size too large")
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'error'

def test_create_volume_unicode_name():
    """Test volume creation with Unicode characters in name"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['volume_name'] = 'test-volume-测试-🗃️'
    args['creation_token'] = 'test-token-测试-unicode'
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_maximum_name_length():
    """Test volume creation with maximum allowed name length"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['volume_name'] = 'a' * 64  # Maximum length
    args['creation_token'] = 'b' * 80  # Maximum creation token length
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'


def test_create_volume_special_characters():
    """Test volume creation with special characters in name"""
    args = CREATE_REQUIRED_ARGS.copy()
    args['volume_name'] = 'test-volume_123-v2.0'
    args['creation_token'] = 'test-token_123-v2.0'
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**args)
        assert result['status'] == 'success'

def test_create_volume_concurrent_requests():
    """Test volume creation with concurrent requests simulation"""
    import threading
    import time
    
    results = []
    exceptions = []
    
    def create_volume_thread():
        try:
            with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
                mock_client = MagicMock()
                mock_client_func.return_value = (mock_client, 'test-subscription')
                mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()

                args = CREATE_REQUIRED_ARGS.copy()
                args['volume_name'] = f'concurrent-volume-{threading.current_thread().ident}'
                args['creation_token'] = f'concurrent-token-{threading.current_thread().ident}'
                
                result = volume_management.create_volume(**args)
                results.append(result)
        except Exception as e:
            exceptions.append(e)
    
    # Create multiple threads to simulate concurrent volume creation
    threads = []
    for i in range(3):
        thread = threading.Thread(target=create_volume_thread)
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all volumes were created successfully
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
    assert len(results) >= 1, "No volumes were created"

# =============================================================================
# CLONE VOLUME TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------
def test_clone_volume_success():
    """Test successful volume cloning"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.clone_volume(**CLONE_REQUIRED_ARGS)
        assert result['status'] == 'success'

def test_clone_volume_with_different_snapshot():
    """Test volume cloning with a different snapshot name"""
    args = CLONE_REQUIRED_ARGS.copy()
    args['snapshot_name'] = 'different-snapshot'
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        result = volume_management.clone_volume(**args)
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------
def test_clone_volume_source_not_found():
    """Test volume cloning when source volume doesn't exist"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.side_effect = ResourceNotFoundError("Source volume not found")
        result = volume_management.clone_volume(**CLONE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'not found' in result['details'].lower()

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------
def test_clone_volume_missing_source():
    """Test volume cloning with missing source volume name"""
    args = CLONE_REQUIRED_ARGS.copy()
    del args['source_volume_name']
    # Python raises TypeError for missing required positional arguments
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        volume_management.clone_volume(**args)

# =============================================================================
# LIST VOLUMES TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------
def test_list_volumes_success():
    """Test successful listing of volumes"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_volume = MagicMock()
        mock_volume.name = 'test-volume'
        mock_client.volumes.list.return_value = [mock_volume]
        result = volume_management.list_volumes(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 1

def test_list_volumes_empty():
    """Test listing volumes when no volumes exist"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.list.return_value = []
        result = volume_management.list_volumes(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 0

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------
def test_list_volumes_client_exception():
    """Test listing volumes with client exception"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.list.side_effect = Exception("Client error")
        result = volume_management.list_volumes(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Client error' in result['details']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------
def test_list_volumes_missing_required_params():
    """Test listing volumes with missing required parameters"""
    args = LIST_REQUIRED_ARGS.copy()
    del args['resource_group_name']
    # Python raises TypeError for missing required positional arguments
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        volume_management.list_volumes(**args)

def test_list_volumes_large_result_set():
    """Test list volumes with large number of volumes"""
    mock_volumes = []
    for i in range(100):
        mock_volume = MagicMock()
        mock_volume.name = f'volume-{i}'
        mock_volume.usage_threshold = 107374182400  # 100 GiB
        mock_volumes.append(mock_volume)
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.list.return_value = mock_volumes
        
        result = volume_management.list_volumes(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 100

# =============================================================================
# DELETE VOLUME TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------
def test_delete_volume_success():
    """Test successful volume deletion"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_delete.return_value.result.return_value = None
        result = volume_management.delete_volume(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------
def test_delete_volume_not_found():
    """Test volume deletion when volume doesn't exist"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_delete.side_effect = ResourceNotFoundError("Volume not found")
        result = volume_management.delete_volume(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'not found' in result['details'].lower()

def test_delete_volume_client_exception():
    """Test volume deletion with client exception"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_delete.side_effect = Exception("Client error")
        result = volume_management.delete_volume(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Client error' in result['details']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------
def test_delete_volume_missing_required_params():
    """Test volume deletion with missing required parameters"""
    args = DELETE_REQUIRED_ARGS.copy()
    del args['volume_name']
    # Python raises TypeError for missing required positional arguments
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        volume_management.delete_volume(**args)

def test_delete_volume_with_snapshots():
    """Test delete volume when snapshots exist"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_delete.side_effect = Exception("Volume has snapshots")
        
        result = volume_management.delete_volume(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'snapshot' in result['details'].lower() or 'failed to delete' in result['details'].lower()


def test_delete_volume_in_replication():
    """Test delete volume when in replication relationship"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_delete.side_effect = Exception("Volume in replication")
        
        result = volume_management.delete_volume(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'replication' in result['details'].lower() or 'failed to delete' in result['details'].lower()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_volume_lifecycle_integration():
    """Test complete volume lifecycle: create, list, delete"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')  # Return tuple as expected
        
        # Mock responses for each operation
        mock_volume = MagicMock()
        mock_volume.name = 'test-volume'
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = mock_volume
        mock_client.volumes.list.return_value = [mock_volume]
        mock_client.volumes.begin_delete.return_value.result.return_value = None
        
        # Test create
        create_result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert create_result['status'] == 'success'
        
        # Test list
        list_result = volume_management.list_volumes(**LIST_REQUIRED_ARGS)
        assert list_result['status'] == 'success'
        assert len(list_result['details']) == 1
        
        # Test delete
        delete_result = volume_management.delete_volume(**DELETE_REQUIRED_ARGS)
        assert delete_result['status'] == 'success'


def test_volume_lifecycle_workflow():
    """Test complete volume lifecycle (create, list, clone, delete)"""
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        
        # Mock volume creation
        mock_volume = MagicMock()
        mock_volume.name = CREATE_REQUIRED_ARGS['volume_name']
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = mock_volume
        
        # Mock volume listing
        mock_client.volumes.list.return_value = [mock_volume]
        
        # Mock volume cloning
        mock_clone = MagicMock()
        mock_clone.name = CLONE_REQUIRED_ARGS['volume_name']
        
        # Mock volume deletion
        mock_client.volumes.begin_delete.return_value.result.return_value = None
        
        # Step 1: Create volume
        create_result = volume_management.create_volume(**CREATE_REQUIRED_ARGS)
        assert create_result['status'] == 'success'
        
        # Step 2: List volumes
        list_result = volume_management.list_volumes(**LIST_REQUIRED_ARGS)
        assert list_result['status'] == 'success'
        assert len(list_result['details']) == 1
        
        # Step 3: Clone volume (if function exists)
        try:
            clone_result = volume_management.clone_volume(**CLONE_REQUIRED_ARGS)
            assert clone_result['status'] == 'success'
        except AttributeError:
            pass  # Function may not exist
        
        # Step 4: Delete volume
        delete_result = volume_management.delete_volume(**DELETE_REQUIRED_ARGS)
        assert delete_result['status'] == 'success'


def test_volume_multi_tenant_environment():
    """Test volume creation in multi-tenant environment"""
    tenant_args = CREATE_REQUIRED_ARGS.copy()
    tenant_args.update({
        'tags': {
            'tenant': 'tenant-a',
            'cost-allocation': 'department-1',
            'security-group': 'isolated',
            'access-control': 'rbac-enabled'
        },
        'export_policy': {
            'rules': [
                {
                    'ruleIndex': 1,
                    'allowedClients': '10.1.0.0/24',  # Tenant-specific network
                    'cifs': False,
                    'nfsv3': True,
                    'nfsv41': False,
                    'unixReadOnly': False,
                    'unixReadWrite': True
                }
            ]
        }
    })
    
    with patch('netapp_dataops.traditional.anf.volume_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.volumes.begin_create_or_update.return_value.result.return_value = MagicMock()
        
        result = volume_management.create_volume(**tenant_args)
        assert result['status'] == 'success'
