"""NetApp Data Science Toolkit for Cloud Environments import module.

This module provides the public functions available to be imported directly
by applications using the import method of utilizing the toolkit.
"""

__version__ = "0.0.1a1"

from datetime import datetime
from getpass import getpass
from time import sleep

import IPython
from kubernetes import client, config
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.rest import ApiException
from tabulate import tabulate
import pandas as pd


#
# Class definitions
#


class APIConnectionError(Exception):
    '''Error that will be raised when an API connection cannot be established'''
    pass


class InvalidConfigError(Exception):
    '''Error that will be raised when the config file is invalid or missing'''
    pass


#
# Private functions
#


def jupyterLabDeployment(workspaceName: str) -> str:
    return jupyterLabPrefix() + workspaceName


def jupyterLabLabels(workspaceName: str) -> dict:
    labels = {
        "app": jupyterLabPrefix() + workspaceName,
        "created-by": "ntap-dsutil",
        "entity-type": "jupyterlab-workspace",
        "created-by-operation": "create-jupyterlab",
        "jupyterlab-workspace-name": workspaceName
    }
    return labels


def jupyterLabPrefix() -> str:
    return "ntap-dsutil-jupyterlab-"


def jupyterLabLabelSelector() -> str:
    labels = jupyterLabLabels(workspaceName="temp")
    return "created-by=" + labels["created-by"] + ",entity-type=" + labels["entity-type"]


def jupyterLabService(workspaceName: str) -> str:
    return jupyterLabPrefix() + workspaceName


def jupyterLabWorkspacePVCName(workspaceName: str) -> str:
    return jupyterLabPrefix() + workspaceName


