"""NetApp DataOps Toolkit for Kubernetes Environments import module.

This module provides the public functions available to be imported directly
by applications using the import method of utilizing the toolkit.
"""

__version__ = "2.0.0"

from datetime import datetime
import functools
from getpass import getpass
from time import sleep
import warnings

import IPython
from kubernetes import client, config
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.rest import ApiException
from tabulate import tabulate
import pandas as pd


# Using this decorator in lieu of using a dependency to manage deprecation
def deprecated(func):
    @functools.wraps(func)
    def warned_func(*args, **kwargs):
        warnings.warn("Function {} is deprecated.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        return func(*args, **kwargs)
    return warned_func


#
# Class definitions
#


class APIConnectionError(Exception):
    '''Error that will be raised when an API connection cannot be established'''
    pass


class InvalidConfigError(Exception):
    '''Error that will be raised when the config file is invalid or missing'''
    pass


class ServiceUnavailableError(Exception):
    '''Error that will be raised when a service is not available'''
    pass


#
# Private functions
#


def _get_jupyter_lab_prefix() -> str:
    return "ntap-dsutil-jupyterlab-"


def _get_jupyter_lab_deployment(workspaceName: str) -> str:
    return _get_jupyter_lab_prefix() + workspaceName


def _get_jupyter_lab_labels(workspaceName: str) -> dict:
    labels = {
        "app": _get_jupyter_lab_prefix() + workspaceName,
        "created-by": "ntap-dsutil",
        "entity-type": "jupyterlab-workspace",
        "created-by-operation": "create-jupyterlab",
        "jupyterlab-workspace-name": workspaceName
    }
    return labels


def _get_jupyter_lab_label_selector() -> str:
    labels = _get_jupyter_lab_labels(workspaceName="temp")
    return "created-by=" + labels["created-by"] + ",entity-type=" + labels["entity-type"]


def _get_jupyter_lab_service(workspaceName: str) -> str:
    return _get_jupyter_lab_prefix() + workspaceName


def _get_jupyter_lab_workspace_pvc_name(workspaceName: str) -> str:
    return _get_jupyter_lab_prefix() + workspaceName


def _load_kube_config():
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()


def _print_invalid_config_error():
    print(
        "Error: Missing or invalid kubeconfig file. The NetApp DataOps Toolkit for Kubernetes requires that a valid kubeconfig file be present on the host, located at $HOME/.kube or at another path specified by the KUBECONFIG environment variable.")


def _retrieve_image_for_jupyter_lab_deployment(workspaceName: str, namespace: str = "default",
                                         printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve image
    try:
        api = client.AppsV1Api()
        deployment = api.read_namespaced_deployment(namespace=namespace,
                                                    name=_get_jupyter_lab_deployment(workspaceName=workspaceName))
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    return deployment.spec.template.spec.containers[0].image


def _retrieve_jupyter_lab_url(workspaceName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    try:
        api = client.CoreV1Api()
        serviceStatus = api.read_namespaced_service(namespace=namespace,
                                                    name=_get_jupyter_lab_service(workspaceName=workspaceName))

        # Check if service type is LoadBalancer
        if serviceStatus.spec.type == "LoadBalancer":
            # Construct and return url
            try :
                loadBalancerIP = serviceStatus.status.load_balancer.ingress[0].ip
            except :
                if printOutput :
                    print("Error: Kubernetes Service for workspace is not available.")
                raise ServiceUnavailableError()
            return "http://" + loadBalancerIP
        else:
            # Retrieve access port
            port = serviceStatus.spec.ports[0].node_port

            # Retrieve node IP (random node)
            try:
                api = client.CoreV1Api()
                nodes = api.list_node()
                ip = nodes.items[0].status.addresses[0].address
            except:
                ip = "<IP address of Kubernetes node>"
                pass
            # Construct and return url
            return "http://" + ip + ":" + str(port)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)


def _retrieve_jupyter_lab_workspace_for_pvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve workspace name
    try:
        api = client.CoreV1Api()
        pvc = api.read_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
        workspaceName = pvc.metadata.labels["jupyterlab-workspace-name"]
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    return workspaceName


def _retrieve_size_for_pvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve size
    try:
        api = client.CoreV1Api()
        pvc = api.read_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    pvcSize = pvc.status.capacity["storage"]

    return pvcSize


def _retrieve_source_volume_details_for_volume_snapshot(snapshotName: str, namespace: str = "default",
                                                 printOutput: bool = False) -> (str, str):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve source PVC and restoreSize
    try:
        api = client.CustomObjectsApi()
        volumeSnapshot = api.get_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(),
                                                          namespace=namespace, name=snapshotName,
                                                          plural="volumesnapshots")
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    sourcePvcName = volumeSnapshot["spec"]["source"]["persistentVolumeClaimName"]
    restoreSize = volumeSnapshot["status"]["restoreSize"]

    return sourcePvcName, restoreSize


def _retrieve_storage_class_for_pvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve StorageClass
    try:
        api = client.CoreV1Api()
        pvc = api.read_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    storageClass = pvc.spec.storage_class_name

    return storageClass


def _scale_jupyter_lab_deployment(workspaceName: str, numPods: int, namespace: str = "default", printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Scale deployment
    deploymentName = _get_jupyter_lab_deployment(workspaceName=workspaceName)
    deployment = {
        "metadata": {
            "name": deploymentName
        },
        "spec": {
            "replicas": numPods
        }
    }
    if printOutput:
        print("Scaling Deployment '" + _get_jupyter_lab_deployment(
            workspaceName=workspaceName) + "' in namespace '" + namespace + "' to " + str(numPods) + " pod(s).")
    try:
        api = client.AppsV1Api()
        api.patch_namespaced_deployment(name=deploymentName, namespace=namespace, body=deployment)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)


def _get_snapshot_api_group() -> str:
    return "snapshot.storage.k8s.io"


def _get_snapshot_api_version() -> str:
    return "v1beta1"


def _wait_for_jupyter_lab_deployment_ready(workspaceName: str, namespace: str = "default", printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if printOutput:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Wait for deployment to be ready
    if printOutput:
        print(
            "Waiting for Deployment '" + _get_jupyter_lab_deployment(workspaceName=workspaceName) + "' to reach Ready state.")
    while True:
        try:
            api = client.AppsV1Api()
            deploymentStatus = api.read_namespaced_deployment_status(namespace=namespace, name=_get_jupyter_lab_deployment(
                workspaceName=workspaceName))
        except ApiException as err:
            if printOutput:
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        if deploymentStatus.status.ready_replicas == 1:
            break
        sleep(5)


#
# Public functions used for imports
#


def clone_jupyter_lab(new_workspace_name: str, source_workspace_name: str, source_snapshot_name: str = None,
                      new_workspace_password: str = None, volume_snapshot_class: str = "csi-snapclass",
                      namespace: str = "default", request_cpu: str = None, request_memory: str = None,
                      request_nvidia_gpu: str = None, print_output: bool = False):
    # Determine source PVC details
    if source_snapshot_name:
        sourcePvcName, workspaceSize = _retrieve_source_volume_details_for_volume_snapshot(snapshotName=source_snapshot_name,
                                                                                    namespace=namespace,
                                                                                    printOutput=print_output)
        if print_output:
            print(
                "Creating new JupyterLab workspace '" + new_workspace_name + "' from VolumeSnapshot '" + source_snapshot_name + "' in namespace '" + namespace + "'...\n")
    else:
        sourcePvcName = _get_jupyter_lab_workspace_pvc_name(workspaceName=source_workspace_name)
        workspaceSize = _retrieve_size_for_pvc(pvcName=sourcePvcName, namespace=namespace, printOutput=print_output)
        if print_output:
            print(
                "Creating new JupyterLab workspace '" + new_workspace_name + "' from source workspace '" + source_workspace_name + "' in namespace '" + namespace + "'...\n")

    # Determine source workspace details
    if not source_workspace_name:
        source_workspace_name = _retrieve_jupyter_lab_workspace_for_pvc(pvcName=sourcePvcName, namespace=namespace,
                                                                printOutput=print_output)
    sourceWorkspaceImage = _retrieve_image_for_jupyter_lab_deployment(workspaceName=source_workspace_name, namespace=namespace,
                                                                printOutput=print_output)

    # Set labels
    labels = _get_jupyter_lab_labels(workspaceName=new_workspace_name)
    labels["created-by-operation"] = "clone-jupyterlab"
    labels["source-jupyterlab-workspace"] = source_workspace_name
    labels["source-pvc"] = sourcePvcName

    # Clone workspace PVC
    clone_volume(new_pvc_name=_get_jupyter_lab_workspace_pvc_name(workspaceName=new_workspace_name), source_pvc_name=sourcePvcName,
                 source_snapshot_name=source_snapshot_name, volume_snapshot_class=volume_snapshot_class, namespace=namespace,
                 print_output=print_output, pvc_labels=labels)

    # Remove source PVC from labels
    del labels["source-pvc"]

    # Create new workspace
    print()
    create_jupyter_lab(workspace_name=new_workspace_name, workspace_size=workspaceSize, namespace=namespace,
                       workspace_password=new_workspace_password, workspace_image=sourceWorkspaceImage, request_cpu=request_cpu,
                       request_memory=request_memory, request_nvidia_gpu=request_nvidia_gpu, print_output=print_output,
                       pvc_already_exists=True, labels=labels)

    if print_output:
        print("JupyterLab workspace successfully cloned.")


def clone_volume(new_pvc_name: str, source_pvc_name: str, source_snapshot_name: str = None,
                 volume_snapshot_class: str = "csi-snapclass", namespace: str = "default", print_output: bool = False,
                 pvc_labels: dict = None):
    # Handle volume source
    if not source_snapshot_name:
        # Create new VolumeSnapshot to use as source for clone
        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        source_snapshot_name = "ntap-dsutil.for-clone." + timestamp
        if print_output:
            print(
                "Creating new VolumeSnapshot '" + source_snapshot_name + "' for source PVC '" + source_pvc_name + "' in namespace '" + namespace + "' to use as source for clone...")
        create_volume_snapshot(pvc_name=source_pvc_name, snapshot_name=source_snapshot_name,
                               volume_snapshot_class=volume_snapshot_class, namespace=namespace, print_output=print_output)

    # Retrieve source volume details
    source_pvc_name, restoreSize = _retrieve_source_volume_details_for_volume_snapshot(snapshotName=source_snapshot_name,
                                                                              namespace=namespace,
                                                                              printOutput=print_output)
    storageClass = _retrieve_storage_class_for_pvc(pvcName=source_pvc_name, namespace=namespace, printOutput=print_output)

    # Set PVC labels
    if not pvc_labels:
        pvc_labels = {"created-by": "ntap-dsutil", "created-by-operation": "clone-volume", "source-pvc": source_pvc_name}

    # Create new PVC from snapshot
    if print_output:
        print(
            "Creating new PersistentVolumeClaim (PVC) '" + new_pvc_name + "' from VolumeSnapshot '" + source_snapshot_name + "' in namespace '" + namespace + "'...")
    create_volume(pvc_name=new_pvc_name, volume_size=restoreSize, storage_class=storageClass, namespace=namespace,
                  print_output=print_output, pvc_labels=pvc_labels, source_snapshot=source_snapshot_name)

    if print_output:
        print("Volume successfully cloned.")


def create_jupyter_lab(workspace_name: str, workspace_size: str, storage_class: str = None, load_balancer_service: bool = False, namespace: str = "default",
                       workspace_password: str = None, workspace_image: str = "jupyter/tensorflow-notebook",
                       request_cpu: str = None, request_memory: str = None, request_nvidia_gpu: str = None,
                       print_output: bool = False, pvc_already_exists: bool = False, labels: dict = None) -> str:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Set labels
    if not labels:
        labels = _get_jupyter_lab_labels(workspaceName=workspace_name)

    # Step 0 - Set password
    if not workspace_password:
        while True:
            workspace_password = getpass(
                "Set workspace password (this password will be required in order to access the workspace): ")
            if getpass("Re-enter password: ") == workspace_password:
                break
            else:
                print("Error: Passwords do not match. Try again.")
    hashedPassword = IPython.lib.passwd(workspace_password)

    # Step 1 - Create PVC for workspace
    if not pvc_already_exists:
        if print_output:
            print("\nCreating persistent volume for workspace...")
        try:
            create_volume(pvc_name=_get_jupyter_lab_workspace_pvc_name(workspaceName=workspace_name), volume_size=workspace_size,
                          storage_class=storage_class, namespace=namespace, pvc_labels=labels, print_output=print_output)
        except:
            if print_output:
                print("Aborting workspace creation...")
            raise

    # Step 2 - Create service for workspace

    # Construct service
    if load_balancer_service:
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=_get_jupyter_lab_service(workspaceName=workspace_name),
                labels=labels
            ),
            spec=client.V1ServiceSpec(
                type="LoadBalancer",
                selector={
                    "app": labels["app"]
                },
                ports=[
                    client.V1ServicePort(
                        name="http",
                        port=80,
                        target_port=8888,
                        protocol="TCP"
                    )
                ]
            )
        )
    else:
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=_get_jupyter_lab_service(workspaceName=workspace_name),
                labels=labels
            ),
            spec=client.V1ServiceSpec(
                type="NodePort",
                selector={
                    "app": labels["app"]
                },
                ports=[
                    client.V1ServicePort(
                        name="http",
                        port=8888,
                        target_port=8888,
                        protocol="TCP"
                    )
                ]
            )
        )


    # Create service
    if print_output:
        print("\nCreating Service '" + _get_jupyter_lab_service(
            workspaceName=workspace_name) + "' in namespace '" + namespace + "'.")
    try:
        api = client.CoreV1Api()
        api.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
            print("Aborting workspace creation...")
        raise APIConnectionError(err)

    if print_output:
        print("Service successfully created.")

    # Step 3 - Create deployment

    # Construct deployment
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=_get_jupyter_lab_deployment(workspaceName=workspace_name),
            labels=labels
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector={
                "matchLabels": {
                    "app": labels["app"]
                }
            },
            template=client.V1PodTemplateSpec(
                metadata=V1ObjectMeta(
                    labels=labels
                ),
                spec=client.V1PodSpec(
                    volumes=[
                        client.V1Volume(
                            name="workspace",
                            persistent_volume_claim={
                                "claimName": _get_jupyter_lab_workspace_pvc_name(workspaceName=workspace_name)
                            }
                        )
                    ],
                    containers=[
                        client.V1Container(
                            name="jupyterlab",
                            image=workspace_image,
                            env=[
                                client.V1EnvVar(
                                    name="JUPYTER_ENABLE_LAB",
                                    value="yes"
                                ),
                                client.V1EnvVar(
                                    name="RESTARTABLE",
                                    value="yes"
                                ),
                                client.V1EnvVar(
                                    name="CHOWN_HOME",
                                    value="yes"
                                )
                            ],
                            args=["start-notebook.sh", "--ServerApp.password=" + hashedPassword, "--ServerApp.ip='0.0.0.0'",
                                  "--no-browser"],
                            ports=[
                                client.V1ContainerPort(container_port=8888)
                            ],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="workspace",
                                    mount_path="/home/jovyan"
                                )
                            ],
                            resources={
                                "limits": dict(),
                                "requests": dict()
                            }
                        )
                    ]
                )
            )
        )
    )

    # Apply resource requests
    if request_cpu:
        deployment.spec.template.spec.containers[0].resources["requests"]["cpu"] = request_cpu
    if request_memory:
        deployment.spec.template.spec.containers[0].resources["requests"]["memory"] = request_memory
    if request_nvidia_gpu:
        deployment.spec.template.spec.containers[0].resources["requests"]["nvidia.com/gpu"] = request_nvidia_gpu
        deployment.spec.template.spec.containers[0].resources["limits"]["nvidia.com/gpu"] = request_nvidia_gpu

    # Create deployment
    if print_output:
        print("\nCreating Deployment '" + _get_jupyter_lab_deployment(
            workspaceName=workspace_name) + "' in namespace '" + namespace + "'.")
    try:
        api = client.AppsV1Api()
        api.create_namespaced_deployment(namespace=namespace, body=deployment)
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
            print("Aborting workspace creation...")
        raise APIConnectionError(err)

    # Wait for deployment to be ready
    if print_output:
        print("Deployment '" + _get_jupyter_lab_deployment(workspaceName=workspace_name) + "' created.")
    _wait_for_jupyter_lab_deployment_ready(workspaceName=workspace_name, namespace=namespace, printOutput=print_output)

    if print_output:
        print("Deployment successfully created.")

    # Step 4 - Retrieve access URL
    try:
        url = _retrieve_jupyter_lab_url(workspaceName=workspace_name, namespace=namespace, printOutput=print_output)
    except (APIConnectionError, ServiceUnavailableError) as err:
        if print_output:
            print("Aborting workspace creation...")
        raise

    if print_output:
        print("\nWorkspace successfully created.")
        print("To access workspace, navigate to " + url)

    return url


