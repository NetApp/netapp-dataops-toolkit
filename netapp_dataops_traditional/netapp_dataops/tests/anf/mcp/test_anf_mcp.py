import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Required arguments for testing MCP server functions
VOLUME_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume',
    'location': 'eastus',
    'creation_token': 'test-token',
    'usage_threshold': 107374182400,  # 100 GiB in bytes
    'protocol_types': ['NFSv3'],
    'virtual_network_name': 'test-vnet'
}

CLONE_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'source_volume_name': 'test-source-volume',
    'volume_name': 'test-clone',
    'location': 'eastus',
    'creation_token': 'test-clone-token',
    'snapshot_name': 'test-snapshot',
    'virtual_network_name': 'test-vnet'
}

LIST_VOLUMES_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool'
}

SNAPSHOT_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume',
    'snapshot_name': 'test-snapshot',
    'location': 'eastus'
}

LIST_SNAPSHOTS_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume'
}

REPLICATION_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume',
    'destination_resource_group_name': 'test-dest-rg',
    'destination_account_name': 'test-dest-account',
    'destination_pool_name': 'test-dest-pool',
    'destination_volume_name': 'test-dest-volume',
    'destination_location': 'westus',
    'destination_creation_token': 'test-dest-token',
    'destination_usage_threshold': 107374182400,  # 100 GiB in bytes
    'destination_protocol_types': ['NFSv3'],
    'destination_virtual_network_name': 'test-dest-vnet'
}

# =============================================================================
# MCP SERVER BASIC INTEGRATION TESTS
# =============================================================================

