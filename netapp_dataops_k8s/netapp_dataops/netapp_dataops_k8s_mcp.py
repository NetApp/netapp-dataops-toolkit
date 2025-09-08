#!/usr/bin/env python3

# Entry point to setup and run the MCP server

import logging
import sys
from typing import Optional
from fastmcp import FastMCP

from netapp_dataops.k8s import (
    create_jupyter_lab,
    clone_jupyter_lab,
    list_jupyter_labs,
    create_jupyter_lab_snapshot,
    list_jupyter_lab_snapshots,
    create_volume,
    clone_volume,
    list_volumes,
    create_volume_snapshot,
    list_volume_snapshots,
    create_flexcache
)

# Creates the FastMCP server instance
mcp = FastMCP("NetApp DataOps K8s MCP Server")

# --- Workspace management tools ---

@mcp.tool(name='CreateJupyterLab')
def create_jupyter_lab_tool(
    workspace_name: str, 
    workspace_size: str, 
    mount_pvc: Optional[str] = None, 
    storage_class: Optional[str] = None,
    load_balancer_service: bool = False, 
    namespace: str = "default",
    workspace_password: Optional[str] = None, 
    workspace_image: str = "nvcr.io/nvidia/tensorflow:22.05-tf2-py3",
    request_cpu: Optional[str] = None, 
    request_memory: Optional[str] = None, 
    request_nvidia_gpu: Optional[str] = None, 
    allocate_resource: Optional[str] = None, 
    print_output: bool = False, 
    pvc_already_exists: bool = False
) -> str:
    """
    Create a new JupyterLab workspace.

    This function sets up and deploys a JupyterLab workspace in a Kubernetes cluster.
    It handles the creation of necessary resources such as Persistent Volume Claims (PVCs),
    services, and deployments.

    Parameters:
    - workspace_name (str): Name of the new workspace.
    - workspace_size (str): Size of the workspace.
    - mount_pvc (str, optional): Persistent Volume Claim to mount. Format: "pvc_name:mount_path".
    - storage_class (str, optional): Storage class to use for the PVC.
    - load_balancer_service (bool, optional): Whether to use a LoadBalancer service. Default is False.
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - workspace_password (str, optional): Password for the workspace. If not provided, a password will be generated.
    - workspace_image (str, optional): Docker image for the workspace. Default is "nvcr.io/nvidia/tensorflow:22.05-tf2-py3".
    - request_cpu (str, optional): CPU request for the workspace.
    - request_memory (str, optional): Memory request for the workspace.
    - request_nvidia_gpu (str, optional): NVIDIA GPU request for the workspace.
    - allocate_resource (str, optional): Additional resource allocation in the format "resource=limit".
    - print_output (bool, optional): Whether to print output messages. Default is False.
    - pvc_already_exists (bool, optional): Whether the PVC already exists. Default is False.

    Returns:
    - str: URL of the newly created JupyterLab workspace.

    Raises:
    - InvalidConfigError: If the Kubernetes configuration is invalid.
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    - ServiceUnavailableError: If the service is unavailable.
    """
    try:
        url = create_jupyter_lab(
            workspace_name, 
            workspace_size, 
            mount_pvc,
            storage_class,
            load_balancer_service, 
            namespace,
            workspace_password, 
            workspace_image,
            request_cpu, 
            request_memory, 
            request_nvidia_gpu, 
            allocate_resource, 
            print_output, 
            pvc_already_exists
        )
        return url
    except Exception as e:
        print(f"Error creating JupyterLab: {e}")
        raise

