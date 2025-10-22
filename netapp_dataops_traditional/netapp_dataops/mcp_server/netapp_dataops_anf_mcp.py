#!/usr/bin/env python3

import logging
import sys
import asyncio
from typing import Optional, Dict, Any
from fastmcp import FastMCP
from netapp_dataops.traditional.anf import (
    create_volume,
    clone_volume, 
    list_volumes,
    create_snapshot,
    list_snapshots,
    create_replication,
    create_data_protection_volume
)

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

mcp = FastMCP("NetApp DataOps ANF Toolkit MCP")

@mcp.tool(name="Create Volume")
async def create_volume_tool(
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
    service_level: Optional[str] = None,
    tags: Optional[dict] = None,
    zones: Optional[list] = None,
    export_policy_rules: Optional[list] = None,
    security_style: Optional[str] = None,
    smb_encryption: Optional[bool] = None,
    smb_continuously_available: Optional[bool] = None,
    throughput_mibps: Optional[float] = None,
    volume_type: Optional[str] = None,
    data_protection: Optional[list] = None,
    is_default_quota_enabled: Optional[bool] = None,
    default_user_quota_in_ki_bs: Optional[int] = None,
    default_group_quota_in_ki_bs: Optional[int] = None,
    unix_permissions: Optional[str] = None,
    avs_data_store: Optional[str] = None,
    is_large_volume: Optional[bool] = None,
    kerberos_enabled: Optional[bool] = None,
    ldap_enabled: Optional[bool] = None,
    cool_access: Optional[bool] = None,
    coolness_period: Optional[int] = None,
    snapshot_directory_visible: Optional[bool] = None,
    network_features: Optional[str] = None,
    encryption_key_source: Optional[str] = None,
    enable_subvolumes: Optional[str] = None,
    subscription_id: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create a new Azure NetApp Files volume within the capacity pool.

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
            Optional. DataProtection type volumes include a list containing details of the replication.
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
            Defaults to None.
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
    try:
        result = create_volume(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            location=location,
            creation_token=creation_token,
            virtual_network_name=virtual_network_name,
            subnet_name=subnet_name,
            usage_threshold=usage_threshold,
            service_level=service_level,
            protocol_types=protocol_types,
            tags=tags,
            zones=zones,
            export_policy_rules=export_policy_rules,
            security_style=security_style,
            smb_encryption=smb_encryption,
            smb_continuously_available=smb_continuously_available,
            throughput_mibps=throughput_mibps,
            volume_type=volume_type,
            data_protection=data_protection,
            is_default_quota_enabled=is_default_quota_enabled,
            default_user_quota_in_ki_bs=default_user_quota_in_ki_bs,
            default_group_quota_in_ki_bs=default_group_quota_in_ki_bs,
            unix_permissions=unix_permissions,
            avs_data_store=avs_data_store,
            is_large_volume=is_large_volume,
            kerberos_enabled=kerberos_enabled,
            ldap_enabled=ldap_enabled,
            cool_access=cool_access,
            coolness_period=coolness_period,
            snapshot_directory_visible=snapshot_directory_visible,
            network_features=network_features,
            encryption_key_source=encryption_key_source,
            enable_subvolumes=enable_subvolumes,
            subscription_id=subscription_id,
            print_output=print_output
        )
        if result['status'] == 'error':
            if print_output:
                logger.error(f"Error creating ANF volume: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if print_output:
            logger.error(f"Error creating ANF volume: {e}")
        return {"status": "error", "details": f"Error creating ANF volume: {e}"}


@mcp.tool(name="Clone Volume")
async def clone_volume_tool(
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
    service_level: Optional[str] = None,
    protocol_types: Optional[list] = None,
    tags: Optional[dict] = None,
    zones: Optional[list] = None,
    export_policy_rules: Optional[list] = None,
    security_style: Optional[str] = None,
    smb_encryption: Optional[bool] = None,
    smb_continuously_available: Optional[bool] = None,
    throughput_mibps: Optional[float] = None,
    volume_type: Optional[str] = None,
    data_protection: Optional[list] = None,
    is_default_quota_enabled: Optional[bool] = None,
    default_user_quota_in_ki_bs: Optional[int] = None,
    default_group_quota_in_ki_bs: Optional[int] = None,
    unix_permissions: Optional[str] = None,
    avs_data_store: Optional[str] = None,
    is_large_volume: Optional[bool] = None,
    kerberos_enabled: Optional[bool] = None,
    ldap_enabled: Optional[bool] = None,
    cool_access: Optional[bool] = None,
    coolness_period: Optional[int] = None,
    snapshot_directory_visible: Optional[bool] = None,
    network_features: Optional[str] = None,
    encryption_key_source: Optional[str] = None,
    enable_subvolumes: Optional[str] = None,
    subscription_id: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to clone an existing Azure NetApp Files volume from a snapshot.
    
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
            Optional. DataProtection type volumes include a list containing details of the replication.
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
    try:
        result = clone_volume(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            source_volume_name=source_volume_name,
            volume_name=volume_name,
            location=location,
            creation_token=creation_token,
            snapshot_name=snapshot_name,
            virtual_network_name=virtual_network_name,
            subnet_name=subnet_name,
            service_level=service_level,
            protocol_types=protocol_types,
            tags=tags,
            zones=zones,
            export_policy_rules=export_policy_rules,
            security_style=security_style,
            smb_encryption=smb_encryption,
            smb_continuously_available=smb_continuously_available,
            throughput_mibps=throughput_mibps,
            volume_type=volume_type,
            data_protection=data_protection,
            is_default_quota_enabled=is_default_quota_enabled,
            default_user_quota_in_ki_bs=default_user_quota_in_ki_bs,
            default_group_quota_in_ki_bs=default_group_quota_in_ki_bs,
            unix_permissions=unix_permissions,
            avs_data_store=avs_data_store,
            is_large_volume=is_large_volume,
            kerberos_enabled=kerberos_enabled,
            ldap_enabled=ldap_enabled,
            cool_access=cool_access,
            coolness_period=coolness_period,
            snapshot_directory_visible=snapshot_directory_visible,
            network_features=network_features,
            encryption_key_source=encryption_key_source,
            enable_subvolumes=enable_subvolumes,
            subscription_id=subscription_id,
            print_output=print_output
        )
        if result['status'] == 'error':
            if print_output:
                logger.error(f"Error cloning ANF volume: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if print_output:
            logger.error(f"Error cloning ANF volume: {e}")
        return {"status": "error", "details": f"Error cloning ANF volume: {e}"}


@mcp.tool(name="List Volumes")
async def list_volumes_tool(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    subscription_id: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to retrieve a list of all Azure NetApp Files volumes in a capacity pool.

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
    try:
        result = list_volumes(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            subscription_id=subscription_id,
            print_output=print_output
        )
        if result['status'] == 'error':
            if print_output:
                logger.error(f"Error listing ANF volumes: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if print_output:
            logger.error(f"Error listing ANF volumes: {e}")
        return {"status": "error", "details": f"Error listing ANF volumes: {e}"}


@mcp.tool(name="Create Snapshot")
async def create_snapshot_tool(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    snapshot_name: str,
    location: str,
    tags: Optional[dict] = None,
    subscription_id: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create a new snapshot for an Azure NetApp Files volume.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account
        pool_name (str):
            Required. The name of the capacity pool.
        volume_name (str):
            Required. The name of the volume.
        snapshot_name (str):
            Required. The name of the snapshot.
        location (str):
            Required. Azure region
        tags (Dict[str, str]):
            Optional. Resource tags.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and snapshot details

    Raises:
        ResourceExistsError: If the snapshot already exists
        ResourceNotFoundError: If the volume does not exist
        Exception: For other errors during snapshot creation
    """
    try:
        result = create_snapshot(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            snapshot_name=snapshot_name,
            location=location,
            tags=tags,
            subscription_id=subscription_id,
            print_output=print_output
        )
        if result['status'] == 'error':
            if print_output:
                logger.error(f"Error creating ANF snapshot: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if print_output:
            logger.error(f"Error creating ANF snapshot: {e}")
        return {"status": "error", "details": f"Error creating ANF snapshot: {e}"}

@mcp.tool(name="List Snapshots")
async def list_snapshots_tool(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    subscription_id: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to retrieve a list of all snapshots for an Azure NetApp Files volume.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool.
        volume_name (str):
            Required. The name of the volume.
        subscription_id (str):
            Optional. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and list of snapshots.

    Raises:
        ResourceNotFoundError: If the volume does not exist.
        Exception: For other errors during snapshot listing.
    """
    try:
        result = list_snapshots(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            subscription_id=subscription_id,
            print_output=print_output
        )
        if result['status'] == 'error':
            if print_output:
                logger.error(f"Error listing ANF snapshots: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if print_output:
            logger.error(f"Error listing ANF snapshots: {e}")
        return {"status": "error", "details": f"Error listing ANF snapshots: {e}"}


@mcp.tool(name="Create Replication")
async def create_replication_tool(
    # Source volume parameters
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    # Destination volume parameters (optional - if not provided, will use remote_volume_resource_id)
    destination_resource_group_name: Optional[str] = None,
    destination_account_name: Optional[str] = None,
    destination_pool_name: Optional[str] = None,
    destination_volume_name: Optional[str] = None,
    destination_location: Optional[str] = None,
    destination_creation_token: Optional[str] = None,
    destination_virtual_network_name: Optional[str] = None,
    destination_subnet_name: Optional[str] = "default",
    destination_zones: Optional[list] = None,
    destination_usage_threshold: Optional[int] = 107374182400,
    destination_service_level: Optional[str] = "Premium",
    # For existing destination volume
    remote_volume_resource_id: Optional[str] = None,
    # Common parameters
    subscription_id: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create a complete cross-region replication setup for Azure NetApp Files.
    
    This function can either:
    1. Create a new data protection volume and authorize replication (provide destination_* parameters)
    2. Authorize replication to an existing data protection volume (provide remote_volume_resource_id)
    
    Args:
        # Source volume parameters (required)
        resource_group_name (str):
            Required. Source volume resource group name.
        account_name (str):
            Required. Source volume NetApp account name.
        pool_name (str):
            Required. Source volume capacity pool name.
        volume_name (str):
            Required. Source volume name.

        # For creating new destination volume:
        destination_resource_group_name (str):
            Required. Destination resource group name.
        destination_account_name (str):
            Optional. Destination NetApp account name. 
        destination_pool_name (str):
            Optional. Destination capacity pool name.
        destination_volume_name (str):
            Optional. Destination volume name.
        destination_location (str):
            Optional. Destination Azure region (must differ from source).
        destination_creation_token (str):
            Optional. Destination volume file path. Must be unique within the account.
        destination_virtual_network_name (str):
            Optional. Destination virtual network name.
        destination_subnet_name (str):
            Optional. Destination subnet name.
            Defaults to "default".
        destination_zones (list):
            Optional. Availability zones for destination volume.
        destination_usage_threshold (int):
            Optional. Destination volume quota in bytes (default: 100 GiB).
        destination_service_level (str):
            Optional. Destination service level (Standard/Premium/Ultra).
            Defaults to "Premium".

        # For existing destination volume:
        remote_volume_resource_id (str):
            Required. Resource ID of existing data protection volume

        subscription_id (str):
            Optional. Azure subscription ID
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and replication setup details

    Raises:
        ValueError: If required parameters are missing or invalid
        ResourceNotFoundError: If source volume does not exist
        Exception: If there is an error during the replication setup process   
    
    Note:
        - Must provide either destination_* parameters OR remote_volume_resource_id
        - Source and destination volumes must be in different Azure regions
        - Destination volume will be created as a data protection volume if creating new
    """
    try:
        result = create_replication(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            destination_resource_group_name=destination_resource_group_name,
            destination_account_name=destination_account_name,
            destination_pool_name=destination_pool_name,
            destination_volume_name=destination_volume_name,
            destination_location=destination_location,
            destination_creation_token=destination_creation_token,
            destination_virtual_network_name=destination_virtual_network_name,
            destination_subnet_name=destination_subnet_name,
            destination_zones=destination_zones,
            destination_usage_threshold=destination_usage_threshold,
            destination_service_level=destination_service_level,
            remote_volume_resource_id=remote_volume_resource_id,
            subscription_id=subscription_id,
            print_output=print_output
        )
        if result['status'] == 'error':
            if print_output:
                logger.error(f"Error creating ANF replication: {result.get('details', 'Unknown error')}")
        return result
    except Exception as e:
        if print_output:
            logger.error(f"Error creating ANF replication: {e}")
        return {"status": "error", "details": f"Error creating ANF replication: {e}"}


@mcp.tool(name="Create Data Protection Volume")
async def create_data_protection_volume_tool(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    volume_name: str,
    location: str,
    creation_token: str,
    virtual_network_name: str,
    subnet_name: str,
    source_volume_resource_id: str,
    zones: Optional[list] = None,
    usage_threshold: Optional[int] = 107374182400,
    service_level: Optional[str] = "Premium",
    subscription_id: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create a data protection volume for cross-region replication.
    
    This creates a destination volume specifically designed for replication. After creating
    this volume, use its resource ID in the "Create Replication" tool to authorize
    replication from the source volume.
    
    Args:
        resource_group_name (str):
            Required. The name of the destination resource group.
        account_name (str):
            Required. The name of the destination NetApp account.
        pool_name (str):
            Required. The name of the destination capacity pool.
        volume_name (str):
            Required. The name of the destination volume.
        location (str):
            Required. Azure region for the destination (must be different from source).
        creation_token (str):
            Required. Unique file path for the destination volume.
        virtual_network_name (str):
            Required. The name of the virtual network to which the volume will be connected.
        subnet_name (str):
            Optional. The name of a delegated Azure subnet to construct the Azure Resource ID for a delegated subnet.
            If not provided, the default subnet will be used.
        source_volume_resource_id (str):
            Required. The resource ID of the source volume to replicate from.
        zones (list):
            Required. List of availability zones for cross-zone replication (e.g., ["1"] or ["1", "2", "3"]).
        usage_threshold (int):
            Required. Volume quota in bytes (default: 100 GiB).
        service_level (str):
            Required. Service level (Standard, Premium, Ultra).
        subscription_id (str):
            Required. Azure subscription ID.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and volume creation details

    Raises:
        ValueError: If required parameters are missing or invalid
        ResourceNotFoundError: If the source volume does not exist
        Exception: If there is an error during volume creation
        
    Note:
        - For cross-zone replication, zones parameter is required
        - After creating this volume, use its resource ID as the remote_volume_resource_id
          parameter in the create_replication function on the source volume
        - Common zone values: ["1"], ["2"], ["3"], or ["1", "2", "3"] for zone redundancy
        - The destination pool must have the same or higher service level as source
    """

    try:
        result = create_data_protection_volume(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            volume_name=volume_name,
            location=location,
            creation_token=creation_token,
            virtual_network_name=virtual_network_name,
            subnet_name=subnet_name,
            source_volume_resource_id=source_volume_resource_id,
            zones=zones,
            usage_threshold=usage_threshold,
            service_level=service_level,
            subscription_id=subscription_id,
            print_output=print_output
        )
        return result
    except Exception as e:
        if print_output:
            logger.error(f"Error creating ANF data protection volume: {e}")
        raise


if __name__ == "__main__":
    try:
        # Sets up basic logging to capture server events and errors
        logging.basicConfig(level=logging.INFO)

        if hasattr(mcp, '_tool_manager'):
            logging.info("Registered ANF tools:")
            logging.info(asyncio.run(mcp._tool_manager.get_tools()))

        # Starts the MCP server using stdio transport for local operation
        mcp.run(transport="stdio")

    except Exception as e:
        # Logs and prints any startup errors, then exits with an error code
        logging.error(f"ANF Server startup failed: {e}")
        sys.exit(1)
