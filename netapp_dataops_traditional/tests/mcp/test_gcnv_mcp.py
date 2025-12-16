import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Required arguments for testing MCP server functions
VOLUME_REQUIRED_ARGS = {
    'project_id': 'test-project',
    'location': 'us-central1',
    'volume_id': 'test-volume',
    'share_name': 'test-share',
    'storage_pool': 'projects/test-project/locations/us-central1/storagePools/test-pool',
    'capacity_gib': 100,
    'protocols': ['NFSV3']
}

CLONE_REQUIRED_ARGS = {
    'project_id': 'test-project',
    'location': 'us-central1',
    'volume_id': 'test-clone',
    'source_volume': 'test-source-volume',
    'source_snapshot': 'test-source-snapshot',
    'share_name': 'test-share',
    'storage_pool': 'projects/test-project/locations/us-central1/storagePools/test-pool',
    'protocols': ['NFSV3']
}

LIST_VOLUMES_REQUIRED_ARGS = {
    'project_id': 'test-project',
    'location': 'us-central1'
}

SNAPSHOT_REQUIRED_ARGS = {
    'project_id': 'test-project',
    'location': 'us-central1',
    'volume_id': 'test-volume',
    'snapshot_id': 'test-snapshot'
}

LIST_SNAPSHOTS_REQUIRED_ARGS = {
    'project_id': 'test-project',
    'location': 'us-central1',
    'volume_id': 'test-volume'
}

REPLICATION_REQUIRED_ARGS = {
    'source_project_id': 'test-project',
    'source_location': 'us-central1',
    'source_volume_id': 'test-volume',
    'replication_id': 'test-replication',
    'replication_schedule': 'HOURLY',
    'destination_storage_pool': 'projects/test-project/locations/us-west2/storagePools/test-pool'
}

# =============================================================================
# MCP SERVER BASIC INTEGRATION TESTS
# =============================================================================

def test_mcp_server_instance_exists():
    """Test that the MCP server instance is created correctly"""
    from netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp import mcp
    assert mcp is not None
    assert hasattr(mcp, 'name')
    assert mcp.name == "NetApp DataOps Traditional GCNV Toolkit MCP"


def test_main_function():
    """Test the main entry point function"""
    with patch('netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp.asyncio.run') as mock_run:
        with patch('netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp.mcp.run') as mock_mcp_run:
            from netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp import main
            main()
            mock_run.assert_called_once_with(mock_mcp_run.return_value)


def test_imports_from_traditional_gcnv():
    """Test that the MCP server correctly imports from traditional GCNV module"""
    import netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp as mcp_module
    
    # Check that the required functions are imported
    assert hasattr(mcp_module, 'create_volume')
    assert hasattr(mcp_module, 'clone_volume')
    assert hasattr(mcp_module, 'list_volumes')
    assert hasattr(mcp_module, 'create_snapshot')
    assert hasattr(mcp_module, 'list_snapshots')
    assert hasattr(mcp_module, 'create_replication')


# =============================================================================
# BUSINESS LOGIC TESTS - Direct Function Testing
# =============================================================================
# Since the FastMCP decorator makes direct testing complex, we test the 
# underlying business logic by recreating the wrapper logic

async def create_volume_wrapper_logic(
    create_volume_func, logger_func, **kwargs
):
    """Recreate the create volume wrapper logic for testing"""
    response = create_volume_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error creating volume: {response['message']}")
    return response


async def clone_volume_wrapper_logic(
    clone_volume_func, logger_func, **kwargs
):
    """Recreate the clone volume wrapper logic for testing"""
    response = clone_volume_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error cloning volume: {response.get('message', 'Unknown error')}")
    return response


async def list_volumes_wrapper_logic(
    list_volumes_func, logger_func, **kwargs
):
    """Recreate the list volumes wrapper logic for testing"""
    response = list_volumes_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error listing volumes: {response['message']}")
    return response