@mcp.tool(name="CloneJupyterLab")
def clone_jupyter_lab_tool(
    new_workspace_name: str,
    source_workspace_name: str,
    source_snapshot_name: Optional[str] = None,
    load_balancer_service: bool = False, 
    new_workspace_password: Optional[str] = None, 
    volume_snapshot_class: str = "csi-snapclass",
    namespace: str = "default", 
    request_cpu: Optional[str] = None, 
    request_memory: Optional[str] = None,
    request_nvidia_gpu: Optional[str] = None, 
    allocate_resource: Optional[str] = None, 
    print_output: bool = False
) -> str:
    """
    Clone an existing JupyterLab workspace.

    This function creates a new JupyterLab workspace by cloning an existing workspace or its snapshot.
    It handles the creation of necessary resources such as Persistent Volume Claims (PVCs) and deployments.

    Parameters:
    - new_workspace_name (str): Name of the new workspace.
    - source_workspace_name (str): Name of the source workspace to clone.
    - source_snapshot_name (str, optional): Name of the source snapshot. If not provided, the source workspace will be used.
    - load_balancer_service (bool, optional): Whether to use a LoadBalancer service. Default is False.
    - new_workspace_password (str, optional): Password for the new workspace. If not provided, a password will be generated.
    - volume_snapshot_class (str, optional): Volume snapshot class to use. Default is "csi-snapclass".
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - request_cpu (str, optional): CPU request for the new workspace.
    - request_memory (str, optional): Memory request for the new workspace.
    - request_nvidia_gpu (str, optional): NVIDIA GPU request for the new workspace.
    - allocate_resource (str, optional): Additional resource allocation in the format "resource=limit".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - str: URL of the newly created JupyterLab workspace.

    Raises:
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        url = clone_jupyter_lab(
            new_workspace_name,
            source_workspace_name,
            source_snapshot_name,
            load_balancer_service,
            new_workspace_password,
            volume_snapshot_class,
            namespace,
            request_cpu,
            request_memory,
            request_nvidia_gpu,
            allocate_resource,
            print_output
        )
        return url
    except Exception as e:
        print(f"Error cloning JupyterLab: {e}")
        raise

@mcp.tool(name="ListJupyterLabs")
def list_jupyter_labs_tool(
    namespace: str = "default", 
    print_output: bool = False
) -> list:
    """
    List all JupyterLab workspaces.

    This function retrieves and lists all JupyterLab workspaces in a specified Kubernetes namespace.
    It provides details such as workspace name, status, size, storage class, access URL, and clone details.

    Parameters:
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - list: A list of dictionaries, each containing details of a JupyterLab workspace.

    Raises:
    - InvalidConfigError: If the Kubernetes configuration is invalid.
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        workspaces_list = list_jupyter_labs(
            namespace,
            print_output
        )
        return workspaces_list
    except Exception as e:
        print(f"Error listing JupyterLabs: {e}")
        raise

@mcp.tool(name="CreateJupyterLabSnapshot")
def create_jupyter_lab_snapshot_tool(
    workspace_name: str, 
    snapshot_name: Optional[str] = None, 
    volume_snapshot_class: str = "csi-snapclass", 
    namespace: str = "default", 
    print_output: bool = False
) -> str:
    """
    Create a snapshot of a JupyterLab workspace.

    This function creates a VolumeSnapshot for a specified JupyterLab workspace in a Kubernetes namespace.

    Parameters:
    - workspace_name (str): Name of the JupyterLab workspace.
    - snapshot_name (str, optional): Name of the snapshot. If not provided, a name will be generated.
    - volume_snapshot_class (str, optional): Volume snapshot class to use. Default is "csi-snapclass".
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - str: Name of the created snapshot.

    Raises:
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        snapshot_name = create_jupyter_lab_snapshot(
            workspace_name,
            snapshot_name,
            volume_snapshot_class,
            namespace,
            print_output
        )
        return snapshot_name
    except Exception as e:
        print(f"Error creating JupyterLab snapshot: {e}")
        raise

@mcp.tool(name="ListJupyterLabSnapshots")
def list_jupyter_lab_snapshots_tool(
    workspace_name: Optional[str] = None, 
    namespace: str = "default", 
    print_output: bool = False
) -> list:
    """
    List all snapshots of JupyterLab workspaces.

    This function retrieves and lists all VolumeSnapshots for JupyterLab workspaces in a specified Kubernetes namespace.
    If a workspace name is provided, it lists snapshots for that specific workspace.

    Parameters:
    - workspace_name (str, optional): Name of the JupyterLab workspace. If not provided, lists snapshots for all workspaces.
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - list: A list of dictionaries, each containing details of a VolumeSnapshot.

    Raises:
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        snapshots_list = list_jupyter_lab_snapshots(
            workspace_name,
            namespace,
            print_output
        )
        return snapshots_list
    except Exception as e:
        print(f"Error listing JupyterLab snapshots: {e}")
        raise