def listVolumeSnapshots(pvcName: str = None, namespace: str = "default", printOutput: bool = False,
                        jupyterLabWorkspacesOnly: bool = False) -> list:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve list of Snapshots
    try:
        api = client.CustomObjectsApi()
        volumeSnapshotList = api.list_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(),
                                                               namespace=namespace, plural="volumesnapshots")
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct list of snapshots
    snapshotsList = list()
    # return volumeSnapshotList
    for volumeSnapshot in volumeSnapshotList["items"]:
        # Construct dict containing snapshot details
        if (not pvcName) or (volumeSnapshot["spec"]["source"]["persistentVolumeClaimName"] == pvcName):
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
                snapshotDict["Source JupyterLab workspace"] = retrieveJupyterLabWorkspaceForPvc(
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
            if jupyterLabWorkspacesOnly:
                if jupyterLabWorkspace:
                    snapshotsList.append(snapshotDict)
            else:
                snapshotsList.append(snapshotDict)

    # Print list of snapshots
    if printOutput:
        # Convert snapshots array to Pandas DataFrame
        snapshotsDF = pd.DataFrame.from_dict(snapshotsList, dtype="string")
        print(tabulate(snapshotsDF, showindex=False, headers=snapshotsDF.columns))

    return snapshotsList


def loadKubeConfig():
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()


def printInvalidConfigError():
    print(
        "Error: Missing or invalid kubeconfig file. The NetApp Data Science Toolkit for Kubernetes requires that a valid kubeconfig file be present on the host, located at $HOME/.kube or at another path specified by the KUBECONFIG environment variable.")


def retrieveImageForJupyterLabDeployment(workspaceName: str, namespace: str = "default",
                                         printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve image
    try:
        api = client.AppsV1Api()
        deployment = api.read_namespaced_deployment(namespace=namespace,
                                                    name=jupyterLabDeployment(workspaceName=workspaceName))
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    return deployment.spec.template.spec.containers[0].image


def retrieveJupyterLabURL(workspaceName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve node IP (random node)
    try:
        api = client.CoreV1Api()
        nodes = api.list_node()
        ip = nodes.items[0].status.addresses[0].address
    except:
        ip = "<IP address of Kubernetes node>"
        pass

    # Retrieve access port
    try:
        api = client.CoreV1Api()
        serviceStatus = api.read_namespaced_service(namespace=namespace,
                                                    name=jupyterLabService(workspaceName=workspaceName))
        port = serviceStatus.spec.ports[0].node_port
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct and return url
    return "http://" + ip + ":" + str(port)


def retrieveJupyterLabWorkspaceForPvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
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


def retrieveSizeForPvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
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


def retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName: str, namespace: str = "default",
                                                 printOutput: bool = False) -> (str, str):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve source PVC and restoreSize
    try:
        api = client.CustomObjectsApi()
        volumeSnapshot = api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(),
                                                          namespace=namespace, name=snapshotName,
                                                          plural="volumesnapshots")
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    sourcePvcName = volumeSnapshot["spec"]["source"]["persistentVolumeClaimName"]
    restoreSize = volumeSnapshot["status"]["restoreSize"]

    return sourcePvcName, restoreSize


def retrieveStorageClassForPvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
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


def scaleJupyterLabDeployment(workspaceName: str, numPods: int, namespace: str = "default", printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Scale deployment
    deploymentName = jupyterLabDeployment(workspaceName=workspaceName)
    deployment = {
        "metadata": {
            "name": deploymentName
        },
        "spec": {
            "replicas": numPods
        }
    }
    if printOutput:
        print("Scaling Deployment '" + jupyterLabDeployment(
            workspaceName=workspaceName) + "' in namespace '" + namespace + "' to " + str(numPods) + " pod(s).")
    try:
        api = client.AppsV1Api()
        api.patch_namespaced_deployment(name=deploymentName, namespace=namespace, body=deployment)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)


def snapshotApiGroup() -> str:
    # TODO: get this from config file?
    return "snapshot.storage.k8s.io"


def snapshotApiVersion() -> str:
    # TODO: get this from config file?
    return "v1beta1"


def waitForJupyterLabDeploymentReady(workspaceName: str, namespace: str = "default", printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Wait for deployment to be ready
    if printOutput:
        print(
            "Waiting for Deployment '" + jupyterLabDeployment(workspaceName=workspaceName) + "' to reach Ready state.")
    while True:
        try:
            api = client.AppsV1Api()
            deploymentStatus = api.read_namespaced_deployment_status(namespace=namespace, name=jupyterLabDeployment(
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

def cloneJupyterLab(newWorkspaceName: str, sourceWorkspaceName: str, sourceSnapshotName: str = None,
                    newWorkspacePassword: str = None, volumeSnapshotClass: str = "csi-snapclass",
                    namespace: str = "default", requestCpu: str = None, requestMemory: str = None,
                    requestNvidiaGpu: str = None, printOutput: bool = False):
    # Determine source PVC details
    if sourceSnapshotName:
        sourcePvcName, workspaceSize = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=sourceSnapshotName,
                                                                                    namespace=namespace,
                                                                                    printOutput=printOutput)
        if printOutput:
            print(
                "Creating new JupyterLab workspace '" + newWorkspaceName + "' from VolumeSnapshot '" + sourceSnapshotName + "' in namespace '" + namespace + "'...\n")
    else:
        sourcePvcName = jupyterLabWorkspacePVCName(workspaceName=sourceWorkspaceName)
        workspaceSize = retrieveSizeForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)
        if printOutput:
            print(
                "Creating new JupyterLab workspace '" + newWorkspaceName + "' from source workspace '" + sourceWorkspaceName + "' in namespace '" + namespace + "'...\n")

    # Determine source workspace details
    if not sourceWorkspaceName:
        sourceWorkspaceName = retrieveJupyterLabWorkspaceForPvc(pvcName=sourcePvcName, namespace=namespace,
                                                                printOutput=printOutput)
    sourceWorkspaceImage = retrieveImageForJupyterLabDeployment(workspaceName=sourceWorkspaceName, namespace=namespace,
                                                                printOutput=printOutput)

    # Set labels
    labels = jupyterLabLabels(workspaceName=newWorkspaceName)
    labels["created-by-operation"] = "clone-jupyterlab"
    labels["source-jupyterlab-workspace"] = sourceWorkspaceName
    labels["source-pvc"] = sourcePvcName

    # Clone workspace PVC
    cloneVolume(newPvcName=jupyterLabWorkspacePVCName(workspaceName=newWorkspaceName), sourcePvcName=sourcePvcName,
                sourceSnapshotName=sourceSnapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace,
                printOutput=printOutput, pvcLabels=labels)

    # Remove source PVC from labels
    del labels["source-pvc"]

    # Create new workspace
    print()
    createJupyterLab(workspaceName=newWorkspaceName, workspaceSize=workspaceSize, namespace=namespace,
                     workspacePassword=newWorkspacePassword, workspaceImage=sourceWorkspaceImage, requestCpu=requestCpu,
                     requestMemory=requestMemory, requestNvidiaGpu=requestNvidiaGpu, printOutput=printOutput,
                     pvcAlreadyExists=True, labels=labels)

    if printOutput:
        print("JupyterLab workspace successfully cloned.")


def cloneVolume(newPvcName: str, sourcePvcName: str, sourceSnapshotName: str = None,
                volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", printOutput: bool = False,
                pvcLabels: dict = None):
    # Handle volume source
    if not sourceSnapshotName:
        # Create new VolumeSnapshot to use as source for clone
        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        sourceSnapshotName = "ntap-dsutil.for-clone." + timestamp
        if printOutput:
            print(
                "Creating new VolumeSnapshot '" + sourceSnapshotName + "' for source PVC '" + sourcePvcName + "' in namespace '" + namespace + "' to use as source for clone...")
        createVolumeSnapshot(pvcName=sourcePvcName, snapshotName=sourceSnapshotName,
                             volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=printOutput)

    # Retrieve source volume details
    sourcePvcName, restoreSize = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=sourceSnapshotName,
                                                                              namespace=namespace,
                                                                              printOutput=printOutput)
    storageClass = retrieveStorageClassForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)

    # Set PVC labels
    if not pvcLabels:
        pvcLabels = {"created-by": "ntap-dsutil", "created-by-operation": "clone-volume", "source-pvc": sourcePvcName}

    # Create new PVC from snapshot
    if printOutput:
        print(
            "Creating new PersistentVolumeClaim (PVC) '" + newPvcName + "' from VolumeSnapshot '" + sourceSnapshotName + "' in namespace '" + namespace + "'...")
    createVolume(pvcName=newPvcName, volumeSize=restoreSize, storageClass=storageClass, namespace=namespace,
                 printOutput=printOutput, pvcLabels=pvcLabels, sourceSnapshot=sourceSnapshotName)

    if printOutput:
        print("Volume successfully cloned.")