def create_jupyter_lab_snapshot(workspace_name: str, snapshot_name: str = None, volume_snapshot_class: str = "csi-snapclass",
                                namespace: str = "default", print_output: bool = False):
    # Create snapshot
    if print_output:
        print(
            "Creating VolumeSnapshot for JupyterLab workspace '" + workspace_name + "' in namespace '" + namespace + "'...")
    create_volume_snapshot(pvc_name=_get_jupyter_lab_workspace_pvc_name(workspaceName=workspace_name), snapshot_name=snapshot_name,
                           volume_snapshot_class=volume_snapshot_class, namespace=namespace, print_output=print_output)


def create_volume(pvc_name: str, volume_size: str, storage_class: str = None, namespace: str = "default",
                  print_output: bool = False,
                  pvc_labels: dict = {"created-by": "ntap-dsutil", "created-by-operation": "create-volume"},
                  source_snapshot: str = None, source_pvc: str = None):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Construct PVC
    pvc = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(
            name=pvc_name,
            labels=pvc_labels
        ),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteMany"],
            resources=client.V1ResourceRequirements(
                requests={
                    'storage': volume_size
                }
            )
        )
    )

    # Apply custom storageClass if specified
    if storage_class:
        pvc.spec.storage_class_name = storage_class

    # Apply source snapshot if specified
    if source_snapshot:
        pvc.spec.data_source = {
            'name': source_snapshot,
            'kind': 'VolumeSnapshot',
            'apiGroup': _get_snapshot_api_group()
        }
    # Apply source PVC if specified
    elif source_pvc:
        pvc.metadata.annotations = {
            'trident.netapp.io/cloneFromPVC': source_pvc
        }

    # Create PVC
    if print_output:
        print("Creating PersistentVolumeClaim (PVC) '" + pvc_name + "' in namespace '" + namespace + "'.")
    try:
        api = client.CoreV1Api()
        api.create_namespaced_persistent_volume_claim(body=pvc, namespace=namespace)
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for PVC to bind to volume
    if print_output:
        print("PersistentVolumeClaim (PVC) '" + pvc_name + "' created. Waiting for Kubernetes to bind volume to PVC.")
    while True:
        try:
            api = client.CoreV1Api()
            pvcStatus = api.read_namespaced_persistent_volume_claim_status(name=pvc_name, namespace=namespace)
        except ApiException as err:
            if print_output:
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        if pvcStatus.status.phase == "Bound":
            break
        sleep(5)

    if print_output:
        print(
            "Volume successfully created and bound to PersistentVolumeClaim (PVC) '" + pvc_name + "' in namespace '" + namespace + "'.")


