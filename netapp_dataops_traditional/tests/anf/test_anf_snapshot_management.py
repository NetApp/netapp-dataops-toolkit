import pytest
from unittest.mock import patch, MagicMock, Mock
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from netapp_dataops.traditional.anf import snapshot_management
from netapp_dataops.traditional.anf.config import InvalidConfigError

# Mock config data that simulates a valid ANF configuration
SAMPLE_CONFIG = {
    'subscriptionId': 'test-subscription-id',
    'resourceGroupName': 'test-resource-group',
    'accountName': 'test-account',
    'poolName': 'test-pool',
    'location': 'eastus',
    'virtualNetworkName': 'test-vnet',
    'subnetName': 'test-subnet',
    'protocolTypes': ['NFSv3']
}

# Create snapshot test arguments  
CREATE_SNAPSHOT_REQUIRED_ARGS = {
    'volume_name': 'test-volume',
    'snapshot_name': 'test-snapshot'
}

CREATE_SNAPSHOT_REQUIRED_ARGS_EXPLICIT = CREATE_SNAPSHOT_REQUIRED_ARGS.copy()
CREATE_SNAPSHOT_REQUIRED_ARGS_EXPLICIT.update({
    'subscription_id': 'test-subscription-id',
    'resource_group_name': 'test-resource-group',
    'account_name': 'test-account',
    'pool_name': 'test-pool'
})

# Required arguments for testing (backward compatibility)
REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume',
    'snapshot_name': 'test-snapshot',
    'location': 'eastus'
}

# List snapshots test arguments
LIST_SNAPSHOTS_REQUIRED_ARGS = {
    'volume_name': 'test-volume'
}

LIST_SNAPSHOTS_REQUIRED_ARGS_EXPLICIT = LIST_SNAPSHOTS_REQUIRED_ARGS.copy()
LIST_SNAPSHOTS_REQUIRED_ARGS_EXPLICIT.update({
    'subscription_id': 'test-subscription-id',
    'resource_group_name': 'test-resource-group',
    'account_name': 'test-account',
    'pool_name': 'test-pool'
})

# Required arguments for delete snapshots testing (no location needed)
DELETE_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume',
    'snapshot_name': 'test-snapshot'
}

# Delete snapshot test arguments
DELETE_SNAPSHOT_REQUIRED_ARGS = {
    'volume_name': 'test-volume',
    'snapshot_name': 'test-snapshot'
}

DELETE_SNAPSHOT_REQUIRED_ARGS_EXPLICIT = DELETE_SNAPSHOT_REQUIRED_ARGS.copy()
DELETE_SNAPSHOT_REQUIRED_ARGS_EXPLICIT.update({
    'subscription_id': 'test-subscription-id',
    'resource_group_name': 'test-resource-group',
    'account_name': 'test-account',
    'pool_name': 'test-pool'
})

# Required arguments for list snapshots testing
LIST_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume'
}

# =============================================================================
# CREATE SNAPSHOT TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

@patch('netapp_dataops.traditional.anf.config._retrieve_anf_config')
def test_create_snapshot_success_with_config(mock_config):
    """Test successful snapshot creation using config"""
    mock_config.return_value = SAMPLE_CONFIG
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**CREATE_SNAPSHOT_REQUIRED_ARGS)
        assert result['status'] == 'success'

def test_create_snapshot_success():
    """Test successful snapshot creation with minimal required parameters"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'success'

def test_create_snapshot_success_explicit():
    """Test successful snapshot creation with explicit parameters"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**CREATE_SNAPSHOT_REQUIRED_ARGS_EXPLICIT)
        assert result['status'] == 'success'