# --- Volume management tools ---

@mcp.tool(name="CreateVolume")
def create_volume_tool(
    pvc_name: str, 
    volume_size: str, 
    storage_class: Optional[str] = None, 
    namespace: str = "default",
    print_output: bool = False
) -> None:
    """
    Create a new volume.

    This function creates a new Persistent Volume Claim (PVC) in a specified Kubernetes namespace.
    It can optionally use a source snapshot or source PVC for cloning.

    Parameters:
    - pvc_name (str): Name of the new PVC to be created.
    - volume_size (str): Size of the volume.
    - storage_class (str, optional): Storage class to use for the PVC. Default is None.
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - None

    Raises:
    - InvalidConfigError: If the Kubernetes configuration is invalid.
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        create_volume(
            pvc_name,
            volume_size,
            storage_class,
            namespace,
            print_output
        )
    except Exception as e:
        print(f"Error creating volume: {e}")
        raise

@mcp.tool(name="CloneVolume")
def clone_volume_tool(
    new_pvc_name: str, 
    source_pvc_name: str, 
    source_snapshot_name: Optional[str] = None,
    volume_snapshot_class: str = "csi-snapclass", 
    namespace: str = "default", 
    print_output: bool = False
):
    """
    Clone an existing volume.

    This function creates a new Persistent Volume Claim (PVC) by cloning an existing PVC.
    If a source snapshot is not provided, a new snapshot is created from the source PVC.

    Parameters:
    - new_pvc_name (str): Name of the new PVC to be created.
    - source_pvc_name (str): Name of the source PVC to clone.
    - source_snapshot_name (str, optional): Name of the source snapshot. If not provided, a new snapshot will be created.
    - volume_snapshot_class (str, optional): Volume snapshot class to use. Default is "csi-snapclass".
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - None

    Raises:
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        clone_volume(
            new_pvc_name,
            source_pvc_name,
            source_snapshot_name,
            volume_snapshot_class,
            namespace,
            print_output
        )
    except Exception as e:
        print(f"Error cloning volume: {e}")
        raise

@mcp.tool(name="ListVolumes")
def list_volumes_tool(
    namespace: str = "default", 
    print_output: bool = False
) -> list:
    """
    List all volumes.

    This function retrieves and lists all Persistent Volume Claims (PVCs) in a specified Kubernetes namespace.
    It provides details such as PVC name, status, size, storage class, and clone details.

    Parameters:
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - list: A list of dictionaries, each containing details of a PVC.

    Raises:
    - InvalidConfigError: If the Kubernetes configuration is invalid.
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        volumes_list = list_volumes(
            namespace,
            print_output
        )
        return volumes_list
    except Exception as e:
        print(f"Error listing volumes: {e}")
        raise

@mcp.tool(name="CreateVolumeSnapshot")
def create_volume_snapshot_tool(
    pvc_name: str, 
    snapshot_name: Optional[str] = None, 
    volume_snapshot_class: str = "csi-snapclass",
    namespace: str = "default", 
    print_output: bool = False
) -> str:
    """
    Create a snapshot of a volume.

    This function creates a VolumeSnapshot for a specified Persistent Volume Claim (PVC) in a Kubernetes namespace.

    Parameters:
    - pvc_name (str): Name of the PVC to snapshot.
    - snapshot_name (str, optional): Name of the snapshot. If not provided, a name will be generated.
    - volume_snapshot_class (str, optional): Volume snapshot class to use. Default is "csi-snapclass".
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - str: Name of the created snapshot.

    Raises:
    - InvalidConfigError: If the Kubernetes configuration is invalid.
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        snapshot_name = create_volume_snapshot(
            pvc_name,
            snapshot_name,
            volume_snapshot_class,
            namespace,
            print_output
        )
        return snapshot_name
    except Exception as e:
        print(f"Error creating volume snapshot: {e}")
        raise

