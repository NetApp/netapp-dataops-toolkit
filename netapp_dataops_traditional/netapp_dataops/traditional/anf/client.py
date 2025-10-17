"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Client Management

This module handles Azure client authentication and management for ANF operations.
"""

import os
from typing import Optional, Tuple
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.netapp import NetAppManagementClient
from azure.core.exceptions import ClientAuthenticationError

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

class ANFClientManager:
    """Singleton class for managing Azure NetApp Files client connections."""
    
    _instance: Optional['ANFClientManager'] = None
    _client: Optional[NetAppManagementClient] = None
    
    def __new__(cls) -> 'ANFClientManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self, subscription_id: str, print_output: Optional[bool] = False) -> NetAppManagementClient:
        """
        Get or create an authenticated NetApp Management Client.
        
        Args:
            subscription_id: Azure subscription ID (required).
            
        Returns:
            NetAppManagementClient instance
            
        Raises:
            ClientAuthenticationError: If authentication fails
        """
        if self._client is None:
            # Try to authenticate using various methods
            credential = self._get_credential(print_output=print_output)

            try:
                self._client = NetAppManagementClient(credential, subscription_id)
                # Test the connection by attempting to get subscription details
                # Note: We don't test accounts.list() here since it requires resource_group_name
                # The authentication will be tested when the client is actually used
            except Exception as e:
                raise ClientAuthenticationError(f"Failed to authenticate with Azure: {str(e)}")
        
        return self._client

    def _get_credential(self, print_output: Optional[bool] = False):
        """
        Get Azure credential using the most appropriate method available.
        
        Returns:
            Azure credential instance
        """
        # ALWAYS try service principal authentication first (if environment variables are set)
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET') 
        tenant_id = os.getenv('AZURE_TENANT_ID')

        if print_output:
            logger.debug(f"DEBUG-----: client_id={client_id}, tenant_id={tenant_id}, client_secret={'set' if client_secret else 'not set'}")

        if client_id and client_secret and tenant_id:
            if print_output:
                logger.debug(f"Using ClientSecretCredential with client_id: {client_id}")
            return ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        
        # Fall back to default credential chain (managed identity, CLI, etc.)
        if print_output:
            logger.debug("Using DefaultAzureCredential (service principal env vars not found)")
        return DefaultAzureCredential(exclude_cli_credential=True)  # Exclude Azure CLI to avoid conflicts
    
    def reset_client(self):
        """Reset the client instance to force re-authentication on next use."""
        self._client = None


def get_anf_client(subscription_id: Optional[str] = None, print_output: Optional[bool] = False) -> Tuple[NetAppManagementClient, str]:
    """
    Convenience function to get an authenticated ANF client.
    
    Args:
        subscription_id: Azure subscription ID. If not provided, will try to get from environment.
        
    Returns:
        Tuple of (NetAppManagementClient instance, subscription_id)
    """
    # Get subscription ID from parameter or environment if not provided
    if not subscription_id:
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            raise ValueError(
                "Azure subscription ID must be provided either as parameter or "
                "via AZURE_SUBSCRIPTION_ID environment variable"
            )
    
    manager = ANFClientManager()
    client = manager.get_client(subscription_id, print_output=print_output)
    return client, subscription_id