def create_volume_snapshot(pvc_name: str, snapshot_name: str = None, volume_snapshot_class: str = "csi-snapclass",
                           namespace: str = "default", print_output: bool = False):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Set snapshot name if not passed into function
    if not snapshot_name:
        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        snapshot_name = "ntap-dsutil." + timestamp

    # Construct dict representing snapshot
    snapshot = {
        "apiVersion": _get_snapshot_api_group() + "/" + _get_snapshot_api_version(),
        "kind": "VolumeSnapshot",
        "metadata": {
            "name": snapshot_name
        },
        "spec": {
            "volumeSnapshotClassName": volume_snapshot_class,
            "source": {
                "persistentVolumeClaimName": pvc_name
            }
        }
    }

    # Create snapshot
    if print_output:
        print(
            "Creating VolumeSnapshot '" + snapshot_name + "' for PersistentVolumeClaim (PVC) '" + pvc_name + "' in namespace '" + namespace + "'.")
    try:
        api = client.CustomObjectsApi()
        api.create_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(), namespace=namespace,
                                            body=snapshot, plural="volumesnapshots")
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for snapshot creation to complete
    if print_output:
        print(
            "VolumeSnapshot '" + snapshot_name + "' created. Waiting for Trident to create snapshot on backing storage.")
    while True:
        try:
            api = client.CustomObjectsApi()
            snapshotStatus = api.get_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(),
                                                              namespace=namespace, name=snapshot_name,
                                                              plural="volumesnapshots")
        except ApiException as err:
            if print_output:
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        try:
            if snapshotStatus["status"]["readyToUse"] == True:
                break
        except:
            pass
        sleep(5)

    if print_output:
        print("Snapshot successfully created.")


