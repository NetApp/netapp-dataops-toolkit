import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

# Required arguments for testing MCP server functions
VOLUME_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-volume',
    'location': 'eastus',
    'creation_token': 'test-token',
    'usage_threshold': 107374182400,  # 100 GiB
    'protocol_types': ['NFSv3'],
    'virtual_network_name': 'test-vnet'
}

CLONE_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-clone-volume',
    'location': 'eastus',
    'creation_token': 'test-clone-token',
    'usage_threshold': 107374182400,
    'protocol_types': ['NFSv3'],
    'virtual_network_name': 'test-vnet',
    'source_volume_id': '/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.NetApp/netAppAccounts/test-account/capacityPools/test-pool/volumes/test-source-volume'
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
    'snapshot_name': 'test-snapshot'
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
    'source_volume_name': 'test-source-volume',
    'destination_resource_group_name': 'test-dest-rg',
    'destination_account_name': 'test-dest-account',
    'destination_pool_name': 'test-dest-pool',
    'destination_volume_name': 'test-dest-volume',
    'destination_location': 'westus',
    'replication_schedule': 'hourly',
    'creation_token': 'test-dest-token',
    'usage_threshold': 107374182400,
    'protocol_types': ['NFSv3'],
    'virtual_network_name': 'test-dest-vnet'
}

DATA_PROTECTION_REQUIRED_ARGS = {
    'resource_group_name': 'test-rg',
    'account_name': 'test-account',
    'pool_name': 'test-pool',
    'volume_name': 'test-dp-volume',
    'location': 'westus',
    'creation_token': 'test-dp-token',
    'usage_threshold': 107374182400,
    'protocol_types': ['NFSv3'],
    'virtual_network_name': 'test-vnet',
    'source_resource_id': '/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.NetApp/netAppAccounts/test-account/capacityPools/test-pool/volumes/test-source-volume',
    'replication_schedule': 'hourly',
    'remote_volume_region': 'eastus'
}

# =============================================================================
# SERVER INSTANTIATION TESTS
# =============================================================================

def test_mcp_server_instantiation():
    """Test MCP server can be instantiated successfully"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import mcp
    assert mcp is not None
    assert mcp.name == "NetApp DataOps ANF Toolkit MCP"


def test_mcp_server_tools_registration():
    """Test that all expected tools are registered with the MCP server"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import mcp
    
    # Get list of registered tool names
    tool_names = [tool.name for tool in mcp.tools]
    
    # Check that essential tools are registered
    expected_tools = [
        "Create Volume",
        "Clone Volume", 
        "List Volumes",
        "Create Snapshot",
        "List Snapshots",
        "Create Replication",
        "Create Data Protection Volume"
    ]
    
    for tool in expected_tools:
        assert tool in tool_names, f"Tool '{tool}' not found in registered tools"