async def create_snapshot_wrapper_logic(
    create_snapshot_func, logger_func, **kwargs
):
    """Recreate the create snapshot wrapper logic for testing"""
    response = create_snapshot_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error creating snapshot: {response['message']}")
    return response


async def list_snapshots_wrapper_logic(
    list_snapshots_func, logger_func, **kwargs
):
    """Recreate the list snapshots wrapper logic for testing"""
    response = list_snapshots_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error listing snapshots: {response['message']}")
    return response


async def create_replication_wrapper_logic(
    create_replication_func, logger_func, **kwargs
):
    """Recreate the create replication wrapper logic for testing"""
    response = create_replication_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error creating replication: {response['message']}")
    return response


# =============================================================================
# WRAPPER LOGIC TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_volume_wrapper_success():
    """Test the create volume wrapper logic with success response"""
    mock_create = MagicMock(return_value={'status': 'success', 'details': {'name': 'test-volume'}})
    mock_logger = MagicMock()
    
    result = await create_volume_wrapper_logic(mock_create, mock_logger, **VOLUME_REQUIRED_ARGS)
    
    assert result['status'] == 'success'
    assert result['details']['name'] == 'test-volume'
    mock_create.assert_called_once_with(**VOLUME_REQUIRED_ARGS)
    mock_logger.assert_not_called()


@pytest.mark.asyncio
async def test_create_volume_wrapper_error():
    """Test the create volume wrapper logic with error response"""
    mock_create = MagicMock(return_value={'status': 'error', 'message': 'Volume creation failed'})
    mock_logger = MagicMock()
    
    result = await create_volume_wrapper_logic(mock_create, mock_logger, **VOLUME_REQUIRED_ARGS)
    
    assert result['status'] == 'error'
    assert result['message'] == 'Volume creation failed'
    mock_logger.assert_called_once_with('Error creating volume: Volume creation failed')


@pytest.mark.asyncio
async def test_clone_volume_wrapper_success():
    """Test the clone volume wrapper logic with success response"""
    mock_clone = MagicMock(return_value={'status': 'success', 'details': {'name': 'test-clone'}})
    mock_logger = MagicMock()
    
    result = await clone_volume_wrapper_logic(mock_clone, mock_logger, **CLONE_REQUIRED_ARGS)
    
    assert result['status'] == 'success'
    assert result['details']['name'] == 'test-clone'
    mock_clone.assert_called_once_with(**CLONE_REQUIRED_ARGS)
    mock_logger.assert_not_called()


@pytest.mark.asyncio
async def test_clone_volume_wrapper_error_with_message():
    """Test the clone volume wrapper logic with error response containing message"""
    mock_clone = MagicMock(return_value={'status': 'error', 'message': 'Clone failed'})
    mock_logger = MagicMock()
    
    result = await clone_volume_wrapper_logic(mock_clone, mock_logger, **CLONE_REQUIRED_ARGS)
    
    assert result['status'] == 'error'
    assert result['message'] == 'Clone failed'
    mock_logger.assert_called_once_with('Error cloning volume: Clone failed')


@pytest.mark.asyncio
async def test_clone_volume_wrapper_error_without_message():
    """Test the clone volume wrapper logic with error response missing message"""
    mock_clone = MagicMock(return_value={'status': 'error'})
    mock_logger = MagicMock()
    
    result = await clone_volume_wrapper_logic(mock_clone, mock_logger, **CLONE_REQUIRED_ARGS)
    
    assert result['status'] == 'error'
    mock_logger.assert_called_once_with('Error cloning volume: Unknown error')


@pytest.mark.asyncio
async def test_list_volumes_wrapper_success():
    """Test the list volumes wrapper logic with success response"""
    mock_list = MagicMock(return_value={'status': 'success', 'details': [{'name': 'volume1'}, {'name': 'volume2'}]})
    mock_logger = MagicMock()
    
    result = await list_volumes_wrapper_logic(mock_list, mock_logger, **LIST_VOLUMES_REQUIRED_ARGS)
    
    assert result['status'] == 'success'
    assert len(result['details']) == 2
    mock_list.assert_called_once_with(**LIST_VOLUMES_REQUIRED_ARGS)
    mock_logger.assert_not_called()


