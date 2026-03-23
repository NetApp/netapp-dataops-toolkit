#!/usr/bin/env python3

import asyncio
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP
from netapp_dataops.traditional.anf import (
    create_volume,
    clone_volume, 
    list_volumes,
    create_snapshot,
    list_snapshots,
    create_replication,
    create_anf_config
)

from netapp_dataops.logging_utils import setup_logger

logger = setup_logger(__name__)

mcp = FastMCP("NetApp DataOps ANF Toolkit MCP")

@mcp.tool(name="Create_Volume")
async def create_volume_tool(
    volume_name: str,
    creation_token: str,
    usage_threshold: int,
    resource_group_name: Optional[str] = None,
    account_name: Optional[str] = None,
    pool_name: Optional[str] = None,
    location: Optional[str] = None,
    protocol_types: Optional[List[str]] = None,
    virtual_network_name: Optional[str] = None,
    subnet_name: Optional[str] = None,
    service_level: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    zones: Optional[List[str]] = None,
    export_policy_rules: Optional[List[Dict[str, Any]]] = None,
    security_style: Optional[str] = None,
    smb_encryption: Optional[bool] = None,
    smb_continuously_available: Optional[bool] = None,
    throughput_mibps: Optional[float] = None,
    volume_type: Optional[str] = None,
    data_protection: Optional[List[Dict[str, Any]]] = None,
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
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create a new Azure NetApp Files volume within the capacity pool.

    Args:
        volume_name (str):
            Required. The name of the volume.
        creation_token (str):
            Required. A unique file path for the volume. Used when creating mount targets.
        usage_threshold (int):
            Required. Volume quota in bytes. Maximum storage quota allowed for a file system in bytes.
            This is a soft quota used for alerting only. For regular volumes, valid values are in the range 50GiB to 100TiB.
            For large volumes, valid values are in the range 100TiB to 500TiB, and on an exceptional basis, from to 2400GiB to 2400TiB.
            Values expressed in bytes as multiples of 1 GiB.
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        location (str):
            Optional. Azure region (e.g., "eastus"). Will use config default if not provided.
        protocol_types (List[str]):
            Optional. List of protocol types (NFSv3, NFSv4.1, CIFS). Will use config default if not provided.
        virtual_network_name (str):
            Optional. The name of the virtual network to which the volume will be connected. Will use config default if not provided.
        subnet_name (str):
            Optional. The name of a delegated Azure subnet to construct the Azure Resource ID for a delegated subnet.
            Will use config default if not provided, otherwise defaults to "default".
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
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and volume details

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        ResourceExistsError: If the volume already exists
        Exception: For other errors during volume creation
    """
    try:
        result = create_volume(
            volume_name=volume_name,
            creation_token=creation_token,
            usage_threshold=usage_threshold,
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            location=location,
            protocol_types=protocol_types,
            virtual_network_name=virtual_network_name,
            subnet_name=subnet_name,
            service_level=service_level,
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
            print_output=print_output
        )
        if result['status'] == 'error':
            error_message = f"Error creating ANF volume: {result.get('details', 'Unknown error')}"
            logger.error(error_message)
            if print_output:
                print(error_message)
        return result
    except Exception as e:
        error_message = f"Error creating ANF volume: {e}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": f"Error creating ANF volume: {e}"}


@mcp.tool(name="Clone_Volume")
async def clone_volume_tool(
    source_volume_name: str,
    volume_name: str,
    creation_token: str,
    snapshot_name: str,
    resource_group_name: Optional[str] = None,
    account_name: Optional[str] = None,
    pool_name: Optional[str] = None,
    location: Optional[str] = None,
    virtual_network_name: Optional[str] = None,
    subnet_name: Optional[str] = None,
    service_level: Optional[str] = None,
    protocol_types: Optional[List[str]] = None,
    tags: Optional[Dict[str, str]] = None,
    zones: Optional[List[str]] = None,
    export_policy_rules: Optional[List[Dict[str, Any]]] = None,
    security_style: Optional[str] = None,
    smb_encryption: Optional[bool] = None,
    smb_continuously_available: Optional[bool] = None,
    throughput_mibps: Optional[float] = None,
    volume_type: Optional[str] = None,
    data_protection: Optional[List[Dict[str, Any]]] = None,
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
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to clone an existing Azure NetApp Files volume from a snapshot.
    
    Args:
        source_volume_name (str):
            Required. The name of the source volume to clone from.
        volume_name (str):
            Required. The name of the new clone volume.
        creation_token (str):
            Required. A unique file path for the volume. Used when creating mount targets.
        snapshot_name (str):
            Required. Name of the snapshot to clone from.
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        location (str):
            Optional. Azure region (e.g., "eastus"). Will use config default if not provided.
        virtual_network_name (str):
            Optional. The name of the virtual network to which the volume will be connected. Will use config default if not provided.
        subnet_name (str):
            Optional. The name of a delegated Azure subnet to construct the Azure Resource ID for a delegated subnet.
            Will use config default if not provided, otherwise defaults to "default".
        service_level (str):
            Optional. Service level (Standard, Premium, Ultra, StandardZRS, Flexible).
            Defaults to Premium.
        protocol_types (List[str]):
            Optional. List of protocol types (NFSv3, NFSv4.1, CIFS). Will use config default if not provided.
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
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and volume details

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        ResourceExistsError: If the volume already exists
        Exception: For other errors during volume cloning
    """
    try:
        result = clone_volume(
            source_volume_name=source_volume_name,
            volume_name=volume_name,
            creation_token=creation_token,
            snapshot_name=snapshot_name,
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            location=location,
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
            print_output=print_output
        )
        if result['status'] == 'error':
            error_message = f"Error cloning ANF volume: {result.get('details', 'Unknown error')}"
            logger.error(error_message)
            if print_output:
                print(error_message)
        return result
    except Exception as e:
        error_message = f"Error cloning ANF volume: {e}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": f"Error cloning ANF volume: {e}"}