def test_mcp_server_tool_metadata():
    """Test that tools have proper metadata and descriptions"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import mcp
    
    for tool in mcp.tools:
        assert hasattr(tool, 'name'), f"Tool missing name attribute"
        assert hasattr(tool, 'func'), f"Tool '{tool.name}' missing function"
        # Check that the function is async
        assert asyncio.iscoroutinefunction(tool.func), f"Tool '{tool.name}' function is not async"

# =============================================================================
# BUSINESS LOGIC VALIDATION TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Volume Management MCP Tools
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_volume_tool_success():
    """Test create volume MCP tool with successful execution"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_volume_tool
    
    with patch('netapp_dataops.traditional.anf.create_volume') as mock_create:
        mock_create.return_value = {'status': 'success', 'volume': {'name': 'test-volume'}}
        
        result = await create_volume_tool(**VOLUME_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'volume' in result
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_volume_tool_failure():
    """Test create volume MCP tool with failure scenarios"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_volume_tool
    
    with patch('netapp_dataops.traditional.anf.create_volume') as mock_create:
        mock_create.return_value = {'status': 'error', 'message': 'Volume creation failed'}
        
        result = await create_volume_tool(**VOLUME_REQUIRED_ARGS)
        
        assert result['status'] == 'error'
        assert 'message' in result


@pytest.mark.asyncio
async def test_create_volume_tool_exception():
    """Test create volume MCP tool with exception handling"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_volume_tool
    
    with patch('netapp_dataops.traditional.anf.create_volume') as mock_create:
        mock_create.side_effect = Exception("Unexpected error")
        
        result = await create_volume_tool(**VOLUME_REQUIRED_ARGS)
        
        assert result['status'] == 'error'
        assert 'Unexpected error' in result['message']


@pytest.mark.asyncio
async def test_clone_volume_tool_success():
    """Test clone volume MCP tool with successful execution"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import clone_volume_tool
    
    with patch('netapp_dataops.traditional.anf.clone_volume') as mock_clone:
        mock_clone.return_value = {'status': 'success', 'volume': {'name': 'test-clone-volume'}}
        
        result = await clone_volume_tool(**CLONE_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'volume' in result
        mock_clone.assert_called_once()


@pytest.mark.asyncio
async def test_list_volumes_tool_success():
    """Test list volumes MCP tool with successful execution"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import list_volumes_tool
    
    with patch('netapp_dataops.traditional.anf.list_volumes') as mock_list:
        mock_list.return_value = {'status': 'success', 'volumes': [{'name': 'vol1'}, {'name': 'vol2'}]}
        
        result = await list_volumes_tool(**LIST_VOLUMES_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'volumes' in result
        assert len(result['volumes']) == 2
        mock_list.assert_called_once()

# -----------------------------------------------------------------------------
# Snapshot Management MCP Tools
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_snapshot_tool_success():
    """Test create snapshot MCP tool with successful execution"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_snapshot_tool
    
    with patch('netapp_dataops.traditional.anf.create_snapshot') as mock_create:
        mock_create.return_value = {'status': 'success', 'snapshot': {'name': 'test-snapshot'}}
        
        result = await create_snapshot_tool(**SNAPSHOT_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'snapshot' in result
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_snapshot_tool_failure():
    """Test create snapshot MCP tool with failure scenarios"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_snapshot_tool
    
    with patch('netapp_dataops.traditional.anf.create_snapshot') as mock_create:
        mock_create.return_value = {'status': 'error', 'message': 'Snapshot creation failed'}
        
        result = await create_snapshot_tool(**SNAPSHOT_REQUIRED_ARGS)
        
        assert result['status'] == 'error'
        assert 'message' in result


@pytest.mark.asyncio
async def test_list_snapshots_tool_success():
    """Test list snapshots MCP tool with successful execution"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import list_snapshots_tool
    
    with patch('netapp_dataops.traditional.anf.list_snapshots') as mock_list:
        mock_list.return_value = {'status': 'success', 'snapshots': [{'name': 'snap1'}, {'name': 'snap2'}]}
        
        result = await list_snapshots_tool(**LIST_SNAPSHOTS_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'snapshots' in result
        assert len(result['snapshots']) == 2
        mock_list.assert_called_once()


@pytest.mark.asyncio
async def test_list_snapshots_tool_empty():
    """Test list snapshots MCP tool with empty results"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import list_snapshots_tool
    
    with patch('netapp_dataops.traditional.anf.list_snapshots') as mock_list:
        mock_list.return_value = {'status': 'success', 'snapshots': []}
        
        result = await list_snapshots_tool(**LIST_SNAPSHOTS_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'snapshots' in result
        assert len(result['snapshots']) == 0

# -----------------------------------------------------------------------------
# Replication Management MCP Tools
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_replication_tool_success():
    """Test create replication MCP tool with successful execution"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_replication_tool
    
    with patch('netapp_dataops.traditional.anf.create_replication') as mock_create:
        mock_create.return_value = {'status': 'success', 'replication': {'schedule': 'hourly'}}
        
        result = await create_replication_tool(**REPLICATION_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'replication' in result
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_replication_tool_failure():
    """Test create replication MCP tool with failure scenarios"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_replication_tool
    
    with patch('netapp_dataops.traditional.anf.create_replication') as mock_create:
        mock_create.return_value = {'status': 'error', 'message': 'Replication creation failed'}
        
        result = await create_replication_tool(**REPLICATION_REQUIRED_ARGS)
        
        assert result['status'] == 'error'
        assert 'message' in result


@pytest.mark.asyncio
async def test_create_data_protection_volume_tool_success():
    """Test create data protection volume MCP tool with successful execution"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_data_protection_volume_tool
    
    with patch('netapp_dataops.traditional.anf.create_data_protection_volume') as mock_create:
        mock_create.return_value = {'status': 'success', 'volume': {'name': 'test-dp-volume'}}
        
        result = await create_data_protection_volume_tool(**DATA_PROTECTION_REQUIRED_ARGS)
        
        assert result['status'] == 'success'
        assert 'volume' in result
        mock_create.assert_called_once()

# =============================================================================
# INTEGRATION VALIDATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_volume_lifecycle_integration():
    """Test complete volume lifecycle through MCP tools"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import (
        create_volume_tool, 
        list_volumes_tool
    )
    
    # Mock successful responses
    with patch('netapp_dataops.traditional.anf.create_volume') as mock_create, \
         patch('netapp_dataops.traditional.anf.list_volumes') as mock_list:
        
        mock_create.return_value = {'status': 'success', 'volume': {'name': 'test-volume'}}
        mock_list.return_value = {'status': 'success', 'volumes': [{'name': 'test-volume'}]}
        
        # Test create volume
        create_result = await create_volume_tool(**VOLUME_REQUIRED_ARGS)
        assert create_result['status'] == 'success'
        
        # Test list volumes
        list_result = await list_volumes_tool(**LIST_VOLUMES_REQUIRED_ARGS)
        assert list_result['status'] == 'success'
        assert len(list_result['volumes']) == 1


@pytest.mark.asyncio
async def test_snapshot_lifecycle_integration():
    """Test complete snapshot lifecycle through MCP tools"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import (
        create_snapshot_tool,
        list_snapshots_tool
    )
    
    # Mock successful responses
    with patch('netapp_dataops.traditional.anf.create_snapshot') as mock_create, \
         patch('netapp_dataops.traditional.anf.list_snapshots') as mock_list:
        
        mock_create.return_value = {'status': 'success', 'snapshot': {'name': 'test-snapshot'}}
        mock_list.return_value = {'status': 'success', 'snapshots': [{'name': 'test-snapshot'}]}
        
        # Test create snapshot
        create_result = await create_snapshot_tool(**SNAPSHOT_REQUIRED_ARGS)
        assert create_result['status'] == 'success'
        
        # Test list snapshots
        list_result = await list_snapshots_tool(**LIST_SNAPSHOTS_REQUIRED_ARGS)
        assert list_result['status'] == 'success'
        assert len(list_result['snapshots']) == 1


@pytest.mark.asyncio
async def test_disaster_recovery_integration():
    """Test disaster recovery workflow through MCP tools"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import (
        create_volume_tool,
        create_data_protection_volume_tool,
        create_replication_tool
    )
    
    # Mock successful responses
    with patch('netapp_dataops.traditional.anf.create_volume') as mock_create_vol, \
         patch('netapp_dataops.traditional.anf.create_data_protection_volume') as mock_create_dp, \
         patch('netapp_dataops.traditional.anf.create_replication') as mock_create_rep:
        
        mock_create_vol.return_value = {'status': 'success', 'volume': {'name': 'test-volume'}}
        mock_create_dp.return_value = {'status': 'success', 'volume': {'name': 'test-dp-volume'}}
        mock_create_rep.return_value = {'status': 'success', 'replication': {'schedule': 'hourly'}}
        
        # Test create source volume
        source_result = await create_volume_tool(**VOLUME_REQUIRED_ARGS)
        assert source_result['status'] == 'success'
        
        # Test create data protection volume
        dp_result = await create_data_protection_volume_tool(**DATA_PROTECTION_REQUIRED_ARGS)
        assert dp_result['status'] == 'success'
        
        # Test create replication
        replication_result = await create_replication_tool(**REPLICATION_REQUIRED_ARGS)
        assert replication_result['status'] == 'success'

# =============================================================================
# MODULE STRUCTURE TESTS
# =============================================================================

def test_mcp_server_module_imports():
    """Test that the MCP server module can import all required dependencies"""
    try:
        from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import (
            FastMCP,
            create_volume,
            clone_volume,
            list_volumes,
            create_snapshot,
            list_snapshots,
            create_replication,
            create_data_protection_volume
        )
        # If we get here, all imports were successful
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import required modules: {e}")


def test_mcp_server_module_structure():
    """Test that the MCP server module has the expected structure"""
    import netapp_dataops.mcp_server.netapp_dataops_anf_mcp as anf_mcp
    
    # Check that the module has the expected attributes
    assert hasattr(anf_mcp, 'mcp'), "Module missing 'mcp' attribute"
    assert hasattr(anf_mcp, 'logger'), "Module missing 'logger' attribute"
    
    # Check that essential tool functions exist
    tool_functions = [
        'create_volume_tool',
        'clone_volume_tool',
        'list_volumes_tool',
        'create_snapshot_tool',
        'list_snapshots_tool',
        'create_replication_tool',
        'create_data_protection_volume_tool'
    ]
    
    for func_name in tool_functions:
        assert hasattr(anf_mcp, func_name), f"Module missing tool function '{func_name}'"
        func = getattr(anf_mcp, func_name)
        assert asyncio.iscoroutinefunction(func), f"Tool function '{func_name}' is not async"


def test_mcp_server_tool_parameter_validation():
    """Test that MCP server tools properly validate parameters"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import create_volume_tool
    
    # Test with missing required parameters
    incomplete_args = VOLUME_REQUIRED_ARGS.copy()
    del incomplete_args['resource_group_name']
    
    # The tool should handle missing parameters gracefully
    with patch('netapp_dataops.traditional.anf.create_volume') as mock_create:
        mock_create.side_effect = ValueError("Missing required parameter")
        
        async def test_missing_param():
            result = await create_volume_tool(**incomplete_args)
            assert result['status'] == 'error'
            assert 'Missing required parameter' in result['message']
        
        asyncio.run(test_missing_param())


@pytest.mark.asyncio
async def test_mcp_server_error_handling_consistency():
    """Test that all MCP tools handle errors consistently"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import (
        create_volume_tool,
        create_snapshot_tool,
        create_replication_tool
    )
    
    tools_and_args = [
        (create_volume_tool, VOLUME_REQUIRED_ARGS),
        (create_snapshot_tool, SNAPSHOT_REQUIRED_ARGS),
        (create_replication_tool, REPLICATION_REQUIRED_ARGS)
    ]
    
    for tool_func, args in tools_and_args:
        # Mock the underlying function to raise an exception
        module_path = tool_func.__module__
        func_name = tool_func.__name__.replace('_tool', '').replace('_', '_')
        
        with patch(f'netapp_dataops.traditional.anf.{func_name}') as mock_func:
            mock_func.side_effect = Exception("Test error")
            
            result = await tool_func(**args)
            
            # All tools should return consistent error structure
            assert result['status'] == 'error'
            assert 'message' in result
            assert isinstance(result['message'], str)


def test_mcp_server_logging_configuration():
    """Test that the MCP server has proper logging configuration"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import logger
    
    # Check that logger exists and is properly configured
    assert logger is not None
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'debug')
    assert hasattr(logger, 'warning')


@pytest.mark.asyncio
async def test_concurrent_tool_execution():
    """Test that multiple MCP tools can be executed concurrently"""
    from netapp_dataops.mcp_server.netapp_dataops_anf_mcp import (
        create_volume_tool,
        list_volumes_tool
    )
    
    with patch('netapp_dataops.traditional.anf.create_volume') as mock_create, \
         patch('netapp_dataops.traditional.anf.list_volumes') as mock_list:
        
        mock_create.return_value = {'status': 'success', 'volume': {'name': 'test-volume'}}
        mock_list.return_value = {'status': 'success', 'volumes': []}
        
        # Execute tools concurrently
        tasks = [
            create_volume_tool(**VOLUME_REQUIRED_ARGS),
            list_volumes_tool(**LIST_VOLUMES_REQUIRED_ARGS)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Both operations should complete successfully
        assert all(result['status'] == 'success' for result in results)
        assert len(results) == 2
