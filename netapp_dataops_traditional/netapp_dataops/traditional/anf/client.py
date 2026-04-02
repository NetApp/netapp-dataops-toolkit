"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Client Management
This module handles Azure client authentication and management for ANF operations.

Authentication is handled via DefaultAzureCredential, which automatically chains
through the following methods (in order) without requiring environment variables:
  1. Managed Identity (production: Azure VMs, AKS, App Service, etc.)
  2. Workload Identity (Kubernetes with Azure AD Workload Identity)
  3. Azure CLI ('az login' for local development)
  4. Azure Developer CLI, VS Code, PowerShell, and others

No secrets or environment variables are required. For local development, run:
  az login --tenant <TENANT_ID>
  az account set --subscription <SUBSCRIPTION_ID>
"""

from typing import Tuple, Optional
from azure.identity import DefaultAzureCredential
from azure.mgmt.netapp import NetAppManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.core.exceptions import ClientAuthenticationError

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)


class ANFClientManager:
    """Singleton class for managing Azure NetApp Files client connections."""

    _instance: Optional['ANFClientManager'] = None
    _client: Optional[NetAppManagementClient] = None
    _subscription_id: Optional[str] = None

    def __new__(cls) -> 'ANFClientManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_client(self, subscription_id: str, credential: DefaultAzureCredential, print_output: Optional[bool] = False) -> NetAppManagementClient:
        """
        Get or create an authenticated NetApp Management Client using DefaultAzureCredential.
        Re-creates the client if the subscription ID has changed.
        """
        if self._client is None or self._subscription_id != subscription_id:
            if self._client is not None and self._subscription_id != subscription_id:
                if print_output:
                    logger.info(f"Subscription changed from '{self._subscription_id}' to '{subscription_id}'. Re-initializing ANF client.")
            try:
                self._client = NetAppManagementClient(credential, subscription_id)
                self._subscription_id = subscription_id
            except Exception as e:
                raise ClientAuthenticationError(f"Failed to initialize ANF client: {str(e)}")

        return self._client


def get_anf_client(print_output: bool = False) -> Tuple[NetAppManagementClient, str]:
    """
    Convenience function to get an authenticated ANF client.

    Uses DefaultAzureCredential for authentication and SubscriptionClient to
    resolve the active subscription ID — no dependency on the az CLI at runtime.
    """
    try:
        credential = DefaultAzureCredential()

        # Resolve the active subscription via the Azure SDK (no az CLI required)
        subscription_client = SubscriptionClient(credential)
        subscriptions = list(subscription_client.subscriptions.list())

        if not subscriptions:
            raise ClientAuthenticationError(
                "No Azure subscriptions found for the authenticated identity. "
                "Ensure the credential has access to at least one subscription."
            )

        # Use the first available subscription (respects az account set via CLI credential)
        subscription = subscriptions[0]
        subscription_id = subscription.subscription_id

        if print_output:
            logger.info(f"Connected to ANF via Active Subscription: {subscription.display_name} ({subscription_id})")

    except ClientAuthenticationError:
        raise
    except Exception as e:
        raise ClientAuthenticationError(
            f"Failed to authenticate with Azure: {str(e)}\n"
            "Please run: az login or az login --tenant <TENANT_ID>\n"
        )
    manager = ANFClientManager()
    client = manager.get_client(subscription_id, credential, print_output=print_output)

    return client, subscription_id