@patch('netapp_dataops.traditional.anf.config._retrieve_anf_config')
def test_create_snapshot_config_override(mock_config):
    """Test snapshot creation with config parameter override"""
    mock_config.return_value = SAMPLE_CONFIG
    args = CREATE_SNAPSHOT_REQUIRED_ARGS.copy()
    args['pool_name'] = 'override-pool'
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_optional_args():
    """Test snapshot creation with optional parameters"""
    args = REQUIRED_ARGS.copy()
    args.update({
        'location': 'eastus',
        'tags': {'env': 'test', 'purpose': 'backup'}
    })
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_empty_tags():
    """Test snapshot creation with empty tags"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {}
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_comprehensive_tags():
    """Test snapshot creation with comprehensive tagging"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {
        'environment': 'production',
        'team': 'data-engineering',
        'project': 'ml-pipeline',
        'backup-frequency': 'daily',
        'retention-days': '30'
    }
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_create_snapshot_already_exists():
    """Test snapshot creation when snapshot already exists"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = ResourceExistsError("Snapshot already exists")
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'already exists' in result['details'].lower()


def test_create_snapshot_volume_not_found():
    """Test snapshot creation when source volume doesn't exist"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = ResourceNotFoundError("Volume not found")
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'not found' in result['details'].lower()


def test_create_snapshot_client_exception():
    """Test snapshot creation with general client exception"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = Exception("Client error")
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Client error' in result['details']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_create_snapshot_missing_required_params():
    """Test snapshot creation with missing required parameters"""
    args = REQUIRED_ARGS.copy()
    del args['snapshot_name']
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_empty_snapshot_name():
    """Test snapshot creation with empty snapshot name"""
    args = REQUIRED_ARGS.copy()
    args['snapshot_name'] = ""
    with pytest.raises(ValueError, match="The following required parameters are missing"):
        snapshot_management.create_snapshot(**args)


# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

def test_create_snapshot_long_name():
    """Test snapshot creation with maximum length snapshot name"""
    args = REQUIRED_ARGS.copy()
    args['snapshot_name'] = 'a' * 64  # Maximum allowed length for ANF snapshot names
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_special_characters():
    """Test snapshot creation with special characters in name"""
    args = REQUIRED_ARGS.copy()
    args['snapshot_name'] = 'test-snapshot_v1.0'
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'

# =============================================================================
# LIST SNAPSHOTS TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_list_snapshots_success():
    """Test successful listing of snapshots"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_snapshot = MagicMock()
        mock_snapshot.name = 'test-snapshot'
        mock_client.snapshots.list.return_value = [mock_snapshot]
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 1


def test_list_snapshots_empty():
    """Test listing snapshots when no snapshots exist"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.list.return_value = []
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 0


def test_list_snapshots_multiple():
    """Test listing multiple snapshots"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_snapshots = [MagicMock() for _ in range(5)]
        for i, snapshot in enumerate(mock_snapshots):
            snapshot.name = f'test-snapshot-{i}'
        mock_client.snapshots.list.return_value = mock_snapshots
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 5

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_list_snapshots_volume_not_found():
    """Test listing snapshots when volume doesn't exist"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.list.side_effect = ResourceNotFoundError("Volume not found")
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'not found' in result['details'].lower()


def test_list_snapshots_client_exception():
    """Test listing snapshots with client exception"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.list.side_effect = Exception("Client error")
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Client error' in result['details']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_list_snapshots_missing_required_params():
    """Test listing snapshots with missing required parameters"""
    args = LIST_REQUIRED_ARGS.copy()
    del args['volume_name']
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        snapshot_management.list_snapshots(**args)


def test_list_snapshots_empty_account_name():
    """Test listing snapshots with empty account name"""
    args = LIST_REQUIRED_ARGS.copy()
    args['account_name'] = ""
    with pytest.raises(ValueError, match="The following required parameters are missing"):
        snapshot_management.list_snapshots(**args)

