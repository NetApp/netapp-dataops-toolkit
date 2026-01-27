import pytest
from unittest.mock import patch, MagicMock
from netapp_dataops.traditional.gcnv import replication_management

# Required arguments for testing
REQUIRED_ARGS = {
    'source_project_id': 'proj',
    'source_location': 'us-central1',
    'source_volume_id': 'vol1',
    'replication_id': 'rep1',
    'replication_schedule': 'HOURLY',
    'destination_storage_pool': 'projects/proj/locations/us-central1/storagePools/pool1'
}

# =============================================================================
# CREATE REPLICATION TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_create_replication_success():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(**REQUIRED_ARGS)
        assert result['status'] == 'success'


def test_create_replication_optional_args():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(
            **REQUIRED_ARGS,
            destination_volume_id='dest-vol',
            destination_share_name='dest-share',
            destination_volume_description='Destination volume',
            description='Test replication',
            labels={'env': 'test'},
            tiering_enabled=True,
            cooling_threshold_days=90
        )
        assert result['status'] == 'success'


def test_create_replication_minimal_optional_args():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(
            **REQUIRED_ARGS,
            description='Minimal test',
            labels={}
        )
        assert result['status'] == 'success'


def test_create_replication_tiering_without_threshold():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(
            **REQUIRED_ARGS,
            tiering_enabled=True,
            cooling_threshold_days=None
        )
        assert result['status'] == 'success'