def createJupyterLab(workspaceName: str, workspaceSize: str, storageClass: str = None, namespace: str = "default",
                     workspacePassword: str = None, workspaceImage: str = "jupyter/tensorflow-notebook",
                     requestCpu: str = None, requestMemory: str = None, requestNvidiaGpu: str = None,
                     printOutput: bool = False, pvcAlreadyExists: bool = False, labels: dict = None) -> str:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Set labels
    if not labels:
        labels = jupyterLabLabels(workspaceName=workspaceName)

    # Step 0 - Set password
    if not workspacePassword:
        while True:
            workspacePassword = getpass(
                "Set workspace password (this password will be required in order to access the workspace): ")
            if getpass("Re-enter password: ") == workspacePassword:
                break
            else:
                print("Error: Passwords do not match. Try again.")
    hashedPassword = IPython.lib.passwd(workspacePassword)

    # Step 1 - Create PVC for workspace
    if not pvcAlreadyExists:
        if printOutput:
            print("\nCreating persistent volume for workspace...")
        try:
            createVolume(pvcName=jupyterLabWorkspacePVCName(workspaceName=workspaceName), volumeSize=workspaceSize,
                         storageClass=storageClass, namespace=namespace, pvcLabels=labels, printOutput=printOutput)
        except:
            if printOutput:
                print("Aborting workspace creation...")
            raise

    # Step 2 - Create service for workspace

    # Construct service
    service = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=jupyterLabService(workspaceName=workspaceName),
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
    if printOutput:
        print("\nCreating Service '" + jupyterLabService(
            workspaceName=workspaceName) + "' in namespace '" + namespace + "'.")
    try:
        api = client.CoreV1Api()
        api.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
            print("Aborting workspace creation...")
        raise APIConnectionError(err)

    if printOutput:
        print("Service successfully created.")

    # Step 3 - Create deployment

    # Construct deployment
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=jupyterLabDeployment(workspaceName=workspaceName),
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
                                "claimName": jupyterLabWorkspacePVCName(workspaceName=workspaceName)
                            }
                        )
                    ],
                    containers=[
                        client.V1Container(
                            name="jupyterlab",
                            image=workspaceImage,
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
                            security_context=client.V1PodSecurityContext(
                                run_as_user=0
                            ),
                            args=["start-notebook.sh", "--LabApp.password=" + hashedPassword, "--LabApp.ip='0.0.0.0'",
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
    if requestCpu:
        deployment.spec.template.spec.containers[0].resources["requests"]["cpu"] = requestCpu
    if requestMemory:
        deployment.spec.template.spec.containers[0].resources["requests"]["memory"] = requestMemory
    if requestNvidiaGpu:
        deployment.spec.template.spec.containers[0].resources["requests"]["nvidia.com/gpu"] = requestNvidiaGpu
        deployment.spec.template.spec.containers[0].resources["limits"]["nvidia.com/gpu"] = requestNvidiaGpu

    # Create deployment
    if printOutput:
        print("\nCreating Deployment '" + jupyterLabDeployment(
            workspaceName=workspaceName) + "' in namespace '" + namespace + "'.")
    try:
        api = client.AppsV1Api()
        api.create_namespaced_deployment(namespace=namespace, body=deployment)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
            print("Aborting workspace creation...")
        raise APIConnectionError(err)

    # Wait for deployment to be ready
    if printOutput:
        print("Deployment '" + jupyterLabDeployment(workspaceName=workspaceName) + "' created.")
    waitForJupyterLabDeploymentReady(workspaceName=workspaceName, namespace=namespace, printOutput=printOutput)

    if printOutput:
        print("Deployment successfully created.")

    # Step 4 - Retrieve access URL
    try:
        url = retrieveJupyterLabURL(workspaceName=workspaceName, namespace=namespace, printOutput=printOutput)
    except APIConnectionError as err:
        if printOutput:
            print("Aborting workspace creation...")
        raise

    if printOutput:
        print("\nWorkspace successfully created.")
        print("To access workspace, navigate to " + url)

    return url


def createJupyterLabSnapshot(workspaceName: str, snapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass",
                             namespace: str = "default", printOutput: bool = False):
    # Create snapshot
    if printOutput:
        print(
            "Creating VolumeSnapshot for JupyterLab workspace '" + workspaceName + "' in namespace '" + namespace + "'...")
    createVolumeSnapshot(pvcName=jupyterLabWorkspacePVCName(workspaceName=workspaceName), snapshotName=snapshotName,
                         volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=printOutput)


def createVolume(pvcName: str, volumeSize: str, storageClass: str = None, namespace: str = "default",
                 printOutput: bool = False,
                 pvcLabels: dict = {"created-by": "ntap-dsutil", "created-by-operation": "create-volume"},
                 sourceSnapshot: str = None, sourcePvc: str = None):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Construct PVC
    pvc = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(
            name=pvcName,
            labels=pvcLabels
        ),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteMany"],
            resources=client.V1ResourceRequirements(
                requests={
                    'storage': volumeSize
                }
            )
        )
    )

    # Apply custom storageClass if specified
    if storageClass:
        pvc.spec.storage_class_name = storageClass

    # Apply source snapshot if specified
    if sourceSnapshot:
        pvc.spec.data_source = {
            'name': sourceSnapshot,
            'kind': 'VolumeSnapshot',
            'apiGroup': snapshotApiGroup()
        }
    # Apply source PVC if specified
    elif sourcePvc:
        pvc.metadata.annotations = {
            'trident.netapp.io/cloneFromPVC': sourcePvc
        }

    # Create PVC
    if printOutput:
        print("Creating PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'.")
    try:
        api = client.CoreV1Api()
        api.create_namespaced_persistent_volume_claim(body=pvc, namespace=namespace)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for PVC to bind to volume
    if printOutput:
        print("PersistentVolumeClaim (PVC) '" + pvcName + "' created. Waiting for Kubernetes to bind volume to PVC.")
    while True:
        try:
            api = client.CoreV1Api()
            pvcStatus = api.read_namespaced_persistent_volume_claim_status(name=pvcName, namespace=namespace)
        except ApiException as err:
            if printOutput:
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        if pvcStatus.status.phase == "Bound":
            break
        sleep(5)

    if printOutput:
        print(
            "Volume successfully created and bound to PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'.")


def createVolumeSnapshot(pvcName: str, snapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass",
                         namespace: str = "default", printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Set snapshot name if not passed into function
    if not snapshotName:
        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        snapshotName = "ntap-dsutil." + timestamp

    # Construct dict representing snapshot
    snapshot = {
        "apiVersion": snapshotApiGroup() + "/" + snapshotApiVersion(),
        "kind": "VolumeSnapshot",
        "metadata": {
            "name": snapshotName
        },
        "spec": {
            "volumeSnapshotClassName": volumeSnapshotClass,
            "source": {
                "persistentVolumeClaimName": pvcName
            }
        }
    }

    # Create snapshot
    if printOutput:
        print(
            "Creating VolumeSnapshot '" + snapshotName + "' for PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'.")
    try:
        api = client.CustomObjectsApi()
        api.create_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace,
                                            body=snapshot, plural="volumesnapshots")
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for snapshot creation to complete
    if printOutput:
        print(
            "VolumeSnapshot '" + snapshotName + "' created. Waiting for Trident to create snapshot on backing storage.")
    while True:
        try:
            api = client.CustomObjectsApi()
            snapshotStatus = api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(),
                                                              namespace=namespace, name=snapshotName,
                                                              plural="volumesnapshots")
        except ApiException as err:
            if printOutput:
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        try:
            if snapshotStatus["status"]["readyToUse"] == True:
                break
        except:
            pass
        sleep(5)

    if printOutput:
        print("Snapshot successfully created.")