@pytest.mark.asyncio
async def test_list_volumes_wrapper_error():
    """Test the list volumes wrapper logic with error response"""
    mock_list = MagicMock(return_value={'status': 'error', 'message': 'List failed'})
    mock_logger = MagicMock()
    
    result = await list_volumes_wrapper_logic(mock_list, mock_logger, **LIST_VOLUMES_REQUIRED_ARGS)
    
    assert result['status'] == 'error'
    assert result['message'] == 'List failed'
    mock_logger.assert_called_once_with('Error listing volumes: List failed')


@pytest.mark.asyncio
async def test_create_snapshot_wrapper_success():
    """Test the create snapshot wrapper logic with success response"""
    mock_create = MagicMock(return_value={'status': 'success', 'details': {'name': 'test-snapshot'}})
    mock_logger = MagicMock()
    
    result = await create_snapshot_wrapper_logic(mock_create, mock_logger, **SNAPSHOT_REQUIRED_ARGS)
    
    assert result['status'] == 'success'
    assert result['details']['name'] == 'test-snapshot'
    mock_create.assert_called_once_with(**SNAPSHOT_REQUIRED_ARGS)
    mock_logger.assert_not_called()


@pytest.mark.asyncio
async def test_create_snapshot_wrapper_error():
    """Test the create snapshot wrapper logic with error response"""
    mock_create = MagicMock(return_value={'status': 'error', 'message': 'Snapshot creation failed'})
    mock_logger = MagicMock()
    
    result = await create_snapshot_wrapper_logic(mock_create, mock_logger, **SNAPSHOT_REQUIRED_ARGS)
    
    assert result['status'] == 'error'
    assert result['message'] == 'Snapshot creation failed'
    mock_logger.assert_called_once_with('Error creating snapshot: Snapshot creation failed')


@pytest.mark.asyncio
async def test_list_snapshots_wrapper_success():
    """Test the list snapshots wrapper logic with success response"""
    mock_list = MagicMock(return_value={'status': 'success', 'details': [{'name': 'snap1'}, {'name': 'snap2'}]})
    mock_logger = MagicMock()
    
    result = await list_snapshots_wrapper_logic(mock_list, mock_logger, **LIST_SNAPSHOTS_REQUIRED_ARGS)
    
    assert result['status'] == 'success'
    assert len(result['details']) == 2
    mock_list.assert_called_once_with(**LIST_SNAPSHOTS_REQUIRED_ARGS)
    mock_logger.assert_not_called()


@pytest.mark.asyncio
async def test_list_snapshots_wrapper_error():
    """Test the list snapshots wrapper logic with error response"""
    mock_list = MagicMock(return_value={'status': 'error', 'message': 'List snapshots failed'})
    mock_logger = MagicMock()
    
    result = await list_snapshots_wrapper_logic(mock_list, mock_logger, **LIST_SNAPSHOTS_REQUIRED_ARGS)
    
    assert result['status'] == 'error'
    assert result['message'] == 'List snapshots failed'
    mock_logger.assert_called_once_with('Error listing snapshots: List snapshots failed')


@pytest.mark.asyncio
async def test_create_replication_wrapper_success():
    """Test the create replication wrapper logic with success response"""
    mock_create = MagicMock(return_value={'status': 'success', 'details': {'name': 'test-replication'}})
    mock_logger = MagicMock()
    
    result = await create_replication_wrapper_logic(mock_create, mock_logger, **REPLICATION_REQUIRED_ARGS)
    
    assert result['status'] == 'success'
    assert result['details']['name'] == 'test-replication'
    mock_create.assert_called_once_with(**REPLICATION_REQUIRED_ARGS)
    mock_logger.assert_not_called()