def test_create_replication_none_optional_args():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(
            **REQUIRED_ARGS,
            destination_volume_id=None,
            destination_share_name=None,
            destination_volume_description=None,
            description=None,
            labels=None,
            tiering_enabled=None,
            cooling_threshold_days=None
        )
        assert result['status'] == 'success'

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_create_replication_api_failure():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.side_effect = Exception('Replication API error')
        result = replication_management.create_replication(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Replication API error' in result['message']


def test_create_replication_source_volume_not_found():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.side_effect = Exception('Source volume not found')
        result = replication_management.create_replication(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Source volume not found' in result['message']


def test_create_replication_destination_pool_not_found():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.side_effect = Exception('Destination storage pool not found')
        result = replication_management.create_replication(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Destination storage pool not found' in result['message']


def test_create_replication_region_pair_unsupported():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.side_effect = Exception('Unsupported region pair for replication')
        result = replication_management.create_replication(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Unsupported region pair for replication' in result['message']


def test_create_replication_unexpected_exception():
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client', side_effect=Exception('Unexpected error')):
        result = replication_management.create_replication(**REQUIRED_ARGS)
        assert result['status'] == 'error'
        assert 'Unexpected error' in result['message']

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_create_replication_missing_source_project_id():
    args = REQUIRED_ARGS.copy()
    args['source_project_id'] = None
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_missing_source_location():
    args = REQUIRED_ARGS.copy()
    args['source_location'] = None
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_missing_source_volume_id():
    args = REQUIRED_ARGS.copy()
    args['source_volume_id'] = None
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_missing_replication_id():
    args = REQUIRED_ARGS.copy()
    args['replication_id'] = None
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_missing_replication_schedule():
    args = REQUIRED_ARGS.copy()
    args['replication_schedule'] = None
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_missing_destination_storage_pool():
    args = REQUIRED_ARGS.copy()
    args['destination_storage_pool'] = None
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_empty_source_project_id():
    args = REQUIRED_ARGS.copy()
    args['source_project_id'] = ''
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_empty_source_location():
    args = REQUIRED_ARGS.copy()
    args['source_location'] = ''
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_empty_source_volume_id():
    args = REQUIRED_ARGS.copy()
    args['source_volume_id'] = ''
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_empty_replication_id():
    args = REQUIRED_ARGS.copy()
    args['replication_id'] = ''
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_empty_replication_schedule():
    args = REQUIRED_ARGS.copy()
    args['replication_schedule'] = ''
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_empty_destination_storage_pool():
    args = REQUIRED_ARGS.copy()
    args['destination_storage_pool'] = ''
    with pytest.raises(ValueError):
        replication_management.create_replication(**args)


def test_create_replication_whitespace_source_project_id():
    args = REQUIRED_ARGS.copy()
    args['source_project_id'] = '   '
    result = replication_management.create_replication(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_replication_whitespace_source_location():
    args = REQUIRED_ARGS.copy()
    args['source_location'] = '   '
    result = replication_management.create_replication(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_replication_whitespace_source_volume_id():
    args = REQUIRED_ARGS.copy()
    args['source_volume_id'] = '   '
    result = replication_management.create_replication(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_replication_whitespace_replication_id():
    args = REQUIRED_ARGS.copy()
    args['replication_id'] = '   '
    result = replication_management.create_replication(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_replication_whitespace_replication_schedule():
    args = REQUIRED_ARGS.copy()
    args['replication_schedule'] = '   '
    result = replication_management.create_replication(**args)
    assert result['status'] == 'error'
    assert "'   '" in result['message']


def test_create_replication_whitespace_destination_storage_pool():
    args = REQUIRED_ARGS.copy()
    args['destination_storage_pool'] = '   '
    result = replication_management.create_replication(**args)
    assert result['status'] == 'error'
    assert 'Permission denied' in result['message']


def test_create_replication_wrong_labels_type():
    with pytest.raises(ValueError):
        replication_management.create_replication(
            **REQUIRED_ARGS,
            labels='not_a_dict'
        )

# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

def test_create_replication_long_replication_id():
    long_id = 'r' * 256
    args = REQUIRED_ARGS.copy()
    args['replication_id'] = long_id
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(**args)
        assert result['status'] == 'success'


def test_create_replication_long_description():
    long_description = 'desc' * 500
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(
            **REQUIRED_ARGS,
            description=long_description
        )
        assert result['status'] == 'success'


def test_create_replication_special_char_id():
    special_id = 'rep!@#'
    args = REQUIRED_ARGS.copy()
    args['replication_id'] = special_id
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(**args)
        assert result['status'] == 'success'


def test_create_replication_unicode_characters():
    unicode_id = 'rëp-tëst-ünïcödé'
    args = REQUIRED_ARGS.copy()
    args['replication_id'] = unicode_id
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(**args)
        assert result['status'] == 'success'


def test_create_replication_max_labels():
    # Google Cloud allows up to 64 labels
    max_labels = {f'key{i}': f'value{i}' for i in range(64)}
    with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.create_replication.return_value.result.return_value = MagicMock()
        result = replication_management.create_replication(
            **REQUIRED_ARGS,
            labels=max_labels
        )
        assert result['status'] == 'success'


def test_create_replication_different_schedules():
    # Only test valid replication schedules based on API documentation
    schedules = ['HOURLY', 'DAILY']  # WEEKLY and MONTHLY may not be supported by API
    for schedule in schedules:
        args = REQUIRED_ARGS.copy()
        args['replication_id'] = f'rep-{schedule.lower()}'
        args['replication_schedule'] = schedule
        with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.create_replication.return_value.result.return_value = MagicMock()
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'


def test_create_replication_invalid_schedules():
    # Test invalid replication schedules
    invalid_schedules = ['WEEKLY', 'MONTHLY', 'INVALID_SCHEDULE']
    for schedule in invalid_schedules:
        args = REQUIRED_ARGS.copy()
        args['replication_id'] = f'rep-{schedule.lower()}'
        args['replication_schedule'] = schedule
        result = replication_management.create_replication(**args)
        assert result['status'] == 'error'
        assert schedule in result['message']


def test_create_replication_boundary_cooling_threshold():
    boundary_values = [2, 31, 183]  # Min, default, max
    for threshold in boundary_values:
        with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.create_replication.return_value.result.return_value = MagicMock()
            result = replication_management.create_replication(
                **REQUIRED_ARGS,
                tiering_enabled=True,
                cooling_threshold_days=threshold
            )
            assert result['status'] == 'success'


def test_create_replication_cross_region_pools():
    """Test replication with cross-region destination storage pools"""
    cross_region_pools = [
        'projects/proj/locations/europe-west2/storagePools/pool1',
        'projects/proj/locations/asia-southeast1/storagePools/pool1',
        'projects/proj/locations/us-west2/storagePools/pool1'
    ]
    for pool in cross_region_pools:
        args = REQUIRED_ARGS.copy()
        args['replication_id'] = 'cross-region-rep'
        args['replication_schedule'] = 'DAILY'
        args['destination_storage_pool'] = pool
        with patch('netapp_dataops.traditional.gcnv.replication_management.create_client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            mock_instance.create_replication.return_value.result.return_value = MagicMock()
            result = replication_management.create_replication(**args)
            assert result['status'] == 'success'