@mcp.tool(name="List_Volumes")
async def list_volumes_tool(
    resource_group_name: Optional[str] = None,
    account_name: Optional[str] = None,
    pool_name: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to retrieve a list of all Azure NetApp Files volumes in a capacity pool.

    Args:
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and list of volumes

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        Exception: For errors during volume listing
    """
    try:
        result = list_volumes(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            print_output=print_output
        )
        if result['status'] == 'error':
            error_message = f"Error listing ANF volumes: {result.get('details', 'Unknown error')}"
            logger.error(error_message)
            if print_output:
                print(error_message)
        return result
    except Exception as e:
        error_message = f"Error listing ANF volumes: {e}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": f"Error listing ANF volumes: {e}"}


@mcp.tool(name="Create_Snapshot")
async def create_snapshot_tool(
    volume_name: str,
    snapshot_name: str,
    resource_group_name: Optional[str] = None,
    account_name: Optional[str] = None,
    pool_name: Optional[str] = None,
    location: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create a new snapshot for an Azure NetApp Files volume.
    
    Args:
        volume_name (str):
            Required. The name of the volume.
        snapshot_name (str):
            Required. The name of the snapshot.
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        location (str):
            Optional. Azure region. Will use config default if not provided.
        tags (Dict[str, str]):
            Optional. Resource tags.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and snapshot details

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        ResourceExistsError: If the snapshot already exists
        ResourceNotFoundError: If the volume does not exist
        Exception: For other errors during snapshot creation
    """
    try:
        result = create_snapshot(
            volume_name=volume_name,
            snapshot_name=snapshot_name,
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            location=location,
            print_output=print_output
        )
        if result['status'] == 'error':
            error_message = f"Error creating ANF snapshot: {result.get('details', 'Unknown error')}"
            logger.error(error_message)
            if print_output:
                print(error_message)
        return result
    except Exception as e:
        error_message = f"Error creating ANF snapshot: {e}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": f"Error creating ANF snapshot: {e}"}

