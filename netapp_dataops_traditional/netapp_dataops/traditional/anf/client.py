"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Client Management
This module handles Azure client authentication and management for ANF operations.
"""

from typing import Tuple, Optional
from azure.identity import AzureCliCredential
# Required: pip install azure-mgmt-resource-subscriptions
from azure.mgmt.resource.subscriptions import SubscriptionClient
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
    
    def get_client(self, subscription_id: str, print_output: bool = False) -> NetAppManagementClient:
        """
        Get or create an authenticated NetApp Management Client.
        """
        if self._client is None or self._client._config.subscription_id != subscription_id:
            # Use AzureCliCredential to specifically respect 'az login' and 'az account set'
            credential = AzureCliCredential()
            try:
                self._client = NetAppManagementClient(credential, subscription_id)
            except Exception as e:
                raise ClientAuthenticationError(f"Failed to initialize ANF client: {str(e)}")
        
        return self._client


def get_anf_client(print_output: bool = False) -> Tuple[NetAppManagementClient, str]:
    """
    Convenience function to get an authenticated ANF client.
    Automatically fetches the active Subscription ID and Tenant ID from the 'az account show' context.
    """
    import subprocess
    import json
    
    try:
        # Get the currently active subscription from Azure CLI
        # This respects 'az account set --subscription <id>'
        result = subprocess.run(
            ['az', 'account', 'show'],
            capture_output=True,
            text=True,
            check=True
        )
        
        account_info = json.loads(result.stdout)
        subscription_id = account_info['id']
        tenant_id = account_info['tenantId']
        subscription_name = account_info['name']
        
        if print_output:
            logger.info(f"Detected Tenant from CLI: {tenant_id}")
            logger.info(f"Connected to ANF via Active Subscription: {subscription_name} ({subscription_id})")
    
    except subprocess.CalledProcessError as e:
        raise ClientAuthenticationError(
            f"Failed to get active subscription from Azure CLI: {e.stderr}\n"
            "Please run: az login --tenant <TENANT_ID>"
        )
    except json.JSONDecodeError as e:
        raise ClientAuthenticationError(f"Failed to parse Azure CLI output: {str(e)}")
    except FileNotFoundError:
        raise ClientAuthenticationError(
            "Azure CLI (az) not found. Please install it from: "
            "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        )
    
    # Use AzureCliCredential with the detected subscription
    manager = ANFClientManager()
    client = manager.get_client(subscription_id, print_output=print_output)
    
    return client, subscription_id