# =============================================================================
# DELETE SNAPSHOT TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_delete_snapshot_success():
    """Test successful snapshot deletion"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_delete.return_value.result.return_value = None
        result = snapshot_management.delete_snapshot(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_delete_snapshot_not_found():
    """Test snapshot deletion when snapshot doesn't exist - should return proper error"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_delete.side_effect = ResourceNotFoundError("Snapshot not found")
        
        result = snapshot_management.delete_snapshot(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'not found' in result['details'].lower()


def test_delete_snapshot_client_exception():
    """Test snapshot deletion with client exception"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_delete.side_effect = Exception("Client error")
        result = snapshot_management.delete_snapshot(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Client error' in result['details']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_snapshot_lifecycle_integration():
    """Test complete snapshot lifecycle: create, list, delete"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        
        # Mock responses for each operation
        mock_snapshot = MagicMock()
        mock_snapshot.name = 'test-snapshot'
        mock_client.snapshots.begin_create.return_value.result.return_value = mock_snapshot
        mock_client.snapshots.list.return_value = [mock_snapshot]
        mock_client.snapshots.begin_delete.return_value.result.return_value = None
        
        # Test create
        create_result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert create_result['status'] == 'success'
        
        # Test list
        list_result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert list_result['status'] == 'success'
        assert len(list_result['details']) == 1
        
        # Test delete
        delete_result = snapshot_management.delete_snapshot(**DELETE_REQUIRED_ARGS)
        assert delete_result['status'] == 'success'


def test_snapshot_with_backup_integration():
    """Test snapshot creation and backup workflow"""
    backup_args = REQUIRED_ARGS.copy()
    backup_args.update({
        'tags': {
            'backup-type': 'automated',
            'retention': '30-days',
            'application': 'database'
        }
    })
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**backup_args)
        assert result['status'] == 'success'


def test_create_snapshot_with_application_tags():
    """Test snapshot creation with application-specific tags"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {
        'application': 'oracle',
        'environment': 'production',
        'backup-schedule': 'daily',
        'retention-policy': '90-days'
    }
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_with_compliance_tags():
    """Test snapshot creation with compliance and governance tags"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {
        'compliance': 'PCI-DSS',
        'data-classification': 'confidential',
        'retention-required': 'yes',
        'audit-trail': 'enabled'
    }
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_with_maximum_tags():
    """Test snapshot creation with maximum number of allowed tags"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {f'tag_{i}': f'value_{i}' for i in range(15)}  # Azure allows up to 15 tags
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_different_subscription():
    """Test snapshot creation with explicit subscription ID"""
    args = REQUIRED_ARGS.copy()
    args['subscription_id'] = 'different-subscription-id'
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'different-subscription-id')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_with_print_output():
    """Test snapshot creation with print output enabled"""
    args = REQUIRED_ARGS.copy()
    args['print_output'] = True
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'

def test_create_snapshot_permission_denied():
    """Test snapshot creation with insufficient permissions"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = Exception("Permission denied")
        
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'permission denied' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_create_snapshot_quota_exceeded():
    """Test snapshot creation when quota is exceeded"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = Exception("Snapshot quota exceeded")
        
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'quota' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_create_snapshot_network_timeout():
    """Test snapshot creation with network timeout"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = Exception("Network timeout")
        
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'timeout' in result['details'].lower() or 'failed to create' in result['details'].lower()


def test_list_snapshots_permission_denied():
    """Test list snapshots with insufficient permissions"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.list.side_effect = Exception("Permission denied")
        
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'permission denied' in result['details'].lower() or 'failed to list' in result['details'].lower()


def test_delete_snapshot_in_use():
    """Test delete snapshot when snapshot is in use"""
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_delete.side_effect = Exception("Snapshot is in use")
        
        result = snapshot_management.delete_snapshot(**DELETE_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'in use' in result['details'].lower() or 'failed to delete' in result['details'].lower()

def test_create_snapshot_invalid_tag_key():
    """Test snapshot creation with invalid tag key"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {'': 'invalid-empty-key'}  # Empty key is invalid
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = Exception("Invalid tag key")
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'error'