@mcp.tool(name="List_Snapshots")
async def list_snapshots_tool(
    volume_name: str,
    resource_group_name: Optional[str] = None,
    account_name: Optional[str] = None,
    pool_name: Optional[str] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to retrieve a list of all snapshots for an Azure NetApp Files volume.
    
    Args:
        volume_name (str):
            Required. The name of the volume.
        resource_group_name (str):
            Optional. The name of the resource group. Will use config default if not provided.
        account_name (str):
            Optional. The name of the NetApp account. Will use config default if not provided.
        pool_name (str):
            Optional. The name of the capacity pool. Will use config default if not provided.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and list of snapshots.

    Raises:
        InvalidConfigError: If required parameters are missing from both function call and config
        ResourceNotFoundError: If the volume does not exist.
        Exception: For other errors during snapshot listing.
    """
    try:
        result = list_snapshots(
            volume_name=volume_name,
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            print_output=print_output
        )
        if result['status'] == 'error':
            error_message = f"Error listing ANF snapshots: {result.get('details', 'Unknown error')}"
            logger.error(error_message)
            if print_output:
                print(error_message)
        return result
    except Exception as e:
        error_message = f"Error listing ANF snapshots: {e}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": f"Error listing ANF snapshots: {e}"}


@mcp.tool(name="Create_Replication")
async def create_replication_tool(
    # Source volume parameters
    volume_name: str,
    # Destination volume parameters
    destination_resource_group_name: str,
    destination_account_name: str,
    destination_pool_name: str,
    destination_volume_name: str,
    destination_location: str,
    destination_creation_token: str,
    destination_usage_threshold: int,
    destination_protocol_types: List[str],
    destination_virtual_network_name: str,
    destination_subnet_name: str = "default",
    destination_service_level: Optional[str] = None,
    destination_zones: Optional[List[str]] = None,
    # Source volume parameters (optional - will use config defaults)
    resource_group_name: Optional[str] = None,
    account_name: Optional[str] = None,
    pool_name: Optional[str] = None,
    # Common parameters
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create a complete cross-region replication setup for Azure NetApp Files.
    
    Args:
        # Source volume parameters
        volume_name (str):
            Required. Source volume name.
        
        # Destination volume parameters (required - typically in different region/subscription)
        destination_resource_group_name (str):
            Required. Destination resource group name.
        destination_account_name (str):
            Required. Destination NetApp account name. 
        destination_pool_name (str):
            Required. Destination capacity pool name.
        destination_volume_name (str):
            Required. Destination volume name.
        destination_location (str):
            Required. Destination Azure region (must differ from source).
        destination_creation_token (str):
            Required. Destination volume file path. Must be unique within the account.
        destination_usage_threshold (int):
            Required. Destination volume quota in bytes.
            This must be at least as large as the source volume's usage threshold.
        destination_protocol_types (list):
            Required. List of protocol types for destination volume (e.g., ["NFSv4.1"]).
        destination_virtual_network_name (str):
            Required. Destination virtual network name.
        destination_subnet_name (str):
            Optional. Destination subnet name. Defaults to "default".
        destination_service_level (str):
            Optional. Destination service level (Standard/Premium/Ultra).
            Defaults to "Premium".
        destination_zones (list):
            Optional. Availability zones for destination volume. If None, defaults to ["1"].
        
        # Source volume parameters (optional - will use config defaults)
        resource_group_name (str):
            Optional. Source volume resource group name. Will use config default if not provided.
        account_name (str):
            Optional. Source volume NetApp account name. Will use config default if not provided.
        pool_name (str):
            Optional. Source volume capacity pool name. Will use config default if not provided.
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and replication setup details

    Raises:
        InvalidConfigError: If required source volume parameters are missing from both function call and config
        ValueError: If required destination parameters are missing or invalid
        ResourceNotFoundError: If source volume does not exist
        Exception: If there is an error during the replication setup process   
    
    Note:
        - Source and destination volumes must be in different Azure regions
        - Destination volume will be created as a data protection volume
    """
    try:
        result = create_replication(
            volume_name=volume_name,
            destination_resource_group_name=destination_resource_group_name,
            destination_account_name=destination_account_name,
            destination_pool_name=destination_pool_name,
            destination_volume_name=destination_volume_name,
            destination_location=destination_location,
            destination_creation_token=destination_creation_token,
            destination_usage_threshold=destination_usage_threshold,
            destination_protocol_types=destination_protocol_types,
            destination_virtual_network_name=destination_virtual_network_name,
            destination_subnet_name=destination_subnet_name,
            destination_service_level=destination_service_level,
            destination_zones=destination_zones,
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            print_output=print_output
        )
        if result['status'] == 'error':
            error_message = f"Error creating ANF replication: {result.get('details', 'Unknown error')}"
            logger.error(error_message)
            if print_output:
                print(error_message)
        return result
    except Exception as e:
        error_message = f"Error creating ANF replication: {e}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": f"Error creating ANF replication: {e}"}

@mcp.tool(name="Create_ANF_Config")
async def create_anf_config_tool(
    resource_group_name: str,
    account_name: str,
    pool_name: str,
    location: str,
    virtual_network_name: str,
    subnet_name: str = "default",
    protocol_types: Optional[List[str]] = None,
    print_output: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Use this tool to create an ANF configuration file to avoid repetitive parameters.
    
    Args:
        resource_group_name (str):
            Required. The name of the resource group.
        account_name (str):
            Required. The name of the NetApp account.
        pool_name (str):
            Required. The name of the capacity pool.
        location (str):
            Required. Azure region (e.g., "centralus").
        virtual_network_name (str):
            Required. The name of the virtual network.
        subnet_name (str):
            Optional. The name of the subnet. Defaults to "default".
        protocol_types (List[str]):
            Optional. List of protocol types (NFSv3, NFSv4.1, CIFS). Defaults to ["NFSv3"].
        print_output (bool):
            Optional. If set to True, prints log messages to the console.
            Defaults to False.

    Returns:
        Dictionary with status and config creation details

    Raises:
        Exception: For errors during config creation
    """
    try:
        # Set default protocol types if not provided
        if protocol_types is None:
            protocol_types = ["NFSv3"]
            
        result = create_anf_config(
            resource_group_name=resource_group_name,
            account_name=account_name,
            pool_name=pool_name,
            location=location,
            virtual_network_name=virtual_network_name,
            subnet_name=subnet_name,
            protocol_types=protocol_types,
            print_output=print_output
        )
        if result.get('status') == 'error':
            error_message = f"Error creating ANF config: {result.get('details', 'Unknown error')}"
            logger.error(error_message)
            if print_output:
                print(error_message)
        return result
    except Exception as e:
        error_message = f"Error creating ANF config: {e}"
        logger.error(error_message)
        if print_output:
            print(error_message)
        return {"status": "error", "details": f"Error creating ANF config: {e}"}

# Register the MCP instance to run the tools
def main():
    """Main entry point for the ANF MCP server."""
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()
# The module can be imported for testing and development purposes without executing the main logic
