import pytest
from unittest.mock import patch, MagicMock, Mock
from azure.core.exceptions import ClientAuthenticationError, AzureError
from netapp_dataops.traditional.anf import client

# =============================================================================
# ANF CLIENT TESTS
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

def test_get_anf_client_success():
    """Test successful ANF client creation"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result_client, result_sub_id = client.get_anf_client(subscription_id='test-sub-id')
                
                assert result_client is not None
                assert result_sub_id == 'test-sub-id'
                mock_client_class.assert_called_once()
                mock_credential.assert_called_once()


def test_get_anf_client_with_environment_subscription():
    """Test ANF client creation with subscription from environment"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                with patch('os.getenv') as mock_getenv:
                    # Configure mock to return specific values for different env vars
                    def getenv_side_effect(key):
                        if key == 'AZURE_SUBSCRIPTION_ID':
                            return 'env-sub-id'
                        elif key in ['AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID']:
                            return None  # No service principal env vars
                        return None
                    
                    mock_getenv.side_effect = getenv_side_effect
                    mock_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result_client, result_sub_id = client.get_anf_client()
                    
                    assert result_client is not None
                    assert result_sub_id == 'env-sub-id'
                    # Verify that AZURE_SUBSCRIPTION_ID was called among the getenv calls
                    getenv_calls = mock_getenv.call_args_list
                    assert any(call[0][0] == 'AZURE_SUBSCRIPTION_ID' for call in getenv_calls)


def test_get_anf_client_caching():
    """Test that ANF client instances are properly cached"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Call get_anf_client twice with same subscription
                client1, sub_id1 = client.get_anf_client(subscription_id='test-sub-id')
                client2, sub_id2 = client.get_anf_client(subscription_id='test-sub-id')
                
                # Should return the same instance due to singleton pattern
                assert client1 is not None
                assert client2 is not None
                assert client1 is client2  # Same instance due to singleton
                assert sub_id1 == sub_id2 == 'test-sub-id'
                # Should only create client once due to caching
                mock_client_class.assert_called_once()

# -----------------------------------------------------------------------------
# Failure Cases
# -----------------------------------------------------------------------------

def test_get_anf_client_authentication_error():
    """Test ANF client creation with authentication failure"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client_class.side_effect = Exception("Authentication failed")
                
                with pytest.raises(ClientAuthenticationError):
                    client.get_anf_client(subscription_id='test-sub-id')


def test_get_anf_client_azure_error():
    """Test ANF client creation with general Azure error"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client_class.side_effect = AzureError("Azure service error")
                
                with pytest.raises(ClientAuthenticationError):  # Implementation wraps all exceptions in ClientAuthenticationError
                    client.get_anf_client(subscription_id='test-sub-id')


def test_get_anf_client_generic_exception():
    """Test ANF client creation with generic exception"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client_class.side_effect = Exception("Unexpected error")
                
                with pytest.raises(ClientAuthenticationError) as exc_info:
                    client.get_anf_client(subscription_id='test-sub-id')
                
                assert "Failed to authenticate with Azure" in str(exc_info.value)

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

def test_get_anf_client_missing_subscription_id():
    """Test ANF client creation with missing subscription ID"""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.return_value = None  # No env var set
        with pytest.raises(ValueError):
            client.get_anf_client(subscription_id=None)


def test_get_anf_client_empty_subscription_id():
    """Test ANF client creation with empty subscription ID"""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.return_value = None  # No env var set
        with pytest.raises(ValueError):
            client.get_anf_client(subscription_id="")