@mcp.tool(name="ListVolumeSnapshots")
def list_volume_snapshots_tool(
    pvc_name: Optional[str] = None, 
    namespace: str = "default", 
    print_output: bool = False
) -> list:
    """
    List all snapshots of volumes.

    This function retrieves and lists all VolumeSnapshots in a specified Kubernetes namespace.
    If a PVC name is provided, it lists snapshots for that specific PVC. It can also filter snapshots
    to include only those associated with JupyterLab workspaces.

    Parameters:
    - pvc_name (str, optional): Name of the PVC. If not provided, lists snapshots for all PVCs.
    - namespace (str, optional): Kubernetes namespace. Default is "default".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - list: A list of dictionaries, each containing details of a VolumeSnapshot.

    Raises:
    - InvalidConfigError: If the Kubernetes configuration is invalid.
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    """
    try:
        snapshots_list = list_volume_snapshots(
            pvc_name,
            namespace,
            print_output
        )
        return snapshots_list
    except Exception as e:
        print(f"Error listing volume snapshots: {e}")
        raise

@mcp.tool(name="CreateFlexCache")
def create_flexcache_tool(
    source_vol: str,
    source_svm: str,
    flexcache_vol: str,
    flexcache_size: str,
    backend_name: str,
    junction: Optional[str] = None,
    namespace: str = "default",
    trident_namespace: str = "trident",
    print_output: bool = False
) -> str:
    """
    Create a FlexCache volume in ONTAP and a corresponding PersistentVolume (PV) and PersistentVolumeClaim (PVC) in Kubernetes.

    This function creates a FlexCache volume in ONTAP and then creates a PV and PVC representing the FlexCache in a specified Kubernetes namespace.

    Parameters:
    - source_vol (str): The name of the source volume in the source SVM that will be cached by the FlexCache volume.
    - source_svm (str): The name of the source Storage Virtual Machine (SVM) that contains the origin volume to be cached.
    - flexcache_vol (str): The name of the FlexCache volume to be created.
    - flexcache_size (str): The size of the FlexCache volume to be created. The size must be specified in a format such as '1024Mi', '100Gi', '10Ti', etc. Note: The size must be at least 50Gi.
    - backend_name (str): The name of the tridentbackendconfig.
    - junction (str, optional): The junction path for the FlexCache volume. Default is None.
    - namespace (str, optional): Kubernetes namespace to create the new PersistentVolumeClaim (PVC) in. Default is "default".
    - trident_namespace (str, optional): Kubernetes namespace where Trident is installed. Default is "trident".
    - print_output (bool, optional): Whether to print output messages. Default is False.

    Returns:
    - dict: A dictionary containing the FlexCache volume and PVC information.

    Raises:
    - InvalidConfigError: If the Kubernetes configuration is invalid.
    - APIConnectionError: If there is an error connecting to the Kubernetes API.
    - InvalidVolumeParameterError: If the volume parameters are invalid.
    - NetAppRestError: If there is an error with the NetApp REST API.
    - ConnectionTypeError: If the connection type is invalid.
    """
    try:
        result = create_flexcache(
            source_vol=source_vol,
            source_svm=source_svm,
            flexcache_vol=flexcache_vol,
            flexcache_size=flexcache_size,
            backend_name=backend_name,
            junction=junction,
            namespace=namespace,
            trident_namespace=trident_namespace,
            print_output=print_output
        )

        return {
            "ontap_flexcache": result['ontap_flexcache'],
            "k8s_pvc": result['k8s_pvc']
        }
    except Exception as e:
        print(f"Error creating FlexCache volume: {e}")
        raise

def main():
    try:
        # Sets up basic logging to capture server events and errors
        logging.basicConfig(level=logging.INFO)

        # Starts the MCP server using stdio transport for local operation
        mcp.run(transport="stdio")

    except Exception as e:
        # Logs and prints any startup errors, then exits with an error code
        logging.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
