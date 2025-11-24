import pytest
from unittest.mock import patch, MagicMock
from netapp_dataops.traditional.gcnv import snapshot_management

# Required arguments for testing
REQUIRED_ARGS = {
    'project_id': 'proj',
    'location': 'us-central1',
    'volume_id': 'vol1',
    'snapshot_id': 'snap1'
}

# Required arguments for list snapshots testing
LIST_REQUIRED_ARGS = {
    'project_id': 'proj',
    'location': 'us-central1',
    'volume_id': 'vol1'
}

# =============================================================================
# CREATE SNAPSHOT TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_create_snapshot_success():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'success'


def test_create_snapshot_optional_args():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(
            **REQUIRED_ARGS, description='Test description', labels={'env': 'test'})
        assert result['status'] == 'success'


def test_create_snapshot_empty_labels():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(
            **REQUIRED_ARGS, labels={})
        assert result['status'] == 'success'


def test_create_snapshot_none_optional_args():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(
            **REQUIRED_ARGS, description=None, labels=None)
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_create_snapshot_api_failure():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.side_effect = Exception('Snapshot API error')
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Snapshot API error' in result['message']


def test_create_snapshot_unexpected_exception():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client', side_effect=Exception('Unexpected error')):
        result = snapshot_management.create_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Unexpected error' in result['message']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_create_snapshot_missing_project_id():
    args = REQUIRED_ARGS.copy()
    args['project_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_missing_location():
    args = REQUIRED_ARGS.copy()
    args['location'] = None
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_missing_volume_id():
    args = REQUIRED_ARGS.copy()
    args['volume_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_missing_snapshot_id():
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_empty_project_id():
    args = REQUIRED_ARGS.copy()
    args['project_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_empty_location():
    args = REQUIRED_ARGS.copy()
    args['location'] = ''
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_empty_volume_id():
    args = REQUIRED_ARGS.copy()
    args['volume_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_empty_snapshot_id():
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.create_snapshot(**args)


def test_create_snapshot_whitespace_project_id():
    args = REQUIRED_ARGS.copy()
    args['project_id'] = '   '
    result = snapshot_management.create_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_snapshot_whitespace_location():
    args = REQUIRED_ARGS.copy()
    args['location'] = '   '
    result = snapshot_management.create_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_snapshot_whitespace_volume_id():
    args = REQUIRED_ARGS.copy()
    args['volume_id'] = '   '
    result = snapshot_management.create_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_snapshot_whitespace_snapshot_id():
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = '   '
    result = snapshot_management.create_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_snapshot_wrong_labels_type():
    with pytest.raises(Exception):
        snapshot_management.create_snapshot(
            **REQUIRED_ARGS, labels='not_a_dict')

# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

def test_create_snapshot_long_id():
    long_id = 's' * 256
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = long_id
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_long_description():
    long_description = 'desc' * 500
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(
            **REQUIRED_ARGS, description=long_description)
        assert result['status'] == 'success'


def test_create_snapshot_special_char_id():
    special_id = 'snap!@#'
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = special_id
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_unicode_characters():
    unicode_id = 'snäp-tëst-ünïcödé'
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = unicode_id
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(**args)
        assert result['status'] == 'success'


def test_create_snapshot_max_labels():
    # Google Cloud allows up to 64 labels
    max_labels = {f'key{i}': f'value{i}' for i in range(64)}
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.create_snapshot(
            **REQUIRED_ARGS, labels=max_labels)
        assert result['status'] == 'success'

# =============================================================================
# DELETE SNAPSHOT TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_delete_snapshot_success():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.delete_snapshot.return_value.result.return_value = MagicMock()
        result = snapshot_management.delete_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_delete_snapshot_api_failure():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.delete_snapshot.side_effect = Exception('Delete snapshot error')
        result = snapshot_management.delete_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Delete snapshot error' in result['message']


def test_delete_snapshot_not_found():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.delete_snapshot.side_effect = Exception('Snapshot not found')
        result = snapshot_management.delete_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Snapshot not found' in result['message']


def test_delete_snapshot_unexpected_exception():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client', side_effect=Exception('Unexpected error')):
        result = snapshot_management.delete_snapshot(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Unexpected error' in result['message']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_delete_snapshot_missing_project_id():
    args = REQUIRED_ARGS.copy()
    args['project_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_missing_location():
    args = REQUIRED_ARGS.copy()
    args['location'] = None
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_missing_volume_id():
    args = REQUIRED_ARGS.copy()
    args['volume_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_missing_snapshot_id():
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_empty_project_id():
    args = REQUIRED_ARGS.copy()
    args['project_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_empty_location():
    args = REQUIRED_ARGS.copy()
    args['location'] = ''
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_empty_volume_id():
    args = REQUIRED_ARGS.copy()
    args['volume_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_empty_snapshot_id():
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.delete_snapshot(**args)


def test_delete_snapshot_whitespace_project_id():
    args = REQUIRED_ARGS.copy()
    args['project_id'] = '   '
    result = snapshot_management.delete_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_delete_snapshot_whitespace_location():
    args = REQUIRED_ARGS.copy()
    args['location'] = '   '
    result = snapshot_management.delete_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_delete_snapshot_whitespace_volume_id():
    args = REQUIRED_ARGS.copy()
    args['volume_id'] = '   '
    result = snapshot_management.delete_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_delete_snapshot_whitespace_snapshot_id():
    args = REQUIRED_ARGS.copy()
    args['snapshot_id'] = '   '
    result = snapshot_management.delete_snapshot(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']

# =============================================================================
# LIST SNAPSHOTS TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_list_snapshots_success():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.list_snapshots.return_value = [MagicMock()]
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'


def test_list_snapshots_multiple():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.list_snapshots.return_value = [MagicMock(), MagicMock()]
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) >= 2


def test_list_snapshots_empty():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.list_snapshots.return_value = []
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'success'
        assert len(result['details']) == 0

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_list_snapshots_api_failure():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.list_snapshots.side_effect = Exception('List snapshots error')
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'List snapshots error' in result['message']


def test_list_snapshots_volume_not_found():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.list_snapshots.side_effect = Exception('Volume not found')
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Volume not found' in result['message']


def test_list_snapshots_unexpected_exception():
    with patch('netapp_dataops.traditional.gcnv.snapshot_management.create_client', side_effect=Exception('Unexpected error')):
        result = snapshot_management.list_snapshots(**LIST_REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Unexpected error' in result['message']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_list_snapshots_missing_project_id():
    args = LIST_REQUIRED_ARGS.copy()
    args['project_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.list_snapshots(**args)


def test_list_snapshots_missing_location():
    args = LIST_REQUIRED_ARGS.copy()
    args['location'] = None
    with pytest.raises(ValueError):
        snapshot_management.list_snapshots(**args)


def test_list_snapshots_missing_volume_id():
    args = LIST_REQUIRED_ARGS.copy()
    args['volume_id'] = None
    with pytest.raises(ValueError):
        snapshot_management.list_snapshots(**args)


def test_list_snapshots_empty_project_id():
    args = LIST_REQUIRED_ARGS.copy()
    args['project_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.list_snapshots(**args)


def test_list_snapshots_empty_location():
    args = LIST_REQUIRED_ARGS.copy()
    args['location'] = ''
    with pytest.raises(ValueError):
        snapshot_management.list_snapshots(**args)


def test_list_snapshots_empty_volume_id():
    args = LIST_REQUIRED_ARGS.copy()
    args['volume_id'] = ''
    with pytest.raises(ValueError):
        snapshot_management.list_snapshots(**args)


def test_list_snapshots_whitespace_project_id():
    args = LIST_REQUIRED_ARGS.copy()
    args['project_id'] = '   '
    result = snapshot_management.list_snapshots(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_list_snapshots_whitespace_location():
    args = LIST_REQUIRED_ARGS.copy()
    args['location'] = '   '
    result = snapshot_management.list_snapshots(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_list_snapshots_whitespace_volume_id():
    args = LIST_REQUIRED_ARGS.copy()
    args['volume_id'] = '   '
    result = snapshot_management.list_snapshots(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']