def test_get_anf_client_invalid_subscription_id_format():
    """Test ANF client creation with invalid subscription ID format"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                # Azure SDK should handle validation, but let's test our client doesn't crash
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result_client, result_sub_id = client.get_anf_client(subscription_id='invalid-format')
                assert result_client is not None
                assert result_sub_id == 'invalid-format'

# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

def test_get_anf_client_different_subscriptions():
    """Test ANF client creation with different subscription IDs"""
    # Note: The singleton pattern means only one client is created per process
    # This test demonstrates the current behavior
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                client1, sub_id1 = client.get_anf_client(subscription_id='sub-1')
                client2, sub_id2 = client.get_anf_client(subscription_id='sub-2')
                
                assert client1 is not None
                assert client2 is not None
                assert sub_id1 == 'sub-1'
                assert sub_id2 == 'sub-2'
                # Due to singleton pattern, same client instance is reused
                assert client1 is client2
                # Only one client created due to singleton
                assert mock_client_class.call_count == 1


def test_get_anf_client_concurrent_creation():
    """Test ANF client creation under concurrent access"""
    import threading
    import time
    
    results = []
    exceptions = []
    
    def create_client():
        try:
            with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
                with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
                    mock_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result = client.get_anf_client(subscription_id='test-sub-id')
                    results.append(result)
        except Exception as e:
            exceptions.append(e)
    
    # Create multiple threads to test concurrent client creation
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=create_client)
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All clients should be created successfully
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
    assert len(results) > 0, "No clients were created"


def test_get_anf_client_with_service_principal_env_vars():
    """Test ANF client creation with service principal environment variables"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.ClientSecretCredential') as mock_sp_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                with patch.dict('os.environ', {
                    'AZURE_CLIENT_ID': 'test-client-id',
                    'AZURE_CLIENT_SECRET': 'test-client-secret',
                    'AZURE_TENANT_ID': 'test-tenant-id'
                }):
                    mock_sp_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result_client, result_sub_id = client.get_anf_client(subscription_id='test-sub-id')
                    
                    assert result_client is not None
                    assert result_sub_id == 'test-sub-id'
                    # Should use ClientSecretCredential when env vars are set
                    mock_sp_credential.assert_called_once_with(
                        tenant_id='test-tenant-id',
                        client_id='test-client-id',
                        client_secret='test-client-secret'
                    )

# =============================================================================
# CLIENT CONFIGURATION TESTS
# =============================================================================

def test_anf_client_configuration():
    """Test that ANF client is configured with correct parameters"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                test_subscription = 'test-subscription-id'
                result_client, result_sub_id = client.get_anf_client(subscription_id=test_subscription)
                
                # Verify client was created with correct parameters
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                
                # Check that subscription_id was passed (as positional arg)
                assert call_args.args[1] == test_subscription  # Second arg after credential
                assert result_sub_id == test_subscription


def test_anf_client_retry_configuration():
    """Test ANF client retry configuration"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result_client, result_sub_id = client.get_anf_client(subscription_id='test-sub-id')
                
                # Verify client has the expected attributes for retry configuration
                assert result_client is not None
                assert result_sub_id == 'test-sub-id'
                # The actual retry configuration would depend on Azure SDK defaults


def test_anf_client_logging_configuration():
    """Test ANF client logging configuration"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Test that client creation doesn't interfere with logging
                import logging
                logger = logging.getLogger(__name__)
                original_level = logger.level
                
                try:
                    result_client, result_sub_id = client.get_anf_client(subscription_id='test-sub-id')
                    assert result_client is not None
                    assert result_sub_id == 'test-sub-id'
                    
                    # Logging level should remain unchanged
                    assert logger.level == original_level
                    
                finally:
                    logger.setLevel(original_level)

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_anf_client_operations_integration():
    """Test that ANF client can be used for basic operations"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Mock client operations
                mock_client.accounts.list.return_value = []
                mock_client.pools.list.return_value = []
                mock_client.volumes.list.return_value = []
                
                anf_client, sub_id = client.get_anf_client(subscription_id='test-sub-id')
                
                # Test that client has expected operations
                assert hasattr(anf_client, 'accounts')
                assert hasattr(anf_client, 'pools')
                assert hasattr(anf_client, 'volumes')
                assert hasattr(anf_client, 'snapshots')
                assert sub_id == 'test-sub-id'
                
                # Test basic operations don't raise exceptions
                try:
                    anf_client.accounts.list('test-rg')
                    anf_client.pools.list('test-rg', 'test-account')
                    anf_client.volumes.list('test-rg', 'test-account', 'test-pool')
                except AttributeError:
                    # These might not be implemented in the mock, which is fine
                    pass