def delete_jupyter_lab(workspace_name: str, namespace: str = "default", preserve_snapshots: bool = False,
                       print_output: bool = False):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Delete workspace
    if print_output:
        print("Deleting workspace '" + workspace_name + "' in namespace '" + namespace + "'.")
    try:
        # Delete deployment
        if print_output:
            print("Deleting Deployment...")
        api = client.AppsV1Api()
        api.delete_namespaced_deployment(namespace=namespace, name=_get_jupyter_lab_deployment(workspaceName=workspace_name))

        # Delete service
        if print_output:
            print("Deleting Service...")
        api = client.CoreV1Api()
        api.delete_namespaced_service(namespace=namespace, name=_get_jupyter_lab_service(workspaceName=workspace_name))

    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Delete PVC
    if print_output:
        print("Deleting PVC...")
    delete_volume(pvc_name=_get_jupyter_lab_workspace_pvc_name(workspaceName=workspace_name), namespace=namespace,
                  preserve_snapshots=preserve_snapshots, print_output=print_output)

    if print_output:
        print("Workspace successfully deleted.")


def delete_volume(pvc_name: str, namespace: str = "default", preserve_snapshots: bool = False, print_output: bool = False):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Optionally delete snapshots
    if not preserve_snapshots:
        if print_output:
            print(
                "Deleting all VolumeSnapshots associated with PersistentVolumeClaim (PVC) '" + pvc_name + "' in namespace '" + namespace + "'...")

        # Retrieve list of snapshots for PVC
        try:
            snapshotList = list_volume_snapshots(pvc_name=pvc_name, namespace=namespace, print_output=False)
        except APIConnectionError as err:
            if print_output:
                print("Error: Kubernetes API Error: ", err)
            raise

        # Delete each snapshot
        for snapshot in snapshotList:
            delete_volume_snapshot(snapshot_name=snapshot["VolumeSnapshot Name"], namespace=namespace,
                                   print_output=print_output)

    # Delete PVC
    if print_output:
        print(
            "Deleting PersistentVolumeClaim (PVC) '" + pvc_name + "' in namespace '" + namespace + "' and associated volume.")
    try:
        api = client.CoreV1Api()
        api.delete_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for PVC to disappear
    while True:
        try:
            api = client.CoreV1Api()
            api.read_namespaced_persistent_volume_claim(name=pvc_name,
                                                        namespace=namespace)  # Confirm that source PVC still exists
        except:
            break  # Break loop when source PVC no longer exists
        sleep(5)

    if print_output:
        print("PersistentVolumeClaim (PVC) successfully deleted.")


