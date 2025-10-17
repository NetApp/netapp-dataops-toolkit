"""
NetApp DataOps Toolkit - Azure NetApp Files (ANF) Volume Management

This module provides volume management operations for Azure NetApp Files.
"""

from typing import Dict, List, Optional, Any
from azure.mgmt.netapp.models import (
    Volume, 
    VolumePropertiesExportPolicy,
    ExportPolicyRule,
    VolumePropertiesDataProtection
)
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from .client import get_anf_client
from .base import _serialize, validate_required_params

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

def create_volume(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    location: str,
    creation_token: str,
    usage_threshold: int,
    protocol_types: list,
    virtual_network_name: str,
    subnet_name: str = "default",
    service_level: str = None,
    tags: dict = None,
    zones: list = None,
    export_policy_rules: list = None,
    security_style: str = None,
    smb_encryption: bool = None,
    smb_continuously_available: bool = None,
    throughput_mibps: float = None,
    volume_type: str = None,
    data_protection: list = None,
    is_default_quota_enabled: bool = None,
    default_user_quota_in_ki_bs: int = None,
    default_group_quota_in_ki_bs: int = None,
    unix_permissions: str = None,
    avs_data_store: str = None,
    is_large_volume: bool = None,
    kerberos_enabled: bool = None,
    ldap_enabled: bool = None,
    cool_access: bool = None,
    coolness_period: int = None,
    snapshot_directory_visible: bool = None,
    network_features: str = None,
    encryption_key_source: str = None,
    enable_subvolumes: str = None,
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Create a new Azure NetApp Files volume within the capacity pool.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool
        volume_name (str):
            Required. The name of the volume.
        location (str):
            Required. Azure region (e.g., "eastus").
        creation_token (str):
            Required. A unique file path for the volume. Used when creating mount targets.
        usage_threshold (int):
            Required. Volume quota in bytes. Maximum storage quota allowed for a file system in bytes.
            This is a soft quota used for alerting only. For regular volumes, valid values are in the range 50GiB to 100TiB.
            For large volumes, valid values are in the range 100TiB to 500TiB, and on an exceptional basis, from to 2400GiB to 2400TiB.
            Values expressed in bytes as multiples of 1 GiB.
        protocol_types (List[str]):
            Required. List of protocol types (NFSv3, NFSv4.1, CIFS).
        virtual_network_name (str):
            Required. The name of the virtual network to which the volume will be connected.
        subnet_name (str):
            Optional. The name of a delegated Azure subnet to construct the Azure Resource ID for a delegated subnet.
            If not provided, the default subnet will be used.
        service_level (str):
            Optional. Service level (Standard, Premium, Ultra, StandardZRS, Flexible).
            Defaults to Premium.
        tags (Dict[str, str]):
            Optional. Resource tags.
            Defaults to empty dictionary.
        zones (List[str]):
            Optional. Availability zones.
            Defaults to empty list.
        export_policy (List[Dict[str, Any]]):
            Optional. List of export policy rule dictionaries. Each dictionary should contain export policy rule parameters.
            Expected keys in each rule dictionary:
                - rule_index (int): The index of the rule (defaults to position in list + 1)
                - unix_read_only (bool): Unix read only access (defaults to False)
                - unix_read_write (bool): Unix read write access (defaults to True)
                - cifs (bool): CIFS protocol access (defaults to False)
                - nfsv3 (bool): NFSv3 protocol access (defaults based on protocol_types)
                - nfsv41 (bool): NFSv4.1 protocol access (defaults based on protocol_types)
                - allowed_clients (str): Allowed client specification (defaults to "0.0.0.0/0")
                - has_root_access (bool): Root access (defaults to True)
                - kerberos5_read_only (bool): Kerberos5 read only (defaults to False)
                - kerberos5_read_write (bool): Kerberos5 read write (defaults to False)
                - kerberos5_i_read_only (bool): Kerberos5i read only (defaults to False)
                - kerberos5_i_read_write (bool): Kerberos5i read write (defaults to False)
                - kerberos5_p_read_only (bool): Kerberos5p read only (defaults to False)
                - kerberos5_p_read_write (bool): Kerberos5p read write (defaults to False)
                - chown_mode (str): Chown mode (defaults to "Restricted")
            Defaults to None. If not provided and using NFS, a default export policy will be created.
        security_style (str):
            Optional. The security style of volume, default unix, defaults to ntfs for dual protocol or CIFS protocol. Known values are: "ntfs" and "unix".
            Defaults to unix.
        smb_encryption (bool):
            Optional. Enables encryption for in-flight smb3 data. Only applicable for SMB/DualProtocol volume. To be used with swagger version 2020-08-01 or later.
            Defaults to False.
        smb_continuously_available (bool):
            Optional. Enables continuously available share property for smb volume. Only applicable for SMB volume.
            Defaults to False.
        throughput_mibps (int):
            Optional. Maximum throughput in MiB/s that can be achieved by this volume and this will be accepted as input only for manual qosType volume.
            Defaults to 0.
        volume_type (str):
            Optional. What type of volume is this. For destination volumes in Cross Region Replication, set type to DataProtection.
            Defaults to empty string.
        data_protection (Dict[str, Any]):
            Optional. DataProtection type volumes include an object containing details of the replication.
            Defaults to empty dictionary.
        is_default_quota_enabled (bool):
            Optional. Specifies if default quota is enabled for the volume.
            Defaults to False.
        default_user_quota_in_ki_bs (int):
            Optional. Default user quota in KiBs.
            Defaults to 0.
        default_group_quota_in_ki_bs (int):
            Optional. Default group quota in KiBs.
            Defaults to 0.
        unix_permissions (str):
            Optional. UNIX permissions in octal 4 digit format.
            Defaults to "0770".
        avs_data_store (str):
            Optional. Specifies whether the volume is enabled for Azure VMware Solution (AVS) datastore purpose. Known values are: "Enabled" and "Disabled".
            Default value: Disabled
        is_large_volume (bool):
            Optional. Specifies whether volume is a Large Volume or Regular Volume.
            Defaults to False.
        kerberos_enabled (bool):
            Optional. Describe if a volume is KerberosEnabled. To be use with swagger version 2020-05-01 or later.
            Defaults to False.
        ldap_enabled (bool):
            Optional. Specifies whether LDAP is enabled or not for a given NFS volume.
            Defaults to False.
        cool_access (bool):
            Optional. Specifies whether Cool Access (tiering) is enabled for the volume.
            Defaults to False.
        coolness_period (int):
            Optional. Specifies the number of days after which data that is not accessed by clients will be tiered.
            Defaults to 0.
        snapshot_directory_visible (bool):
            Optional. Volume contains read-only snapshot directory.
            If enabled (true) the volume will contain a read-only snapshot directory which provides access to each of the volume's snapshots.
            Defaults to true.
        network_features (str):
            Optional. Network features (Basic, Standard, Basic_Standard, Standard_Basic).
            Defaults to Basic.
        encryption_key_source (str):
            Optional. Key source for encryption (Microsoft.NetApp, Microsoft.KeyVault).
            Defaults to Microsoft.NetApp.
        enable_subvolumes (str):
            Optional. Flag indicating whether subvolume operations are enabled on the volume. Known values are: "Enabled" and "Disabled".
            Defaults to Disabled.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and volume details

    Raises:
        ResourceExistsError: If the volume already exists
        Exception: For other errors during volume creation
    """

    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name,
        volume_name=volume_name,
        location=location,
        creation_token=creation_token,
        usage_threshold=usage_threshold,
        protocol_types=protocol_types,
        virtual_network_name=virtual_network_name
    )

    try:
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # Construct subnet ID from provided parameters
        subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/virtualNetworks/{virtual_network_name}/subnets/{subnet_name}"
        
        # Construct export policy from provided list or create default for NFS
        export_policy = None
        if export_policy_rules is not None:
            # Construct export policy from provided list of rules
            export_rules = []
            for i, rule_dict in enumerate(export_policy_rules):
                # Set default values if not provided in the rule dictionary
                rule_params = {
                    'rule_index': rule_dict.get('rule_index', i + 1),
                    'unix_read_only': rule_dict.get('unix_read_only', False),
                    'unix_read_write': rule_dict.get('unix_read_write', True),
                    'cifs': rule_dict.get('cifs', False),
                    'nfsv3': rule_dict.get('nfsv3', "NFSv3" in protocol_types),
                    'nfsv41': rule_dict.get('nfsv41', "NFSv4.1" in protocol_types),
                    'allowed_clients': rule_dict.get('allowed_clients', '0.0.0.0/0'),
                    'has_root_access': rule_dict.get('has_root_access', True),
                    'kerberos5_read_only': rule_dict.get('kerberos5_read_only', False),
                    'kerberos5_read_write': rule_dict.get('kerberos5_read_write', False),
                    'kerberos5_i_read_only': rule_dict.get('kerberos5_i_read_only', False),
                    'kerberos5_i_read_write': rule_dict.get('kerberos5_i_read_write', False),
                    'kerberos5_p_read_only': rule_dict.get('kerberos5_p_read_only', False),
                    'kerberos5_p_read_write': rule_dict.get('kerberos5_p_read_write', False),
                    'chown_mode': rule_dict.get('chown_mode', 'Restricted')
                }
                export_rules.append(ExportPolicyRule(**rule_params))
            
            export_policy = VolumePropertiesExportPolicy(rules=export_rules)
            
        elif any(proto in protocol_types for proto in ["NFSv3", "NFSv4.1"]):
            # Create default export policy for NFS volumes
            export_policy = VolumePropertiesExportPolicy(
                rules=[
                    ExportPolicyRule(
                        rule_index=1,
                        unix_read_only=False,
                        unix_read_write=True,
                        cifs=False,
                        nfsv3="NFSv3" in protocol_types,
                        nfsv41="NFSv4.1" in protocol_types,
                        allowed_clients="0.0.0.0/0",
                        has_root_access=True,
                        kerberos5_read_only=False,
                        kerberos5_read_write=False,
                        kerberos5_i_read_only=False,
                        kerberos5_i_read_write=False,
                        kerberos5_p_read_only=False,
                        kerberos5_p_read_write=False,
                        chown_mode='Restricted'
                    )
                ]
            )

        # Build volume properties
        volume_properties = {
            'location': location,
            'creation_token': creation_token,
            'subnet_id': subnet_id,
            'usage_threshold': usage_threshold,
            'service_level': service_level,
            'protocol_types': protocol_types,
            'security_style': security_style,
            'smb_encryption': smb_encryption,
            'smb_continuously_available': smb_continuously_available,
            'is_default_quota_enabled': is_default_quota_enabled,
            'default_user_quota_in_ki_bs': default_user_quota_in_ki_bs,
            'default_group_quota_in_ki_bs': default_group_quota_in_ki_bs,
            'avs_data_store': avs_data_store,
            'is_large_volume': is_large_volume,
            'kerberos_enabled': kerberos_enabled,
            'ldap_enabled': ldap_enabled,
            'cool_access': cool_access,
            'snapshot_directory_visible': snapshot_directory_visible,
            'network_features': network_features,
            'encryption_key_source': encryption_key_source,
            'enable_subvolumes': enable_subvolumes
        }
        
        # Add optional parameters if provided
        if tags:
            volume_properties['tags'] = tags
        if zones:
            volume_properties['zones'] = zones
        if export_policy:
            volume_properties['export_policy'] = export_policy
        if throughput_mibps:
            volume_properties['throughput_mibps'] = throughput_mibps
        if volume_type:
            volume_properties['volume_type'] = volume_type
        if data_protection:
            volume_properties['data_protection'] = data_protection
        if unix_permissions:
            volume_properties['unix_permissions'] = unix_permissions
        if coolness_period:
            volume_properties['coolness_period'] = coolness_period
        
        # Create the volume object
        volume = Volume(**volume_properties)
        
        # Create the volume
        poller = client.volumes.begin_create_or_update(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            body=volume
        )

        if print_output:
            logger.info("Creating volume...")
        
        # Wait for completion and get result
        result = poller.result()

        if print_output:
            logger.info(f"Volume created:\n{result}")

        return {"status": "success", "details": _serialize(result)}
       
    except ResourceExistsError as e:
        if print_output:
            logger.error(f"Volume '{volume_name}' already exists: {str(e)}")
        return {"status": "error", "details": str(e)}
    except Exception as e:
        if print_output:
            logger.error(f"Failed to create volume: {str(e)}")
        return {"status": "error", "details": str(e)}


def clone_volume(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    source_volume_name: str,
    volume_name: str,
    location: str,
    creation_token: str,
    snapshot_name: str,
    virtual_network_name: str,
    subnet_name: str = "default",
    service_level: str = None,
    protocol_types: list = None,
    tags: dict = None,
    zones: list = None,
    export_policy_rules: list = None,
    security_style: str = None,
    smb_encryption: bool = None,
    smb_continuously_available: bool = None,
    throughput_mibps: float = None,
    volume_type: str = None,
    data_protection: list = None,
    is_default_quota_enabled: bool = None,
    default_user_quota_in_ki_bs: int = None,
    default_group_quota_in_ki_bs: int = None,
    unix_permissions: str = None,
    avs_data_store: str = None,
    is_large_volume: bool = None,
    kerberos_enabled: bool = None,
    ldap_enabled: bool = None,
    cool_access: bool = None,
    coolness_period: int = None,
    snapshot_directory_visible: bool = None,
    network_features: str = None,
    encryption_key_source: str = None,
    enable_subvolumes: str = None,
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Clone an existing Azure NetApp Files volume from a snapshot.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool.
        volume_name (str):
            Required. The name of the new clone volume.
        location (str):
            Required. Azure region (e.g., "eastus").
        creation_token (str):
            Required. A unique file path for the volume. Used when creating mount targets.
        snapshot_name (str):
            Required. Name of the snapshot to clone from.
        virtual_network_name (str):
            Required. The name of the virtual network to which the volume will be connected.
        subnet_name (str):
            Optional. The name of a delegated Azure subnet to construct the Azure Resource ID for a delegated subnet.
            If not provided, the default subnet will be used.
        service_level (str):
            Optional. Service level (Standard, Premium, Ultra, StandardZRS, Flexible).
            Defaults to Premium.
        protocol_types (List[str]):
            Optional. List of protocol types (NFSv3, NFSv4.1, CIFS).
            Defaults to ["NFSv3"] if not provided.
        tags (Dict[str, str]):
            Optional. Resource tags.
            Defaults to None.
        zones (List[str]):
            Optional. Availability zones.
            Defaults to None.
        export_policy_rules (List[Dict[str, Any]]):
            Optional. List of export policy rule dictionaries. Each dictionary should contain export policy rule parameters.
            Expected keys in each rule dictionary:
                - rule_index (int): The index of the rule (defaults to position in list + 1)
                - unix_read_only (bool): Unix read only access (defaults to False)
                - unix_read_write (bool): Unix read write access (defaults to True)
                - cifs (bool): CIFS protocol access (defaults to False)
                - nfsv3 (bool): NFSv3 protocol access (defaults based on protocol_types)
                - nfsv41 (bool): NFSv4.1 protocol access (defaults based on protocol_types)
                - allowed_clients (str): Allowed client specification (defaults to "0.0.0.0/0")
                - has_root_access (bool): Root access (defaults to True)
                - kerberos5_read_only (bool): Kerberos5 read only (defaults to False)
                - kerberos5_read_write (bool): Kerberos5 read write (defaults to False)
                - kerberos5_i_read_only (bool): Kerberos5i read only (defaults to False)
                - kerberos5_i_read_write (bool): Kerberos5i read write (defaults to False)
                - kerberos5_p_read_only (bool): Kerberos5p read only (defaults to False)
                - kerberos5_p_read_write (bool): Kerberos5p read write (defaults to False)
                - chown_mode (str): Chown mode (defaults to "Restricted")
            Defaults to None. If not provided and using NFS, a default export policy will be created.
        security_style (str):
            Optional. The security style of volume, default unix, defaults to ntfs for dual protocol or CIFS protocol. Known values are: "ntfs" and "unix".
            Defaults to unix.
        smb_encryption (bool):
            Optional. Enables encryption for in-flight smb3 data. Only applicable for SMB/DualProtocol volume. To be used with swagger version 2020-08-01 or later.
            Defaults to False.
        smb_continuously_available (bool):
            Optional. Enables continuously available share property for smb volume. Only applicable for SMB volume.
            Defaults to False.
        throughput_mibps (int):
            Optional. Maximum throughput in MiB/s that can be achieved by this volume and this will be accepted as input only for manual qosType volume.
            Defaults to None.
        volume_type (str):
            Optional. What type of volume is this. For destination volumes in Cross Region Replication, set type to DataProtection.
            Defaults to None.
        data_protection (List[Dict[str, Any]]):
            Optional. DataProtection type volumes include an object containing details of the replication.
            Defaults to None.
        is_default_quota_enabled (bool):
            Optional. Specifies if default quota is enabled for the volume.
            Defaults to False.
        default_user_quota_in_ki_bs (int):
            Optional. Default user quota in KiBs.
            Defaults to 0.
        default_group_quota_in_ki_bs (int):
            Optional. Default group quota in KiBs.
            Defaults to 0.
        unix_permissions (str):
            Optional. UNIX permissions in octal 4 digit format.
            Defaults to "0777".
        avs_data_store (str):
            Optional. Specifies whether the volume is enabled for Azure VMware Solution (AVS) datastore purpose. Known values are: "Enabled" and "Disabled".
            Default value: Disabled
        is_large_volume (bool):
            Optional. Specifies whether volume is a Large Volume or Regular Volume.
            Defaults to False.
        kerberos_enabled (bool):
            Optional. Describe if a volume is KerberosEnabled. To be use with swagger version 2020-05-01 or later.
            Defaults to False.
        ldap_enabled (bool):
            Optional. Specifies whether LDAP is enabled or not for a given NFS volume.
            Defaults to False.
        cool_access (bool):
            Optional. Specifies whether Cool Access (tiering) is enabled for the volume.
            Defaults to False.
        coolness_period (int):
            Optional. Specifies the number of days after which data that is not accessed by clients will be tiered.
            Defaults to None.
        snapshot_directory_visible (bool):
            Optional. Volume contains read-only snapshot directory.
            If enabled (true) the volume will contain a read-only snapshot directory which provides access to each of the volume's snapshots.
            Defaults to true.
        network_features (str):
            Optional. Network features (Basic, Standard, Basic_Standard, Standard_Basic)
            Defaults to Basic.
        encryption_key_source (str):
            Optional. Key source for encryption (Microsoft.NetApp, Microsoft.KeyVault)
            Defaults to Microsoft.NetApp.
        enable_subvolumes (bool):
            Optional. Flag indicating whether subvolume operations are enabled on the volume. Known values are: "Enabled" and "Disabled".
            Defaults to Disabled.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and volume details

    Raises:
        ResourceExistsError: If the volume already exists
        Exception: For other errors during volume cloning
    """

    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name,
        source_volume_name=source_volume_name,
        volume_name=volume_name,
        location=location,
        creation_token=creation_token,
        snapshot_name=snapshot_name,
        virtual_network_name=virtual_network_name
    )

    try:
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # Construct subnet ID from provided parameters
        subnet_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/virtualNetworks/{virtual_network_name}/subnets/{subnet_name}"

        # Construct snapshot ID from provided parameters
        snapshot_id = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.NetApp/netAppAccounts/{account_name}/capacityPools/{pool_name}/volumes/{source_volume_name}/snapshots/{snapshot_name}"

        # Set default protocol types and get usage_threshold from source volume if not provided
        usage_threshold = None
        if protocol_types is None:
            # Try to get protocol types and usage_threshold from the source volume
            try:
                source_volume = client.volumes.get(
                    resource_group_name=resource_group_name,
                    account_name=account_name,
                    pool_name=pool_name,
                    volume_name=source_volume_name
                )
                if hasattr(source_volume, 'protocol_types') and source_volume.protocol_types:
                    protocol_types = source_volume.protocol_types
                    logger.info(f"Retrieved protocol types from source volume '{source_volume_name}': {protocol_types}")
                else:
                    logger.warning(f"No protocol types found for source volume '{source_volume_name}', using default NFSv3")
                    protocol_types = ["NFSv3"]
                
                # Get usage_threshold from source volume
                if hasattr(source_volume, 'usage_threshold') and source_volume.usage_threshold:
                    usage_threshold = source_volume.usage_threshold
                    logger.info(f"Retrieved usage threshold from source volume '{source_volume_name}': {usage_threshold}")
                else:
                    logger.warning(f"No usage threshold found for source volume '{source_volume_name}', using default 100 GiB")
                    usage_threshold = 107374182400  # 100 GiB default
                    
            except Exception as e:
                logger.warning(f"Failed to get details from source volume '{source_volume_name}': {str(e)}, using defaults")
                protocol_types = ["NFSv3"]
                usage_threshold = 107374182400  # 100 GiB default
        else:
            # If protocol_types are provided, still need to get usage_threshold from source volume
            try:
                source_volume = client.volumes.get(
                    resource_group_name=resource_group_name,
                    account_name=account_name,
                    pool_name=pool_name,
                    volume_name=source_volume_name
                )
                if hasattr(source_volume, 'usage_threshold') and source_volume.usage_threshold:
                    usage_threshold = source_volume.usage_threshold
                    logger.info(f"Retrieved usage threshold from source volume '{source_volume_name}': {usage_threshold}")
                else:
                    logger.warning(f"No usage threshold found for source volume '{source_volume_name}', using default 100 GiB")
                    usage_threshold = 107374182400  # 100 GiB default
            except Exception as e:
                logger.warning(f"Failed to get usage threshold from source volume '{source_volume_name}': {str(e)}, using default 100 GiB")
                usage_threshold = 107374182400  # 100 GiB default
        
        # Construct export policy from provided list or create default for NFS
        export_policy = None
        if export_policy_rules is not None:
            # Construct export policy from provided list of rules
            export_rules = []
            for i, rule_dict in enumerate(export_policy_rules):
                # Set default values if not provided in the rule dictionary
                rule_params = {
                    'rule_index': rule_dict.get('rule_index', i + 1),
                    'unix_read_only': rule_dict.get('unix_read_only', False),
                    'unix_read_write': rule_dict.get('unix_read_write', True),
                    'cifs': rule_dict.get('cifs', False),
                    'nfsv3': rule_dict.get('nfsv3', "NFSv3" in protocol_types),
                    'nfsv41': rule_dict.get('nfsv41', "NFSv4.1" in protocol_types),
                    'allowed_clients': rule_dict.get('allowed_clients', '0.0.0.0/0'),
                    'has_root_access': rule_dict.get('has_root_access', True),
                    'kerberos5_read_only': rule_dict.get('kerberos5_read_only', False),
                    'kerberos5_read_write': rule_dict.get('kerberos5_read_write', False),
                    'kerberos5_i_read_only': rule_dict.get('kerberos5_i_read_only', False),
                    'kerberos5_i_read_write': rule_dict.get('kerberos5_i_read_write', False),
                    'kerberos5_p_read_only': rule_dict.get('kerberos5_p_read_only', False),
                    'kerberos5_p_read_write': rule_dict.get('kerberos5_p_read_write', False),
                    'chown_mode': rule_dict.get('chown_mode', 'Restricted')
                }
                export_rules.append(ExportPolicyRule(**rule_params))
            
            export_policy = VolumePropertiesExportPolicy(rules=export_rules)
            
        elif any(proto in protocol_types for proto in ["NFSv3", "NFSv4.1"]):
            # Create default export policy for NFS volumes
            export_policy = VolumePropertiesExportPolicy(
                rules=[
                    ExportPolicyRule(
                        rule_index=1,
                        unix_read_only=False,
                        unix_read_write=True,
                        cifs=False,
                        nfsv3="NFSv3" in protocol_types,
                        nfsv41="NFSv4.1" in protocol_types,
                        allowed_clients="0.0.0.0/0",
                        has_root_access=True,
                        kerberos5_read_only=False,
                        kerberos5_read_write=False,
                        kerberos5_i_read_only=False,
                        kerberos5_i_read_write=False,
                        kerberos5_p_read_only=False,
                        kerberos5_p_read_write=False,
                        chown_mode='Restricted'
                    )
                ]
            )
        
        # Build volume properties
        volume_properties = {
            'location': location,
            'creation_token': creation_token,
            'subnet_id': subnet_id,
            'usage_threshold': usage_threshold,
            'service_level': service_level,
            'protocol_types': protocol_types,
            'security_style': security_style,
            'smb_encryption': smb_encryption,
            'smb_continuously_available': smb_continuously_available,
            'is_default_quota_enabled': is_default_quota_enabled,
            'default_user_quota_in_ki_bs': default_user_quota_in_ki_bs,
            'default_group_quota_in_ki_bs': default_group_quota_in_ki_bs,
            'avs_data_store': avs_data_store,
            'is_large_volume': is_large_volume,
            'kerberos_enabled': kerberos_enabled,
            'ldap_enabled': ldap_enabled,
            'cool_access': cool_access,
            'snapshot_directory_visible': snapshot_directory_visible,
            'network_features': network_features,
            'encryption_key_source': encryption_key_source,
            'enable_subvolumes': enable_subvolumes
        }
        
        # Add snapshot reference for snapshot-based cloning
        if snapshot_id:
            # For snapshot-based cloning in Azure NetApp Files, use snapshot_id parameter
            # Based on Azure SDK samples, snapshot_id goes directly in Volume object
            volume_properties['snapshot_id'] = snapshot_id
        
        # Add optional parameters if provided
        if tags:
            volume_properties['tags'] = tags
        if zones:
            volume_properties['zones'] = zones
        if export_policy:
            volume_properties['export_policy'] = export_policy
        if throughput_mibps:
            volume_properties['throughput_mibps'] = throughput_mibps
        if volume_type:
            volume_properties['volume_type'] = volume_type
        if data_protection:
            volume_properties['data_protection'] = data_protection
        if unix_permissions:
            volume_properties['unix_permissions'] = unix_permissions
        if coolness_period:
            volume_properties['coolness_period'] = coolness_period
        
        # Create the volume object
        volume = Volume(**volume_properties)
        
        # Create the clone volume
        poller = client.volumes.begin_create_or_update(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            body=volume
        )

        if print_output:
            logger.info("Cloning volume...")
        
        # Wait for completion and get result
        result = poller.result()

        if print_output:
            logger.info(f"Volume cloned:\n{result}")

        return {"status": "success", "details": _serialize(result)}
            
    except ResourceExistsError as e:
        if print_output:
            logger.error(f"Volume '{volume_name}' already exists: {str(e)}")
        return {"status": "error", "details": str(e)}
    except Exception as e:
        if print_output:
            logger.error(f"Failed to clone volume: {str(e)}")
        return {"status": "error", "details": str(e)}