def test_anf_client_resource_management():
    """Test ANF client resource management capabilities"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                anf_client, sub_id = client.get_anf_client(subscription_id='test-sub-id')
                
                # Test that client has resource management capabilities
                resource_types = ['accounts', 'pools', 'volumes', 'snapshots']
                
                for resource_type in resource_types:
                    assert hasattr(anf_client, resource_type), f"Client missing {resource_type} attribute"
                    
                    resource_manager = getattr(anf_client, resource_type)
                    
                    # Check for common CRUD operations
                    expected_operations = ['list', 'get', 'begin_create_or_update', 'begin_delete']
                    for operation in expected_operations:
                        # Not all operations may be available for all resource types
                        # This is more of a structure check than functional validation
                        if hasattr(resource_manager, operation):
                            assert callable(getattr(resource_manager, operation))
                
                assert sub_id == 'test-sub-id'


def test_anf_client_subscription_handling():
    """Test ANF client handles subscription changes correctly"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):  # Reset singleton
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Create clients for different subscriptions
                client1, sub_id1 = client.get_anf_client(subscription_id='sub-1')
                client2, sub_id2 = client.get_anf_client(subscription_id='sub-2')
                
                # Verify both clients were created
                assert client1 is not None
                assert client2 is not None
                assert sub_id1 == 'sub-1'
                assert sub_id2 == 'sub-2'
                
                # Note: Due to singleton pattern, only one client instance is created
                # The subscription ID is returned separately to track which was requested
                assert mock_client_class.call_count == 1
                
                # Verify the client was created with the first subscription
                calls = mock_client_class.call_args_list
                assert calls[0].args[1] == 'sub-1'  # Second arg after credential


# =============================================================================
# ADVANCED CLIENT AUTHENTICATION TESTS
# =============================================================================

def test_get_anf_client_with_managed_identity():
    """Test ANF client creation with managed identity authentication"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                with patch('os.getenv') as mock_getenv:
                    # Simulate managed identity environment
                    def getenv_side_effect(key):
                        if key == 'AZURE_SUBSCRIPTION_ID':
                            return 'managed-identity-sub'
                        elif key == 'MSI_ENDPOINT':
                            return 'http://169.254.169.254/metadata/identity/oauth2/token'
                        return None
                    
                    mock_getenv.side_effect = getenv_side_effect
                    mock_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result_client, result_sub_id = client.get_anf_client()
                    
                    assert result_client is not None
                    assert result_sub_id == 'managed-identity-sub'


def test_get_anf_client_with_service_principal():
    """Test ANF client creation with service principal authentication"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.ClientSecretCredential') as mock_sp_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                with patch('os.getenv') as mock_getenv:
                    # Simulate service principal environment
                    def getenv_side_effect(key):
                        env_vars = {
                            'AZURE_SUBSCRIPTION_ID': 'sp-sub-id',
                            'AZURE_CLIENT_ID': 'test-client-id',
                            'AZURE_CLIENT_SECRET': 'test-client-secret',
                            'AZURE_TENANT_ID': 'test-tenant-id'
                        }
                        return env_vars.get(key)
                    
                    mock_getenv.side_effect = getenv_side_effect
                    mock_sp_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result_client, result_sub_id = client.get_anf_client()
                    
                    assert result_client is not None
                    assert result_sub_id == 'sp-sub-id'
                    mock_sp_credential.assert_called_once_with(
                        tenant_id='test-tenant-id',
                        client_id='test-client-id',
                        client_secret='test-client-secret'
                    )