def delete_volume_snapshot(snapshot_name: str, namespace: str = "default", print_output: bool = False):
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Delete VolumeSnapshot
    if print_output:
        print("Deleting VolumeSnapshot '" + snapshot_name + "' in namespace '" + namespace + "'.")
    try:
        api = client.CustomObjectsApi()
        api.delete_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(), namespace=namespace,
                                            plural="volumesnapshots", name=snapshot_name)
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for VolumeSnapshot to disappear
    while True:
        try:
            api = client.CustomObjectsApi()
            api.get_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(),
                                             namespace=namespace, plural="volumesnapshots",
                                             name=snapshot_name)  # Confirm that VolumeSnapshot still exists
        except:
            break  # Break loop when snapshot no longer exists
        sleep(5)

    if print_output:
        print("VolumeSnapshot successfully deleted.")


def list_jupyter_labs(namespace: str = "default", print_output: bool = False) -> list:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve list of workspaces
    try:
        api = client.AppsV1Api()
        deployments = api.list_namespaced_deployment(namespace=namespace, label_selector=_get_jupyter_lab_label_selector())
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct list of workspaces
    workspacesList = list()
    for deployment in deployments.items:
        # Construct dict containing workspace details
        workspaceDict = dict()

        # Retrieve workspace name
        workspaceName = deployment.metadata.labels["jupyterlab-workspace-name"]
        workspaceDict["Workspace Name"] = workspaceName

        # Determine readiness status
        if deployment.status.ready_replicas == 1:
            workspaceDict["Status"] = "Ready"
        else:
            workspaceDict["Status"] = "Not Ready"

        # Retrieve PVC size and StorageClass
        try:
            api = client.CoreV1Api()
            pvc = api.read_namespaced_persistent_volume_claim(namespace=namespace, name=_get_jupyter_lab_workspace_pvc_name(
                workspaceName=workspaceName))
            workspaceDict["Size"] = pvc.status.capacity["storage"]
            workspaceDict["StorageClass"] = pvc.spec.storage_class_name
        except:
            workspaceDict["Size"] = ""
            workspaceDict["StorageClass"] = ""

        # Retrieve access URL
        try :
            workspaceDict["Access URL"] = _retrieve_jupyter_lab_url(workspaceName=workspaceName, namespace=namespace, printOutput=False)
        except ServiceUnavailableError :
            workspaceDict["Access URL"] = "unavailable"
        except APIConnectionError as err:
            if print_output:
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)

        # Retrieve clone details
        try:
            if deployment.metadata.labels["created-by-operation"] == "clone-jupyterlab":
                workspaceDict["Clone"] = "Yes"
                workspaceDict["Source Workspace"] = pvc.metadata.labels["source-jupyterlab-workspace"]
                try:
                    api = client.AppsV1Api()
                    deployments = api.read_namespaced_deployment(namespace=namespace, name=_get_jupyter_lab_deployment(
                        workspaceName=workspaceDict["Source Workspace"]))
                except:
                    workspaceDict["Source Workspace"] = "*deleted*"
                try:
                    workspaceDict["Source VolumeSnapshot"] = pvc.spec.data_source.name
                    try:
                        api = client.CustomObjectsApi()
                        api.get_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(),
                                                         namespace=namespace, plural="volumesnapshots",
                                                         name=workspaceDict[
                                                             "Source VolumeSnapshot"])  # Confirm that VolumeSnapshot still exists
                    except:
                        workspaceDict["Source VolumeSnapshot"] = "*deleted*"
                except:
                    workspaceDict["Source VolumeSnapshot"] = "n/a"
            else:
                workspaceDict["Clone"] = "No"
                workspaceDict["Source Workspace"] = ""
                workspaceDict["Source VolumeSnapshot"] = ""
        except:
            workspaceDict["Clone"] = "No"
            workspaceDict["Source Workspace"] = ""
            workspaceDict["Source VolumeSnapshot"] = ""

        # Append dict to list of workspaces
        workspacesList.append(workspaceDict)

    # Print list of workspaces
    if print_output:
        # Convert workspaces array to Pandas DataFrame
        workspacesDF = pd.DataFrame.from_dict(workspacesList, dtype="string")
        print(tabulate(workspacesDF, showindex=False, headers=workspacesDF.columns))

    return workspacesList