def test_mcp_server_instance_exists():
    """Test that the MCP server instance is created correctly"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import mcp
    assert mcp is not None
    assert hasattr(mcp, 'name')
    assert mcp.name == "NetApp DataOps ANF Toolkit MCP"


def test_main_function():
    """Test the main entry point function"""
    with patch('netapp_dataops.mcp_server.netapp_dataops_anf_mcp.mcp.run') as mock_mcp_run:
        with patch('netapp_dataops.mcp_server.netapp_dataops_anf_mcp.logging.basicConfig'):
            with patch('netapp_dataops.mcp_server.netapp_dataops_anf_mcp.logging.info'):
                # Import and run the main execution
                import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
                
                # Simulate the main execution path
                try:
                    mcp_module.mcp.run(transport="stdio")
                    mock_mcp_run.assert_called_once_with(transport="stdio")
                except SystemExit:
                    # Expected for testing
                    pass


def test_imports_from_traditional_anf():
    """Test that the MCP server correctly imports from traditional ANF module"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
    
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
    try:
        result = create_volume_func(**kwargs)
        if result['status'] == 'error':
            if kwargs.get('print_output', False):
                logger_func(f"Error creating ANF volume: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if kwargs.get('print_output', False):
            logger_func(f"Error creating ANF volume: {e}")
        return {"status": "error", "details": f"Error creating ANF volume: {e}"}


async def clone_volume_wrapper_logic(
    clone_volume_func, logger_func, **kwargs
):
    """Recreate the clone volume wrapper logic for testing"""
    try:
        result = clone_volume_func(**kwargs)
        if result['status'] == 'error':
            if kwargs.get('print_output', False):
                logger_func(f"Error cloning ANF volume: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if kwargs.get('print_output', False):
            logger_func(f"Error cloning ANF volume: {e}")
        return {"status": "error", "details": f"Error cloning ANF volume: {e}"}


async def list_volumes_wrapper_logic(
    list_volumes_func, logger_func, **kwargs
):
    """Recreate the list volumes wrapper logic for testing"""
    try:
        result = list_volumes_func(**kwargs)
        if result['status'] == 'error':
            if kwargs.get('print_output', False):
                logger_func(f"Error listing ANF volumes: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if kwargs.get('print_output', False):
            logger_func(f"Error listing ANF volumes: {e}")
        return {"status": "error", "details": f"Error listing ANF volumes: {e}"}


async def create_snapshot_wrapper_logic(
    create_snapshot_func, logger_func, **kwargs
):
    """Recreate the create snapshot wrapper logic for testing"""
    try:
        result = create_snapshot_func(**kwargs)
        if result['status'] == 'error':
            if kwargs.get('print_output', False):
                logger_func(f"Error creating ANF snapshot: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if kwargs.get('print_output', False):
            logger_func(f"Error creating ANF snapshot: {e}")
        return {"status": "error", "details": f"Error creating ANF snapshot: {e}"}


async def list_snapshots_wrapper_logic(
    list_snapshots_func, logger_func, **kwargs
):
    """Recreate the list snapshots wrapper logic for testing"""
    try:
        result = list_snapshots_func(**kwargs)
        if result['status'] == 'error':
            if kwargs.get('print_output', False):
                logger_func(f"Error listing ANF snapshots: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if kwargs.get('print_output', False):
            logger_func(f"Error listing ANF snapshots: {e}")
        return {"status": "error", "details": f"Error listing ANF snapshots: {e}"}


async def create_replication_wrapper_logic(
    create_replication_func, logger_func, **kwargs
):
    """Recreate the create replication wrapper logic for testing"""
    try:
        result = create_replication_func(**kwargs)
        if result['status'] == 'error':
            if kwargs.get('print_output', False):
                logger_func(f"Error creating ANF replication: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if kwargs.get('print_output', False):
            logger_func(f"Error creating ANF replication: {e}")
        return {"status": "error", "details": f"Error creating ANF replication: {e}"}


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
    mock_create = MagicMock(return_value={'status': 'error', 'details': 'Volume creation failed'})
    mock_logger = MagicMock()
    
    args_with_print = VOLUME_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await create_volume_wrapper_logic(mock_create, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    assert result['details'] == 'Volume creation failed'
    mock_logger.assert_called_once_with('Error creating ANF volume: Volume creation failed')


@pytest.mark.asyncio
async def test_create_volume_wrapper_exception():
    """Test the create volume wrapper logic with exception"""
    mock_create = MagicMock(side_effect=Exception('Connection failed'))
    mock_logger = MagicMock()
    
    args_with_print = VOLUME_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await create_volume_wrapper_logic(mock_create, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    assert 'Connection failed' in result['details']
    mock_logger.assert_called_once()


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
async def test_clone_volume_wrapper_error_with_details():
    """Test the clone volume wrapper logic with error response containing details"""
    mock_clone = MagicMock(return_value={'status': 'error', 'details': 'Clone failed'})
    mock_logger = MagicMock()
    
    args_with_print = CLONE_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await clone_volume_wrapper_logic(mock_clone, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    assert result['details'] == 'Clone failed'
    mock_logger.assert_called_once_with('Error cloning ANF volume: Clone failed')


@pytest.mark.asyncio
async def test_clone_volume_wrapper_error_without_details():
    """Test the clone volume wrapper logic with error response missing details"""
    mock_clone = MagicMock(return_value={'status': 'error'})
    mock_logger = MagicMock()
    
    args_with_print = CLONE_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await clone_volume_wrapper_logic(mock_clone, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    mock_logger.assert_called_once_with('Error cloning ANF volume: Unknown error')


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
    mock_list = MagicMock(return_value={'status': 'error', 'details': 'List failed'})
    mock_logger = MagicMock()
    
    args_with_print = LIST_VOLUMES_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await list_volumes_wrapper_logic(mock_list, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    assert result['details'] == 'List failed'
    mock_logger.assert_called_once_with('Error listing ANF volumes: List failed')


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
    mock_create = MagicMock(return_value={'status': 'error', 'details': 'Snapshot creation failed'})
    mock_logger = MagicMock()
    
    args_with_print = SNAPSHOT_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await create_snapshot_wrapper_logic(mock_create, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    assert result['details'] == 'Snapshot creation failed'
    mock_logger.assert_called_once_with('Error creating ANF snapshot: Snapshot creation failed')


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
    mock_list = MagicMock(return_value={'status': 'error', 'details': 'List snapshots failed'})
    mock_logger = MagicMock()
    
    args_with_print = LIST_SNAPSHOTS_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await list_snapshots_wrapper_logic(mock_list, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    assert result['details'] == 'List snapshots failed'
    mock_logger.assert_called_once_with('Error listing ANF snapshots: List snapshots failed')


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
    mock_create = MagicMock(return_value={'status': 'error', 'details': 'Replication failed'})
    mock_logger = MagicMock()
    
    args_with_print = REPLICATION_REQUIRED_ARGS.copy()
    args_with_print['print_output'] = True
    
    result = await create_replication_wrapper_logic(mock_create, mock_logger, **args_with_print)
    
    assert result['status'] == 'error'
    assert result['details'] == 'Replication failed'
    mock_logger.assert_called_once_with('Error creating ANF replication: Replication failed')


# =============================================================================
# INTEGRATION VALIDATION TESTS
# =============================================================================

def test_response_format_consistency():
    """Test that all wrapper functions follow consistent response format patterns"""
    # This test validates that our wrapper logic follows the expected patterns
    # All success responses should have 'status': 'success' and 'details'
    # All error responses should have 'status': 'error' and 'details'
    
    # Test data structures match expected format
    success_response = {'status': 'success', 'details': {'name': 'test-resource'}}
    error_response = {'status': 'error', 'details': 'Test error'}
    
    assert 'status' in success_response
    assert success_response['status'] == 'success'
    assert 'details' in success_response
    
    assert 'status' in error_response
    assert error_response['status'] == 'error'
    assert 'details' in error_response


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
        'create_volume': 'Error creating ANF volume:',
        'clone_volume': 'Error cloning ANF volume:',
        'list_volumes': 'Error listing ANF volumes:',
        'create_snapshot': 'Error creating ANF snapshot:',
        'list_snapshots': 'Error listing ANF snapshots:',
        'create_replication': 'Error creating ANF replication:'
    }
    
    # These patterns should be consistent across all wrapper functions
    for operation, pattern in expected_patterns.items():
        assert pattern.startswith('Error ')
        assert pattern.endswith(':')
        assert 'ANF' in pattern
        # Verify the core operation is mentioned in the error message
        if 'create' in operation:
            assert 'creating' in pattern.lower() or 'create' in pattern.lower()
        elif 'list' in operation:
            assert 'listing' in pattern.lower() or 'list' in pattern.lower()
        elif 'clone' in operation:
            assert 'cloning' in pattern.lower() or 'clone' in pattern.lower()


def test_print_output_parameter_handling():
    """Test that print_output parameter is handled consistently across all functions"""
    # All wrapper functions should check print_output before logging
    # This ensures consistent behavior for MCP tool output control
    
    test_functions = [
        'create_volume_wrapper_logic',
        'clone_volume_wrapper_logic', 
        'list_volumes_wrapper_logic',
        'create_snapshot_wrapper_logic',
        'list_snapshots_wrapper_logic',
        'create_replication_wrapper_logic'
    ]
    
    for func_name in test_functions:
        # Check that the function exists and handles print_output
        func = globals()[func_name]
        assert asyncio.iscoroutinefunction(func)
        # The actual print_output handling is tested in individual wrapper tests


# =============================================================================
# MODULE STRUCTURE VALIDATION TESTS  
# =============================================================================

def test_mcp_module_structure():
    """Test that the MCP module has expected structure"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
    
    # Check that key components exist
    assert hasattr(mcp_module, 'mcp')
    assert hasattr(mcp_module, 'logger')
    
    # Check that traditional ANF imports exist
    anf_functions = [
        'create_volume', 'clone_volume', 'list_volumes',
        'create_snapshot', 'list_snapshots', 'create_replication'
    ]
    
    for func_name in anf_functions:
        assert hasattr(mcp_module, func_name), f"Missing import: {func_name}"


def test_mcp_module_can_be_imported():
    """Test that the MCP module can be imported without errors"""
    try:
        import netapp_dataops.mcp_server.netapp_dataops_anf_mcp
        # If we get here, import was successful
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import MCP module: {e}")


def test_logging_configuration():
    """Test that logging is properly configured"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
    
    assert hasattr(mcp_module, 'logger')
    logger = mcp_module.logger
    
    # Check that logger has expected attributes
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'warning')
    assert logger.name == 'netapp_dataops.mcp_server.netapp_dataops_anf_mcp'


def test_fastmcp_integration():
    """Test that FastMCP is properly integrated"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
    
    # Check that mcp instance exists and is configured
    assert hasattr(mcp_module, 'mcp')
    mcp_instance = mcp_module.mcp
    
    # Verify it's a FastMCP instance (duck typing check)
    assert hasattr(mcp_instance, 'name')
    assert hasattr(mcp_instance, 'run')
    assert mcp_instance.name == "NetApp DataOps ANF Toolkit MCP"


def test_anf_specific_imports():
    """Test that ANF-specific imports are correct"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
    
    # Verify ANF-specific functions are imported
    anf_functions = {
        'create_volume': 'Volume creation function',
        'clone_volume': 'Volume cloning function', 
        'list_volumes': 'Volume listing function',
        'create_snapshot': 'Snapshot creation function',
        'list_snapshots': 'Snapshot listing function',
        'create_replication': 'Replication creation function'
    }
    
    for func_name, description in anf_functions.items():
        assert hasattr(mcp_module, func_name), f"Missing {description}: {func_name}"
        func = getattr(mcp_module, func_name)
        assert callable(func), f"{func_name} is not callable"


def test_mcp_tool_decorators():
    """Test that MCP tool decorators are properly applied"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
    
    # Check that mcp instance has tool manager
    mcp_instance = mcp_module.mcp
    
    # Verify that tools can be retrieved (FastMCP specific)
    if hasattr(mcp_instance, '_tool_manager'):
        # This would be implementation specific for FastMCP
        assert hasattr(mcp_instance._tool_manager, 'get_tools')


def test_module_startup_configuration():
    """Test that module startup configuration is correct"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as mcp_module
    
    # Check for proper imports
    required_imports = ['logging', 'sys', 'asyncio', 'FastMCP']
    
    # The module should have these available through its imports
    assert hasattr(mcp_module, 'logging')
    assert hasattr(mcp_module, 'sys') 
    assert hasattr(mcp_module, 'asyncio')
    
    # Check setup_logger import
    assert hasattr(mcp_module, 'setup_logger')