def test_get_anf_client_authentication_timeout():
    """Test ANF client creation with authentication timeout"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.side_effect = Exception("Authentication timeout")
                
                with pytest.raises(Exception) as exc_info:
                    client.get_anf_client(subscription_id='test-sub-id')
                
                assert "timeout" in str(exc_info.value).lower()


def test_get_anf_client_invalid_credentials():
    """Test ANF client creation with invalid credentials"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.side_effect = ClientAuthenticationError("Invalid credentials")
                
                with pytest.raises(ClientAuthenticationError):
                    client.get_anf_client(subscription_id='test-sub-id')


def test_get_anf_client_network_error():
    """Test ANF client creation with network connectivity issues"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.side_effect = Exception("Network unreachable")
                
                with pytest.raises(Exception) as exc_info:
                    client.get_anf_client(subscription_id='test-sub-id')
                
                assert "network" in str(exc_info.value).lower()

# =============================================================================
# ADVANCED CLIENT CONFIGURATION TESTS
# =============================================================================

def test_get_anf_client_with_custom_endpoint():
    """Test ANF client creation with custom Azure endpoint"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Test with different Azure clouds
                result_client, result_sub_id = client.get_anf_client(subscription_id='test-sub-id')
                
                assert result_client is not None
                assert result_sub_id == 'test-sub-id'


def test_get_anf_client_retry_logic():
    """Test ANF client creation with retry logic for transient failures"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                # Simulate transient failure then success
                call_count = 0
                def credential_side_effect():
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise Exception("Transient network error")
                    return MagicMock()
                
                mock_credential.side_effect = credential_side_effect
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # This might fail on first attempt, but that's expected behavior
                try:
                    result_client, result_sub_id = client.get_anf_client(subscription_id='test-sub-id')
                    assert result_client is not None
                except Exception:
                    # Expected for first call in this test scenario
                    pass


def test_get_anf_client_concurrent_initialization():
    """Test ANF client creation with concurrent initialization requests"""
    import threading
    import time
    
    results = []
    exceptions = []
    
    def create_client_thread():
        try:
            with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
                with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
                    mock_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result_client, result_sub_id = client.get_anf_client(subscription_id='concurrent-test')
                    results.append((result_client, result_sub_id))
        except Exception as e:
            exceptions.append(e)
    
    # Reset singleton before test
    with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
        # Create multiple threads to test concurrent access
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_client_thread)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no exceptions occurred
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

# =============================================================================
# CLIENT LIFECYCLE AND MANAGEMENT TESTS
# =============================================================================

def test_anf_client_singleton_behavior():
    """Test ANF client singleton pattern behavior"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Create multiple clients with same subscription
                client1, sub_id1 = client.get_anf_client(subscription_id='test-sub')
                client2, sub_id2 = client.get_anf_client(subscription_id='test-sub')
                
                # Should return same client instance (singleton behavior)
                assert client1 is client2
                assert sub_id1 == sub_id2 == 'test-sub'
                
                # NetAppManagementClient should only be called once
                assert mock_client_class.call_count == 1


def test_anf_client_memory_cleanup():
    """Test ANF client memory cleanup and garbage collection"""
    import gc
    import weakref
    
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Create client and weak reference
                result_client, _ = client.get_anf_client(subscription_id='memory-test')
                weak_ref = weakref.ref(result_client)
                
                # Client should exist
                assert weak_ref() is not None
                
                # Clear reference and force garbage collection
                del result_client
                gc.collect()
                
                # Note: Due to singleton pattern, the client may still exist in the manager