def list_jupyter_lab_snapshots(workspace_name: str = None, namespace: str = "default", print_output: bool = False):
    # Determine PVC name
    if workspace_name:
        pvcName = _get_jupyter_lab_workspace_pvc_name(workspaceName=workspace_name)
    else:
        pvcName = None

    # List snapshots
    return list_volume_snapshots(pvc_name=pvcName, namespace=namespace, print_output=print_output,
                                 jupyter_lab_workspaces_only=True)


def list_volumes(namespace: str = "default", print_output: bool = False) -> list:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve list of PVCs
    try:
        api = client.CoreV1Api()
        pvcList = api.list_namespaced_persistent_volume_claim(namespace=namespace)
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct list of volumes
    volumesList = list()
    for pvc in pvcList.items:
        # Construct dict containing volume details
        volumeDict = dict()
        volumeDict["PersistentVolumeClaim (PVC) Name"] = pvc.metadata.name
        volumeDict["Status"] = pvc.status.phase
        try:
            volumeDict["Size"] = pvc.status.capacity["storage"]
        except:
            volumeDict["Size"] = ""
        try:
            volumeDict["StorageClass"] = pvc.spec.storage_class_name
        except:
            volumeDict["StorageClass"] = ""
        try:
            if (pvc.metadata.labels["created-by-operation"] == "clone-volume") or (
                    pvc.metadata.labels["created-by-operation"] == "clone-jupyterlab"):
                volumeDict["Clone"] = "Yes"
                volumeDict["Source PVC"] = pvc.metadata.labels["source-pvc"]
                try:
                    api = client.CoreV1Api()
                    api.read_namespaced_persistent_volume_claim(name=volumeDict["Source PVC"],
                                                                namespace=namespace)  # Confirm that source PVC still exists
                except:
                    volumeDict["Source PVC"] = "*deleted*"
                try:
                    volumeDict["Source VolumeSnapshot"] = pvc.spec.data_source.name
                    try:
                        api = client.CustomObjectsApi()
                        api.get_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(),
                                                         namespace=namespace, plural="volumesnapshots", name=volumeDict[
                                "Source VolumeSnapshot"])  # Confirm that VolumeSnapshot still exists
                    except:
                        volumeDict["Source VolumeSnapshot"] = "*deleted*"
                except:
                    volumeDict["Source VolumeSnapshot"] = "n/a"
            else:
                volumeDict["Clone"] = "No"
                volumeDict["Source PVC"] = ""
                volumeDict["Source VolumeSnapshot"] = ""
        except:
            volumeDict["Clone"] = "No"
            volumeDict["Source PVC"] = ""
            volumeDict["Source VolumeSnapshot"] = ""

        # Append dict to list of volumes
        volumesList.append(volumeDict)

    # Print list of volumes
    if print_output:
        # Convert volumes array to Pandas DataFrame
        volumesDF = pd.DataFrame.from_dict(volumesList, dtype="string")
        print(tabulate(volumesDF, showindex=False, headers=volumesDF.columns))

    return volumesList