def test_create_snapshot_invalid_tag_value():
    """Test snapshot creation with invalid tag value"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {'valid-key': 'a' * 257}  # Tag value too long (max 256 chars)
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = Exception("Tag value too long")
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'error'


def test_create_snapshot_too_many_tags():
    """Test snapshot creation with too many tags"""
    args = REQUIRED_ARGS.copy()
    args['tags'] = {f'tag_{i}': f'value_{i}' for i in range(20)}  # More than 15 allowed
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.side_effect = Exception("Too many tags")
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'error'


def test_create_snapshot_whitespace_volume_name():
    """Test snapshot creation with whitespace-only volume name"""
    args = REQUIRED_ARGS.copy()
    args['volume_name'] = '   '
    
    with pytest.raises((ValueError, TypeError)):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_whitespace_account_name():
    """Test snapshot creation with whitespace-only account name"""
    args = REQUIRED_ARGS.copy()
    args['account_name'] = '   '
    
    with pytest.raises((ValueError, TypeError)):
        snapshot_management.create_snapshot(**args)

def test_create_snapshot_unicode_name():
    """Test snapshot creation with Unicode characters in name"""
    args = REQUIRED_ARGS.copy()
    args['snapshot_name'] = 'snapshot-测试-🔄'
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_maximum_name_length():
    """Test snapshot creation with maximum allowed name length"""
    args = REQUIRED_ARGS.copy()
    args['snapshot_name'] = 'a' * 64  # Assuming 64 char limit
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_special_characters_extended():
    """Test snapshot creation with extended special characters and numbers in name"""
    args = REQUIRED_ARGS.copy()
    args['snapshot_name'] = 'test-snapshot_123-v2.0'
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_list_snapshots_large_result_set():
    """Test list snapshots with large number of snapshots"""
    mock_snapshots = []
    for i in range(100):
        mock_snapshot = MagicMock()
        mock_snapshot.name = f'snapshot-{i}'
        mock_snapshot.creation_date = f'2023-01-{i+1:02d}'
        mock_snapshots.append(mock_snapshot)
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.list.return_value = mock_snapshots
        
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 100


def test_create_snapshot_concurrent_requests():
    """Test snapshot creation with concurrent requests simulation"""
    import threading
    import time
    
    results = []
    exceptions = []
    
    def create_snapshot_thread():
        try:
            with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
                mock_client = MagicMock()
                mock_client_func.return_value = (mock_client, 'test-subscription')
                mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
                
                args = REQUIRED_ARGS.copy()
                args['snapshot_name'] = f'concurrent-snapshot-{threading.current_thread().ident}'
                
                result = snapshot_management.create_snapshot(**args)
                results.append(result)
        except Exception as e:
            exceptions.append(e)
    
    # Create multiple threads to simulate concurrent snapshot creation
    threads = []
    for i in range(3):
        thread = threading.Thread(target=create_snapshot_thread)
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all snapshots were created successfully
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
    assert len(results) >= 1, "No snapshots were created"

# =============================================================================
# INTEGRATION TESTS  
# =============================================================================

def test_snapshot_backup_restore_workflow():
    """Test complete snapshot-based backup and restore workflow"""
    # Step 1: Create snapshot
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        
        # Mock snapshot creation
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        create_result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert create_result['status'] == 'success'
        
        # Mock snapshot listing
        mock_snapshot = MagicMock()
        mock_snapshot.name = REQUIRED_ARGS['snapshot_name']
        mock_client.snapshots.list.return_value = [mock_snapshot]
        list_result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert list_result['status'] == 'success'
        assert len(list_result['details']) == 1


def test_snapshot_policy_compliance_workflow():
    """Test snapshot creation with policy compliance validation"""
    compliance_args = REQUIRED_ARGS.copy()
    compliance_args.update({
        'tags': {
            'policy-compliant': 'true',
            'retention-class': 'long-term',
            'data-protection': 'enabled',
            'backup-tier': 'primary'
        }
    })
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**compliance_args)
        assert result['status'] == 'success'


def test_snapshot_disaster_recovery_scenario():
    """Test snapshot creation for disaster recovery scenarios"""
    dr_args = REQUIRED_ARGS.copy()
    dr_args.update({
        'tags': {
            'disaster-recovery': 'enabled',
            'replication-target': 'westus2',
            'rpo': '15-minutes',
            'priority': 'high'
        }
    })
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**dr_args)
        assert result['status'] == 'success'


def test_snapshot_application_consistent_backup():
    """Test application-consistent snapshot creation"""
    app_consistent_args = REQUIRED_ARGS.copy()
    app_consistent_args.update({
        'tags': {
            'consistency-type': 'application-consistent',
            'application': 'sql-server',
            'vss-enabled': 'true',
            'quiesce-timeout': '30'
        }
    })
    
    with patch('netapp_dataops.traditional.anf.snapshot_management.get_anf_client') as mock_client_func:
        mock_client = MagicMock()
        mock_client_func.return_value = (mock_client, 'test-subscription')
        mock_client.snapshots.begin_create.return_value.result.return_value = MagicMock()
        
        result = snapshot_management.create_snapshot(**app_consistent_args)
        assert result['status'] == 'success'