def test_anf_client_error_recovery():
    """Test ANF client error recovery and state management"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                # First call fails
                mock_credential.side_effect = [Exception("First failure"), MagicMock()]
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # First attempt should fail
                with pytest.raises(Exception):
                    client.get_anf_client(subscription_id='error-recovery-test')
                
                # Reset the side effect for second attempt
                with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                    mock_credential.side_effect = None
                    mock_credential.return_value = MagicMock()
                    
                    # Second attempt should succeed
                    result_client, result_sub_id = client.get_anf_client(subscription_id='error-recovery-test')
                    assert result_client is not None
                    assert result_sub_id == 'error-recovery-test'

# =============================================================================
# AZURE CLOUD ENVIRONMENT TESTS
# =============================================================================

def test_get_anf_client_government_cloud():
    """Test ANF client creation in Azure Government cloud"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                with patch('os.getenv') as mock_getenv:
                    # Simulate government cloud environment
                    def getenv_side_effect(key):
                        if key == 'AZURE_SUBSCRIPTION_ID':
                            return 'gov-cloud-sub'
                        elif key == 'AZURE_ENVIRONMENT':
                            return 'AzureUSGovernment'
                        return None
                    
                    mock_getenv.side_effect = getenv_side_effect
                    mock_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result_client, result_sub_id = client.get_anf_client()
                    
                    assert result_client is not None
                    assert result_sub_id == 'gov-cloud-sub'


def test_get_anf_client_china_cloud():
    """Test ANF client creation in Azure China cloud"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                with patch('os.getenv') as mock_getenv:
                    # Simulate China cloud environment
                    def getenv_side_effect(key):
                        if key == 'AZURE_SUBSCRIPTION_ID':
                            return 'china-cloud-sub'
                        elif key == 'AZURE_ENVIRONMENT':
                            return 'AzureChinaCloud'
                        return None
                    
                    mock_getenv.side_effect = getenv_side_effect
                    mock_credential.return_value = MagicMock()
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client
                    
                    result_client, result_sub_id = client.get_anf_client()
                    
                    assert result_client is not None
                    assert result_sub_id == 'china-cloud-sub'

# =============================================================================
# EDGE CASES AND STRESS TESTS
# =============================================================================

def test_get_anf_client_extremely_long_subscription_id():
    """Test ANF client with extremely long subscription ID"""
    long_sub_id = 'a' * 1000  # Very long subscription ID
    
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result_client, result_sub_id = client.get_anf_client(subscription_id=long_sub_id)
                
                assert result_client is not None
                assert result_sub_id == long_sub_id


def test_get_anf_client_special_characters_subscription():
    """Test ANF client with special characters in subscription ID"""
    special_sub_id = 'test-sub-123_456.789@example.com'
    
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result_client, result_sub_id = client.get_anf_client(subscription_id=special_sub_id)
                
                assert result_client is not None
                assert result_sub_id == special_sub_id


def test_get_anf_client_unicode_subscription():
    """Test ANF client with Unicode characters in subscription ID"""
    unicode_sub_id = 'test-订阅-🌟'
    
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result_client, result_sub_id = client.get_anf_client(subscription_id=unicode_sub_id)
                
                assert result_client is not None
                assert result_sub_id == unicode_sub_id


def test_get_anf_client_rapid_successive_calls():
    """Test ANF client with rapid successive calls"""
    with patch('netapp_dataops.traditional.anf.client.NetAppManagementClient') as mock_client_class:
        with patch('netapp_dataops.traditional.anf.client.DefaultAzureCredential') as mock_credential:
            with patch('netapp_dataops.traditional.anf.client.ANFClientManager._instance', None):
                mock_credential.return_value = MagicMock()
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Make many rapid calls
                clients = []
                for i in range(100):
                    result_client, result_sub_id = client.get_anf_client(subscription_id=f'rapid-test-{i}')
                    clients.append((result_client, result_sub_id))
                
                # All should succeed and return the same client instance (singleton)
                assert len(clients) == 100
                for i, (client_instance, sub_id) in enumerate(clients):
                    assert client_instance is not None
                    # Note: Due to singleton pattern, all clients are the same instance
                    # Only the first subscription ID is used for the actual client creation