def list_volume_snapshots(pvc_name: str = None, namespace: str = "default", print_output: bool = False,
                          jupyter_lab_workspaces_only: bool = False) -> list:
    # Retrieve kubeconfig
    try:
        _load_kube_config()
    except:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    # Retrieve list of Snapshots
    try:
        api = client.CustomObjectsApi()
        volumeSnapshotList = api.list_namespaced_custom_object(group=_get_snapshot_api_group(), version=_get_snapshot_api_version(),
                                                               namespace=namespace, plural="volumesnapshots")
    except ApiException as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct list of snapshots
    snapshotsList = list()
    # return volumeSnapshotList
    for volumeSnapshot in volumeSnapshotList["items"]:
        # Construct dict containing snapshot details
        if (not pvc_name) or (volumeSnapshot["spec"]["source"]["persistentVolumeClaimName"] == pvc_name):
            snapshotDict = dict()
            snapshotDict["VolumeSnapshot Name"] = volumeSnapshot["metadata"]["name"]
            snapshotDict["Ready to Use"] = volumeSnapshot["status"]["readyToUse"]
            try:
                snapshotDict["Creation Time"] = volumeSnapshot["status"]["creationTime"]
            except:
                snapshotDict["Creation Time"] = ""
            snapshotDict["Source PersistentVolumeClaim (PVC)"] = volumeSnapshot["spec"]["source"][
                "persistentVolumeClaimName"]
            try:
                api = client.CoreV1Api()
                api.read_namespaced_persistent_volume_claim(name=snapshotDict["Source PersistentVolumeClaim (PVC)"],
                                                            namespace=namespace)  # Confirm that source PVC still exists
            except:
                snapshotDict["Source PersistentVolumeClaim (PVC)"] = "*deleted*"
            try:
                snapshotDict["Source JupyterLab workspace"] = _retrieve_jupyter_lab_workspace_for_pvc(
                    pvcName=snapshotDict["Source PersistentVolumeClaim (PVC)"], namespace=namespace, printOutput=False)
                jupyterLabWorkspace = True
            except:
                snapshotDict["Source JupyterLab workspace"] = ""
                jupyterLabWorkspace = False
            try:
                snapshotDict["VolumeSnapshotClass"] = volumeSnapshot["spec"]["volumeSnapshotClassName"]
            except:
                snapshotDict["VolumeSnapshotClass"] = ""

            # Append dict to list of snapshots
            if jupyter_lab_workspaces_only:
                if jupyterLabWorkspace:
                    snapshotsList.append(snapshotDict)
            else:
                snapshotsList.append(snapshotDict)

    # Print list of snapshots
    if print_output:
        # Convert snapshots array to Pandas DataFrame
        snapshotsDF = pd.DataFrame.from_dict(snapshotsList, dtype="string")
        print(tabulate(snapshotsDF, showindex=False, headers=snapshotsDF.columns))

    return snapshotsList


def restore_jupyter_lab_snapshot(snapshot_name: str = None, namespace: str = "default", print_output: bool = False):
    # Retrieve source PVC name
    sourcePvcName = _retrieve_source_volume_details_for_volume_snapshot(snapshotName=snapshot_name, namespace=namespace,
                                                                 printOutput=print_output)[0]

    # Retrieve workspace name
    workspaceName = _retrieve_jupyter_lab_workspace_for_pvc(pvcName=sourcePvcName, namespace=namespace,
                                                      printOutput=print_output)

    # Set labels
    labels = _get_jupyter_lab_labels(workspaceName=workspaceName)
    labels["created-by-operation"] = "restore-jupyterlab-snapshot"

    if print_output:
        print(
            "Restoring VolumeSnapshot '" + snapshot_name + "' for JupyterLab workspace '" + workspaceName + "' in namespace '" + namespace + "'...")

    # Scale deployment to 0 pods
    _scale_jupyter_lab_deployment(workspaceName=workspaceName, numPods=0, namespace=namespace, printOutput=print_output)
    sleep(5)

    # Restore snapshot
    restore_volume_snapshot(snapshot_name=snapshot_name, namespace=namespace, print_output=print_output, pvc_labels=labels)

    # Scale deployment to 1 pod
    _scale_jupyter_lab_deployment(workspaceName=workspaceName, numPods=1, namespace=namespace, printOutput=print_output)

    # Wait for deployment to reach ready state
    _wait_for_jupyter_lab_deployment_ready(workspaceName=workspaceName, namespace=namespace, printOutput=print_output)

    if print_output:
        print("JupyterLab workspace snapshot successfully restored.")


def restore_volume_snapshot(snapshot_name: str, namespace: str = "default", print_output: bool = False,
                            pvc_labels: dict = {"created-by": "ntap-dsutil",
                                             "created-by-operation": "restore-volume-snapshot"}):
    # Retrieve source PVC, restoreSize, and StorageClass
    sourcePvcName, restoreSize = _retrieve_source_volume_details_for_volume_snapshot(snapshotName=snapshot_name,
                                                                              namespace=namespace,
                                                                              printOutput=print_output)
    storageClass = _retrieve_storage_class_for_pvc(pvcName=sourcePvcName, namespace=namespace, printOutput=print_output)

    if print_output:
        print(
            "Restoring VolumeSnapshot '" + snapshot_name + "' for PersistentVolumeClaim '" + sourcePvcName + "' in namespace '" + namespace + "'.")

    # Delete source PVC
    try:
        delete_volume(pvc_name=sourcePvcName, namespace=namespace, preserve_snapshots=True, print_output=False)
    except APIConnectionError as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise

    # Create new PVC from snapshot
    try:
        create_volume(pvc_name=sourcePvcName, volume_size=restoreSize, storage_class=storageClass, namespace=namespace,
                      print_output=False, pvc_labels=pvc_labels, source_snapshot=snapshot_name)
    except APIConnectionError as err:
        if print_output:
            print("Error: Kubernetes API Error: ", err)
        raise

    if print_output:
        print("VolumeSnapshot successfully restored.")


#
# Deprecated function names
#