def deleteJupyterLab(workspaceName: str, namespace: str = "default", preserveSnapshots: bool = False,
                     printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Delete workspace
    if printOutput:
        print("Deleting workspace '" + workspaceName + "' in namespace '" + namespace + "'.")
    try:
        # Delete deployment
        if printOutput:
            print("Deleting Deployment...")
        api = client.AppsV1Api()
        api.delete_namespaced_deployment(namespace=namespace, name=jupyterLabDeployment(workspaceName=workspaceName))

        # Delete service
        if printOutput:
            print("Deleting Service...")
        api = client.CoreV1Api()
        api.delete_namespaced_service(namespace=namespace, name=jupyterLabService(workspaceName=workspaceName))

    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Delete PVC
    if printOutput:
        print("Deleting PVC...")
    deleteVolume(pvcName=jupyterLabWorkspacePVCName(workspaceName=workspaceName), namespace=namespace,
                 preserveSnapshots=preserveSnapshots, printOutput=printOutput)

    if printOutput:
        print("Workspace successfully deleted.")


def deleteVolume(pvcName: str, namespace: str = "default", preserveSnapshots: bool = False, printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Optionally delete snapshots
    if not preserveSnapshots:
        if printOutput:
            print(
                "Deleting all VolumeSnapshots associated with PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'...")

        # Retrieve list of snapshots for PVC
        try:
            snapshotList = listVolumeSnapshots(pvcName=pvcName, namespace=namespace, printOutput=False)
        except APIConnectionError as err:
            if printOutput:
                print("Error: Kubernetes API Error: ", err)
            raise

        # Delete each snapshot
        for snapshot in snapshotList:
            deleteVolumeSnapshot(snapshotName=snapshot["VolumeSnapshot Name"], namespace=namespace,
                                 printOutput=printOutput)

    # Delete PVC
    if printOutput:
        print(
            "Deleting PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "' and associated volume.")
    try:
        api = client.CoreV1Api()
        api.delete_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for PVC to disappear
    while True:
        try:
            api = client.CoreV1Api()
            api.read_namespaced_persistent_volume_claim(name=pvcName,
                                                        namespace=namespace)  # Confirm that source PVC still exists
        except:
            break  # Break loop when source PVC no longer exists
        sleep(5)

    if printOutput:
        print("PersistentVolumeClaim (PVC) successfully deleted.")


def deleteVolumeSnapshot(snapshotName: str, namespace: str = "default", printOutput: bool = False):
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Delete VolumeSnapshot
    if printOutput:
        print("Deleting VolumeSnapshot '" + snapshotName + "' in namespace '" + namespace + "'.")
    try:
        api = client.CustomObjectsApi()
        api.delete_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace,
                                            plural="volumesnapshots", name=snapshotName)
    except ApiException as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for VolumeSnapshot to disappear
    while True:
        try:
            api = client.CustomObjectsApi()
            api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(),
                                             namespace=namespace, plural="volumesnapshots",
                                             name=snapshotName)  # Confirm that VolumeSnapshot still exists
        except:
            break  # Break loop when snapshot no longer exists
        sleep(5)

    if printOutput:
        print("VolumeSnapshot successfully deleted.")


def listJupyterLabs(namespace: str = "default", printOutput: bool = False) -> list:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve list of workspaces
    try:
        api = client.AppsV1Api()
        deployments = api.list_namespaced_deployment(namespace=namespace, label_selector=jupyterLabLabelSelector())
    except ApiException as err:
        if printOutput:
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
            pvc = api.read_namespaced_persistent_volume_claim(namespace=namespace, name=jupyterLabWorkspacePVCName(
                workspaceName=workspaceName))
            workspaceDict["Size"] = pvc.status.capacity["storage"]
            workspaceDict["StorageClass"] = pvc.spec.storage_class_name
        except:
            workspaceDict["Size"] = ""
            workspaceDict["StorageClass"] = ""

        # Retrieve access URL
        workspaceDict["Access URL"] = retrieveJupyterLabURL(workspaceName=workspaceName, namespace=namespace,
                                                            printOutput=printOutput)

        # Retrieve clone details
        try:
            if deployment.metadata.labels["created-by-operation"] == "clone-jupyterlab":
                workspaceDict["Clone"] = "Yes"
                workspaceDict["Source Workspace"] = pvc.metadata.labels["source-jupyterlab-workspace"]
                try:
                    api = client.AppsV1Api()
                    deployments = api.read_namespaced_deployment(namespace=namespace, name=jupyterLabDeployment(
                        workspaceName=workspaceDict["Source Workspace"]))
                except:
                    workspaceDict["Source Workspace"] = "*deleted*"
                try:
                    workspaceDict["Source VolumeSnapshot"] = pvc.spec.data_source.name
                    try:
                        api = client.CustomObjectsApi()
                        api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(),
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
    if printOutput:
        # Convert workspaces array to Pandas DataFrame
        workspacesDF = pd.DataFrame.from_dict(workspacesList, dtype="string")
        print(tabulate(workspacesDF, showindex=False, headers=workspacesDF.columns))

    return workspacesList


def listJupyterLabSnapshots(workspaceName: str = None, namespace: str = "default", printOutput: bool = False):
    # Determine PVC name
    if workspaceName:
        pvcName = jupyterLabWorkspacePVCName(workspaceName=workspaceName)
    else:
        pvcName = None

    # List snapshots
    return listVolumeSnapshots(pvcName=pvcName, namespace=namespace, printOutput=printOutput,
                               jupyterLabWorkspacesOnly=True)


def listVolumes(namespace: str = "default", printOutput: bool = False) -> list:
    # Retrieve kubeconfig
    try:
        loadKubeConfig()
    except:
        if printOutput:
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve list of PVCs
    try:
        api = client.CoreV1Api()
        pvcList = api.list_namespaced_persistent_volume_claim(namespace=namespace)
    except ApiException as err:
        if printOutput:
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
                        api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(),
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
    if printOutput:
        # Convert volumes array to Pandas DataFrame
        volumesDF = pd.DataFrame.from_dict(volumesList, dtype="string")
        print(tabulate(volumesDF, showindex=False, headers=volumesDF.columns))

    return volumesList


def restoreJupyterLabSnapshot(snapshotName: str = None, namespace: str = "default", printOutput: bool = False):
    # Retrieve source PVC name
    sourcePvcName = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=snapshotName, namespace=namespace,
                                                                 printOutput=printOutput)[0]

    # Retrieve workspace name
    workspaceName = retrieveJupyterLabWorkspaceForPvc(pvcName=sourcePvcName, namespace=namespace,
                                                      printOutput=printOutput)

    # Set labels
    labels = jupyterLabLabels(workspaceName=workspaceName)
    labels["created-by-operation"] = "restore-jupyterlab-snapshot"

    if printOutput:
        print(
            "Restoring VolumeSnapshot '" + snapshotName + "' for JupyterLab workspace '" + workspaceName + "' in namespace '" + namespace + "'...")

    # Scale deployment to 0 pods
    scaleJupyterLabDeployment(workspaceName=workspaceName, numPods=0, namespace=namespace, printOutput=printOutput)
    sleep(5)

    # Restore snapshot
    restoreVolumeSnapshot(snapshotName=snapshotName, namespace=namespace, printOutput=printOutput, pvcLabels=labels)

    # Scale deployment to 1 pod
    scaleJupyterLabDeployment(workspaceName=workspaceName, numPods=1, namespace=namespace, printOutput=printOutput)

    # Wait for deployment to reach ready state
    waitForJupyterLabDeploymentReady(workspaceName=workspaceName, namespace=namespace, printOutput=printOutput)

    if printOutput:
        print("JupyterLab workspace snapshot successfully restored.")