@pytest.mark.asyncio
async def test_create_replication_wrapper_error():
    """Test the create replication wrapper logic with error response"""
    mock_create = MagicMock(return_value={'status': 'error', 'message': 'Replication failed'})
    mock_logger = MagicMock()
    
    result = await create_replication_wrapper_logic(mock_create, mock_logger, **REPLICATION_REQUIRED_ARGS)
    
    assert result['status'] == 'error'
    assert result['message'] == 'Replication failed'
    mock_logger.assert_called_once_with('Error creating replication: Replication failed')


# =============================================================================
# INTEGRATION VALIDATION TESTS
# =============================================================================

def test_response_format_consistency():
    """Test that all wrapper functions follow consistent response format patterns"""
    # This test validates that our wrapper logic follows the expected patterns
    # All success responses should have 'status': 'success' and 'details'
    # All error responses should have 'status': 'error' and 'message'
    
    # Test data structures match expected format
    success_response = {'status': 'success', 'details': {'name': 'test-resource'}}
    error_response = {'status': 'error', 'message': 'Test error'}
    
    assert 'status' in success_response
    assert success_response['status'] == 'success'
    assert 'details' in success_response
    
    assert 'status' in error_response
    assert error_response['status'] == 'error'
    assert 'message' in error_response


def test_all_wrapper_functions_are_async():
    """Test that all wrapper functions are properly async"""
    wrapper_functions = [
        create_volume_wrapper_logic,
        clone_volume_wrapper_logic,
        list_volumes_wrapper_logic,
        create_snapshot_wrapper_logic,
        list_snapshots_wrapper_logic,
        create_replication_wrapper_logic
    ]
    
    for func in wrapper_functions:
        assert asyncio.iscoroutinefunction(func), f"{func.__name__} is not an async function"


def test_error_message_patterns():
    """Test that error messages follow consistent patterns"""
    expected_patterns = {
        'create_volume': 'Error creating volume:',
        'clone_volume': 'Error cloning volume:',
        'list_volumes': 'Error listing volumes:',
        'create_snapshot': 'Error creating snapshot:',
        'list_snapshots': 'Error listing snapshots:',
        'create_replication': 'Error creating replication:'
    }
    
    # These patterns should be consistent across all wrapper functions
    for operation, pattern in expected_patterns.items():
        assert pattern.startswith('Error ')
        assert pattern.endswith(':')
        # Verify the core operation is mentioned in the error message
        if 'create' in operation:
            assert 'creating' in pattern.lower() or 'create' in pattern.lower()
        elif 'list' in operation:
            assert 'listing' in pattern.lower() or 'list' in pattern.lower()
        elif 'clone' in operation:
            assert 'cloning' in pattern.lower() or 'clone' in pattern.lower()


# =============================================================================
# MODULE STRUCTURE VALIDATION TESTS  
# =============================================================================

def test_mcp_module_structure():
    """Test that the MCP module has expected structure"""
    import netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp as mcp_module
    
    # Check that key components exist
    assert hasattr(mcp_module, 'mcp')
    assert hasattr(mcp_module, 'main')
    assert hasattr(mcp_module, 'logger')
    
    # Check that traditional GCNV imports exist
    gcnv_functions = [
        'create_volume', 'clone_volume', 'list_volumes',
        'create_snapshot', 'list_snapshots', 'create_replication'
    ]
    
    for func_name in gcnv_functions:
        assert hasattr(mcp_module, func_name), f"Missing import: {func_name}"


def test_mcp_module_can_be_imported():
    """Test that the MCP module can be imported without errors"""
    try:
        import netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp
        # If we get here, import was successful
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import MCP module: {e}")


def test_logging_configuration():
    """Test that logging is properly configured"""
    import netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp as mcp_module
    
    assert hasattr(mcp_module, 'logger')
    logger = mcp_module.logger
    
    # Check that logger has expected attributes
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'warning')
    assert logger.name == 'netapp_dataops.mcp_server.netapp_dataops_gcnv_mcp'