@deprecated
def cloneJupyterLab(newWorkspaceName: str, sourceWorkspaceName: str, sourceSnapshotName: str = None, newWorkspacePassword: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", requestCpu: str = None, requestMemory: str = None, requestNvidiaGpu: str = None, printOutput: bool = False) :
    clone_jupyter_lab(new_workspace_name=newWorkspaceName, source_workspace_name=sourceWorkspaceName,
                        source_snapshot_name=sourceSnapshotName, new_workspace_password=newWorkspacePassword, volume_snapshot_class=volumeSnapshotClass,
                        namespace=namespace, request_cpu=requestCpu, request_memory=requestMemory,
                        request_nvidia_gpu=requestNvidiaGpu, print_output=printOutput)


@deprecated
def cloneVolume(newPvcName: str, sourcePvcName: str, sourceSnapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", printOutput: bool = False, pvcLabels: dict = None) :
    clone_volume(new_pvc_name=newPvcName, source_pvc_name=sourcePvcName, source_snapshot_name=sourceSnapshotName,
                    volume_snapshot_class=volumeSnapshotClass, namespace=namespace, print_output=printOutput, pvc_labels=pvcLabels)


@deprecated
def createJupyterLab(workspaceName: str, workspaceSize: str, storageClass: str = None, namespace: str = "default", workspacePassword: str = None, workspaceImage: str = "jupyter/tensorflow-notebook", requestCpu: str = None, requestMemory: str = None, requestNvidiaGpu: str = None, printOutput: bool = False, pvcAlreadyExists: bool = False, labels: dict = None) -> str :
    return create_jupyter_lab(workspace_name=workspaceName, workspace_size=workspaceSize, storage_class=storageClass,
                        namespace=namespace, workspace_password=workspacePassword, workspace_image=workspaceImage, request_cpu=requestCpu,
                        request_memory=requestMemory, request_nvidia_gpu=requestNvidiaGpu, print_output=printOutput, pvc_already_exists=pvcAlreadyExists, labels=labels)


@deprecated
def createJupyterLabSnapshot(workspaceName: str, snapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", printOutput: bool = False) :
    create_jupyter_lab_snapshot(workspace_name=workspaceName, snapshot_name=snapshotName,
                                volume_snapshot_class=volumeSnapshotClass, namespace=namespace, print_output=printOutput)


@deprecated
def createVolume(pvcName: str, volumeSize: str, storageClass: str = None, namespace: str = "default", printOutput: bool = False, pvcLabels: dict = {"created-by": "ntap-dsutil", "created-by-operation": "create-volume"}, sourceSnapshot: str = None, sourcePvc: str = None) :
    create_volume(pvc_name=pvcName, volume_size=volumeSize, storage_class=storageClass, namespace=namespace,
                    print_output=printOutput, pvc_labels=pvcLabels, source_snapshot=sourceSnapshot, source_pvc=sourcePvc)


@deprecated
def createVolumeSnapshot(pvcName: str, snapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", printOutput: bool = False) :
    create_volume_snapshot(pvc_name=pvcName, snapshot_name=snapshotName,
                            volume_snapshot_class=volumeSnapshotClass, namespace=namespace, print_output=printOutput)


@deprecated
def deleteJupyterLab(workspaceName: str, namespace: str = "default", preserveSnapshots: bool = False, printOutput: bool = False) :
    delete_jupyter_lab(workspace_name=workspaceName, namespace=namespace, preserve_snapshots=preserveSnapshots,
                        print_output=printOutput)


@deprecated
def deleteVolume(pvcName: str, namespace: str = "default", preserveSnapshots: bool = False, printOutput: bool = False) :
    delete_volume(pvc_name=pvcName, namespace=namespace, preserve_snapshots=preserveSnapshots,
                    print_output=printOutput)


@deprecated
def deleteVolumeSnapshot(snapshotName: str, namespace: str = "default", printOutput: bool = False) :
    delete_volume_snapshot(snapshot_name=snapshotName, namespace=namespace, print_output=printOutput)


@deprecated
def listJupyterLabs(namespace: str = "default", printOutput: bool = False) -> list :
    return list_jupyter_labs(namespace=namespace, print_output=printOutput)


@deprecated
def listJupyterLabSnapshots(workspaceName: str = None, namespace: str = "default", printOutput: bool = False) :
    list_jupyter_lab_snapshots(workspace_name=workspaceName, namespace=namespace, print_output=printOutput)


@deprecated
def listVolumes(namespace: str = "default", printOutput: bool = False) -> list :
    return list_volumes(namespace=namespace, print_output=printOutput)


@deprecated
def listVolumeSnapshots(pvcName: str = None, namespace: str = "default", printOutput: bool = False, jupyterLabWorkspacesOnly: bool = False) -> list :
    return list_volume_snapshots(pvc_name=pvcName, namespace=namespace, print_output=printOutput, jupyter_lab_workspaces_only=jupyterLabWorkspacesOnly)


@deprecated
def restoreJupyterLabSnapshot(snapshotName: str = None, namespace: str = "default", printOutput: bool = False) :
    restore_jupyter_lab_snapshot(snapshot_name=snapshotName, namespace=namespace, print_output=printOutput)


@deprecated
def restoreVolumeSnapshot(snapshotName: str, namespace: str = "default", printOutput: bool = False, pvcLabels: dict = {"created-by": "ntap-dsutil", "created-by-operation": "restore-volume-snapshot"}) :
    restore_volume_snapshot(snapshot_name=snapshotName, namespace=namespace, print_output=printOutput, pvc_labels=pvcLabels)