def restoreVolumeSnapshot(snapshotName: str, namespace: str = "default", printOutput: bool = False,
                          pvcLabels: dict = {"created-by": "ntap-dsutil",
                                             "created-by-operation": "restore-volume-snapshot"}):
    # Retrieve source PVC, restoreSize, and StorageClass
    sourcePvcName, restoreSize = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=snapshotName,
                                                                              namespace=namespace,
                                                                              printOutput=printOutput)
    storageClass = retrieveStorageClassForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)

    if printOutput:
        print(
            "Restoring VolumeSnapshot '" + snapshotName + "' for PersistentVolumeClaim '" + sourcePvcName + "' in namespace '" + namespace + "'.")

    # Delete source PVC
    try:
        deleteVolume(pvcName=sourcePvcName, namespace=namespace, preserveSnapshots=True, printOutput=False)
    except APIConnectionError as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise

    # Create new PVC from snapshot
    try:
        createVolume(pvcName=sourcePvcName, volumeSize=restoreSize, storageClass=storageClass, namespace=namespace,
                     printOutput=False, pvcLabels=pvcLabels, sourceSnapshot=snapshotName)
    except APIConnectionError as err:
        if printOutput:
            print("Error: Kubernetes API Error: ", err)
        raise

    if printOutput:
        print("VolumeSnapshot successfully restored.")