def delete_volume(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    force_delete: bool = None,
    subscription_id: str = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    Delete an Azure NetApp Files volume.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool.
        volume_name (str):
            Required. The name of the volume.
        force_delete (bool):
            Optional. An option to force delete the volume. 
            Will cleanup resources connected to the particular volume.
            Default value is None.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.
        
    Returns:
        Dictionary with status and operation details

    Raises:
        ResourceNotFoundError: If the volume does not exist
        Exception: For other errors during volume deletion
    """
    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name,
        volume_name=volume_name
    )

    try:
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # Delete the volume
        if force_delete is not None:
            poller = client.volumes.begin_delete(
                resource_group_name=resource_group_name,
                account_name=account_name,
                pool_name=pool_name,
                volume_name=volume_name,
                force_delete=force_delete
            )
        else:
            poller = client.volumes.begin_delete(
                resource_group_name=resource_group_name,
                account_name=account_name,
                pool_name=pool_name,
                volume_name=volume_name
            )

        if print_output:
            logger.info("Deleting volume...")
        
        # Wait for completion
        poller.result()

        if print_output:
            logger.info(f"Volume '{volume_name}' deleted successfully")

        return {"status": "success", "details": f"Volume '{volume_name}' deleted successfully"}
    
    except ResourceNotFoundError as e:
            if print_output:
                logger.error(f"Volume '{volume_name}' not found")
            return {"status": "error", "details": str(e)}
    except Exception as e:
        if print_output:
            logger.error(f"Failed to delete volume: {str(e)}")
        return {"status": "error", "details": str(e)}


def list_volumes(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    subscription_id: Optional[str] = None,
    print_output: bool = False
) -> Dict[str, Any]:
    """
    List all Azure NetApp Files volumes in a capacity pool.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and list of volumes

    Raises:
        Exception: For errors during volume listing
    """
    # Validate input parameters
    validate_required_params(
        resource_group_name=resource_group_name,
        account_name=account_name,
        pool_name=pool_name
    )

    try:
        # Get ANF client and subscription ID (if not provided, will use environment variable)
        client, subscription_id = get_anf_client(subscription_id, print_output=print_output)

        # List all volumes in the pool
        volumes = client.volumes.list(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name
        )

        if print_output:
            logger.info("Listing volumes...")
        
        # Convert to list (since it returns an iterator)
        volume_list = list(volumes)

        if print_output:
            logger.info(f"Volumes fetched: {volume_list}")

        return {"status": "success", "details": volume_list}

    except Exception as e:
        if print_output:
            logger.error(f"Failed to list volumes: {str(e)}")
        return {"status": "error", "details": str(e)}
