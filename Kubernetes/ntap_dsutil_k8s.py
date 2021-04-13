#!/usr/bin/env python3

## NetApp Data Science Toolkit for Kubernetes
version = "1.2"


from os import name
from kubernetes import client, config
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.models.v1_persistent_volume_claim import V1PersistentVolumeClaim
from kubernetes.client.models.v1_pod_template import V1PodTemplate
from kubernetes.client.rest import ApiException
import IPython
from getpass import getpass
import pandas as pd
from tabulate import tabulate
from time import sleep
from datetime import datetime


## API connection error class; objects of this class will be raised when an API connection cannot be established
class APIConnectionError(Exception) :
    '''Error that will be raised when an API connection cannot be established'''
    pass


## Invalid config error class; objects of this class will be raised when the config file is invalid or missing
class InvalidConfigError(Exception) :
    '''Error that will be raised when the config file is invalid or missing'''
    pass

## Config related functions

# Function for printing appropriate error message when config file is missing or invalid
def printInvalidConfigError() :
    print("Error: Missing or invalid kubeconfig file. The NetApp Data Science Toolkit for Kubernetes requires that a valid kubeconfig file be present on the host, located at $HOME/.kube or at another path specified by the KUBECONFIG environment variable.")

# Function for loading kubeconfig
def loadKubeConfig() :
    try :
        config.load_incluster_config()
    except :
        config.load_kube_config()


## Functions for defining various snapshot/volume parameters

# API group
def snapshotApiGroup() -> str :
    return "snapshot.storage.k8s.io"

# API version
def snapshotApiVersion() -> str :
    return "v1beta1"

# Function for retrieving source volume details from a volume snapshot
def retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName: str, namespace: str = "default", printOutput: bool = False) -> (str, str) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve source PVC and restoreSize
    try :
        api = client.CustomObjectsApi()
        volumeSnapshot = api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, name=snapshotName, plural="volumesnapshots")
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    sourcePvcName = volumeSnapshot["spec"]["source"]["persistentVolumeClaimName"]
    restoreSize = volumeSnapshot["status"]["restoreSize"]

    return sourcePvcName, restoreSize

# Function for retrieving StorageClass for pvc
def retrieveStorageClassForPvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve StorageClass
    try :
        api = client.CoreV1Api()
        pvc = api.read_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    storageClass = pvc.spec.storage_class_name

    return storageClass

# Function for retrieving size of a pvc
def retrieveSizeForPvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve size
    try :
        api = client.CoreV1Api()
        pvc = api.read_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    pvcSize = pvc.status.capacity["storage"]

    return pvcSize

# Function for retrieving JupyterLab workspace name from a pvc
def retrieveJupyterLabWorkspaceForPvc(pvcName: str, namespace: str = "default", printOutput: bool = False) -> str :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve workspace name
    try :
        api = client.CoreV1Api()
        pvc = api.read_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
        workspaceName = pvc.metadata.labels["jupyterlab-workspace-name"]
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    return workspaceName


## Function for listing all volumes
def listVolumes(namespace: str = "default", printOutput: bool = False) -> list :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve list of PVCs
    try :
        api = client.CoreV1Api()
        pvcList = api.list_namespaced_persistent_volume_claim(namespace=namespace)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct list of volumes
    volumesList = list()
    for pvc in pvcList.items :
        # Construct dict containing volume details
        volumeDict = dict()
        volumeDict["PersistentVolumeClaim (PVC) Name"] = pvc.metadata.name
        volumeDict["Status"] = pvc.status.phase
        try :
            volumeDict["Size"] = pvc.status.capacity["storage"]
        except :
            volumeDict["Size"] = ""
        try :
            volumeDict["StorageClass"] = pvc.spec.storage_class_name
        except :
            volumeDict["StorageClass"] = ""
        try :
            if (pvc.metadata.labels["created-by-operation"] == "clone-volume") or (pvc.metadata.labels["created-by-operation"] == "clone-jupyterlab") :
                volumeDict["Clone"] = "Yes"
                volumeDict["Source PVC"] = pvc.metadata.labels["source-pvc"]
                try :
                    api = client.CoreV1Api()
                    api.read_namespaced_persistent_volume_claim(name=volumeDict["Source PVC"], namespace=namespace) # Confirm that source PVC still exists
                except :
                    volumeDict["Source PVC"] = "*deleted*"
                try :
                    volumeDict["Source VolumeSnapshot"] = pvc.spec.data_source.name
                    try :
                        api = client.CustomObjectsApi()
                        api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, plural="volumesnapshots", name=volumeDict["Source VolumeSnapshot"])   # Confirm that VolumeSnapshot still exists
                    except :
                        volumeDict["Source VolumeSnapshot"] = "*deleted*"
                except :
                    volumeDict["Source VolumeSnapshot"] = "n/a"
            else :
                volumeDict["Clone"] = "No"
                volumeDict["Source PVC"] = ""
                volumeDict["Source VolumeSnapshot"] = ""
        except :
            volumeDict["Clone"] = "No"
            volumeDict["Source PVC"] = ""
            volumeDict["Source VolumeSnapshot"] = ""
        
        # Append dict to list of volumes
        volumesList.append(volumeDict)

    # Print list of volumes
    if printOutput :
        # Convert volumes array to Pandas DataFrame
        volumesDF = pd.DataFrame.from_dict(volumesList, dtype="string")
        print(tabulate(volumesDF, showindex=False, headers=volumesDF.columns))

    return volumesList


## Function for listing all snapshots
def listVolumeSnapshots(pvcName: str = None, namespace: str = "default", printOutput: bool = False, jupyterLabWorkspacesOnly: bool = False) -> list :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve list of Snapshots
    try :
        api = client.CustomObjectsApi()
        volumeSnapshotList = api.list_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, plural="volumesnapshots")
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct list of snapshots
    snapshotsList = list()
    #return volumeSnapshotList
    for volumeSnapshot in volumeSnapshotList["items"] :
        # Construct dict containing snapshot details
        if (not pvcName) or (volumeSnapshot["spec"]["source"]["persistentVolumeClaimName"] == pvcName) :
            snapshotDict = dict()
            snapshotDict["VolumeSnapshot Name"] = volumeSnapshot["metadata"]["name"]
            snapshotDict["Ready to Use"] = volumeSnapshot["status"]["readyToUse"]
            try :
                snapshotDict["Creation Time"] = volumeSnapshot["status"]["creationTime"]
            except :
                snapshotDict["Creation Time"] = ""
            snapshotDict["Source PersistentVolumeClaim (PVC)"] = volumeSnapshot["spec"]["source"]["persistentVolumeClaimName"]
            try :
                api = client.CoreV1Api()
                api.read_namespaced_persistent_volume_claim(name=snapshotDict["Source PersistentVolumeClaim (PVC)"], namespace=namespace) # Confirm that source PVC still exists
            except :
                snapshotDict["Source PersistentVolumeClaim (PVC)"] = "*deleted*"
            try :
                snapshotDict["Source JupyterLab workspace"] = retrieveJupyterLabWorkspaceForPvc(pvcName=snapshotDict["Source PersistentVolumeClaim (PVC)"], namespace=namespace, printOutput=False)
                jupyterLabWorkspace = True
            except :
                snapshotDict["Source JupyterLab workspace"] = ""
                jupyterLabWorkspace = False
            try :
                snapshotDict["VolumeSnapshotClass"] = volumeSnapshot["spec"]["volumeSnapshotClassName"]
            except :
                snapshotDict["VolumeSnapshotClass"] = ""

            # Append dict to list of snapshots
            if jupyterLabWorkspacesOnly :
                if jupyterLabWorkspace :
                    snapshotsList.append(snapshotDict)
            else :
                snapshotsList.append(snapshotDict)

    # Print list of snapshots
    if printOutput :
        # Convert snapshots array to Pandas DataFrame
        snapshotsDF = pd.DataFrame.from_dict(snapshotsList, dtype="string")
        print(tabulate(snapshotsDF, showindex=False, headers=snapshotsDF.columns))

    return snapshotsList


## Function for creating a new volume
def createVolume(pvcName: str, volumeSize: str, storageClass: str = None, namespace: str = "default", printOutput: bool = False, pvcLabels: dict = {"created-by": "ntap-dsutil", "created-by-operation": "create-volume"}, sourceSnapshot: str = None, sourcePvc: str = None) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Construct PVC
    pvc = client.V1PersistentVolumeClaim(
        metadata = client.V1ObjectMeta(
            name = pvcName,
            labels = pvcLabels
        ),
        spec = client.V1PersistentVolumeClaimSpec(
            access_modes = ["ReadWriteMany"],
            resources = client.V1ResourceRequirements(
                requests = {
                    'storage': volumeSize
                }
            )
        )
    )

    # Apply custom storageClass if specified
    if storageClass :
        pvc.spec.storage_class_name = storageClass

    # Apply source snapshot if specified
    if sourceSnapshot :
        pvc.spec.data_source = {
            'name': sourceSnapshot,
            'kind': 'VolumeSnapshot',
            'apiGroup': snapshotApiGroup()
        }
    # Apply source PVC if specified
    elif sourcePvc :
        pvc.metadata.annotations = {
            'trident.netapp.io/cloneFromPVC': sourcePvc
        }

    # Create PVC
    if printOutput :
        print("Creating PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'.")
    try :
        api = client.CoreV1Api()
        api.create_namespaced_persistent_volume_claim(body=pvc, namespace=namespace)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for PVC to bind to volume
    if printOutput :
        print("PersistentVolumeClaim (PVC) '" + pvcName + "' created. Waiting for Kubernetes to bind volume to PVC.")
    while True :
        try :
            api = client.CoreV1Api()
            pvcStatus = api.read_namespaced_persistent_volume_claim_status(name=pvcName, namespace=namespace)
        except ApiException as err :
            if printOutput :
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        if pvcStatus.status.phase == "Bound" :
            break
        sleep(5)

    if printOutput :
        print("Volume successfully created and bound to PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'.")


## Function for deleting a volume
def deleteVolume(pvcName: str, namespace: str = "default", preserveSnapshots: bool = False, printOutput: bool = False) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Optionally delete snapshots
    if not preserveSnapshots :
        if printOutput :
            print("Deleting all VolumeSnapshots associated with PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'...")

        # Retrieve list of snapshots for PVC
        try :
            snapshotList = listVolumeSnapshots(pvcName=pvcName, namespace=namespace, printOutput=False)
        except APIConnectionError as err :
            if printOutput :
                print("Error: Kubernetes API Error: ", err)
            raise

        # Delete each snapshot
        for snapshot in snapshotList :
            deleteVolumeSnapshot(snapshotName=snapshot["VolumeSnapshot Name"], namespace=namespace, printOutput=printOutput)

    # Delete PVC
    if printOutput :
        print("Deleting PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "' and associated volume.")
    try :
        api = client.CoreV1Api()
        api.delete_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for PVC to disappear
    while True :
        try :
            api = client.CoreV1Api()
            api.read_namespaced_persistent_volume_claim(name=pvcName, namespace=namespace) # Confirm that source PVC still exists
        except :
            break    # Break loop when source PVC no longer exists
        sleep(5)
                

    if printOutput :
        print("PersistentVolumeClaim (PVC) successfully deleted.")


## Function for creating a snapshot
def createVolumeSnapshot(pvcName: str, snapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", printOutput: bool = False) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Set snapshot name if not passed into function
    if not snapshotName :
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
    if printOutput :
        print("Creating VolumeSnapshot '" + snapshotName + "' for PersistentVolumeClaim (PVC) '" + pvcName + "' in namespace '" + namespace + "'.")
    try :
        api = client.CustomObjectsApi()
        api.create_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, body=snapshot, plural="volumesnapshots")
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for snapshot creation to complete
    if printOutput :
        print("VolumeSnapshot '" + snapshotName + "' created. Waiting for Trident to create snapshot on backing storage.")
    while True :
        try :
            api = client.CustomObjectsApi()
            snapshotStatus = api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, name=snapshotName, plural="volumesnapshots")
        except ApiException as err :
            if printOutput :
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        try :
            if snapshotStatus["status"]["readyToUse"] == True :
                break
        except :
            pass
        sleep(5)

    if printOutput :
        print("Snapshot successfully created.")


## Function for deleting a volume snapshot
def deleteVolumeSnapshot(snapshotName: str, namespace: str = "default", printOutput: bool = False) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Delete VolumeSnapshot
    if printOutput :
        print("Deleting VolumeSnapshot '" + snapshotName + "' in namespace '" + namespace + "'.")
    try :
        api = client.CustomObjectsApi()
        api.delete_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, plural="volumesnapshots", name=snapshotName)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Wait for VolumeSnapshot to disappear
    while True :
        try :
            api = client.CustomObjectsApi()
            api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, plural="volumesnapshots", name=snapshotName)   # Confirm that VolumeSnapshot still exists
        except :
            break   # Break loop when snapshot no longer exists
        sleep(5)

    if printOutput :
        print("VolumeSnapshot successfully deleted.")


## Function for restoring a volume snapshot
def restoreVolumeSnapshot(snapshotName: str, namespace: str = "default", printOutput: bool = False, pvcLabels: dict = {"created-by": "ntap-dsutil", "created-by-operation": "restore-volume-snapshot"}) :
    # Retrieve source PVC, restoreSize, and StorageClass
    sourcePvcName, restoreSize = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=snapshotName, namespace=namespace, printOutput=printOutput)
    storageClass = retrieveStorageClassForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)

    if printOutput :
        print("Restoring VolumeSnapshot '" + snapshotName + "' for PersistentVolumeClaim '" + sourcePvcName + "' in namespace '" + namespace + "'.")

    # Delete source PVC
    try :
        deleteVolume(pvcName=sourcePvcName, namespace=namespace, preserveSnapshots=True, printOutput=False)
    except APIConnectionError as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise

    # Create new PVC from snapshot
    try :
        createVolume(pvcName=sourcePvcName, volumeSize=restoreSize, storageClass=storageClass, namespace=namespace, printOutput=False, pvcLabels=pvcLabels, sourceSnapshot=snapshotName)
    except APIConnectionError as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise

    if printOutput :
        print("VolumeSnapshot successfully restored.")


## Function for cloning a volume
def cloneVolume(newPvcName: str, sourcePvcName: str, sourceSnapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", printOutput: bool = False, pvcLabels: dict = None) :
    # Handle volume source
    if not sourceSnapshotName :
        # Create new VolumeSnapshot to use as source for clone
        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        sourceSnapshotName = "ntap-dsutil.for-clone." + timestamp
        if printOutput :
            print("Creating new VolumeSnapshot '" + sourceSnapshotName + "' for source PVC '" + sourcePvcName + "' in namespace '" + namespace + "' to use as source for clone...")
        createVolumeSnapshot(pvcName=sourcePvcName, snapshotName=sourceSnapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=printOutput)

    # Retrieve source volume details
    sourcePvcName, restoreSize = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=sourceSnapshotName, namespace=namespace, printOutput=printOutput)
    storageClass = retrieveStorageClassForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)

    # Set PVC labels
    if not pvcLabels :
        pvcLabels = {"created-by": "ntap-dsutil", "created-by-operation": "clone-volume", "source-pvc": sourcePvcName}
    
    # Create new PVC from snapshot
    if printOutput :
        print("Creating new PersistentVolumeClaim (PVC) '" + newPvcName + "' from VolumeSnapshot '" + sourceSnapshotName + "' in namespace '" + namespace + "'...")
    createVolume(pvcName=newPvcName, volumeSize=restoreSize, storageClass=storageClass, namespace=namespace, printOutput=printOutput, pvcLabels=pvcLabels, sourceSnapshot=sourceSnapshotName)

    if printOutput :
        print("Volume successfully cloned.")


## Functions for defining various JupyterLab object names

# Prefix to use for all names
def jupyterLabPrefix() -> str :
    return "ntap-dsutil-jupyterlab-"

# Workspace app label
def jupyterLabLabels(workspaceName: str) -> dict :
    labels = {
        "app": jupyterLabPrefix()+workspaceName,
        "created-by": "ntap-dsutil",
        "entity-type": "jupyterlab-workspace",
        "created-by-operation": "create-jupyterlab",
        "jupyterlab-workspace-name": workspaceName
    }
    return labels

# Label selector
def jupyterLabLabelSelector() -> str :
    labels = jupyterLabLabels(workspaceName="temp")
    return "created-by="+labels["created-by"]+",entity-type="+labels["entity-type"]

# Workspace PVC
def jupyterLabWorkspacePVCName(workspaceName: str) -> str :
    return jupyterLabPrefix()+workspaceName

# Workspace service
def jupyterLabService(workspaceName: str) -> str :
    return jupyterLabPrefix()+workspaceName

# Workspace deployment
def jupyterLabDeployment(workspaceName: str) -> str :
    return jupyterLabPrefix()+workspaceName


## Functions relating to JupyterLab workspaces

# Function for retrieving JupyterLab access url
def retrieveJupyterLabURL(workspaceName: str, namespace: str = "default", printOutput: bool = False) -> str :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve node IP (random node)
    try :
        api = client.CoreV1Api()
        nodes = api.list_node()
        ip = nodes.items[0].status.addresses[0].address
    except :
        ip = "<IP address of Kubernetes node>"
        pass
    
    # Retrieve access port
    try :
        api = client.CoreV1Api()
        serviceStatus = api.read_namespaced_service(namespace=namespace, name=jupyterLabService(workspaceName=workspaceName))
        port = serviceStatus.spec.ports[0].node_port
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct and return url
    return "http://"+ip+":"+str(port)

# Function for scaling a JupyterLab workspace deployment
def scaleJupyterLabDeployment(workspaceName: str, numPods: int, namespace: str = "default", printOutput: bool = False) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
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
    if printOutput :
        print("Scaling Deployment '" + jupyterLabDeployment(workspaceName=workspaceName) + "' in namespace '" + namespace + "' to " + str(numPods) + " pod(s).")
    try :
        api = client.AppsV1Api()
        api.patch_namespaced_deployment(name=deploymentName, namespace=namespace, body=deployment)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

# Function for waiting until JupyterLab workspace deployment is in ready state
def waitForJupyterLabDeploymentReady(workspaceName: str, namespace: str = "default", printOutput: bool = False) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Wait for deployment to be ready
    if printOutput :
        print("Waiting for Deployment '" + jupyterLabDeployment(workspaceName=workspaceName) + "' to reach Ready state.")
    while True :
        try :
            api = client.AppsV1Api()
            deploymentStatus = api.read_namespaced_deployment_status(namespace=namespace, name=jupyterLabDeployment(workspaceName=workspaceName))
        except ApiException as err :
            if printOutput :
                print("Error: Kubernetes API Error: ", err)
            raise APIConnectionError(err)
        if deploymentStatus.status.ready_replicas == 1 :
            break
        sleep(5)

# Function for retrieving container image for JupyterLab workspace deployment
def retrieveImageForJupyterLabDeployment(workspaceName: str, namespace: str = "default", printOutput: bool = False) -> str :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve image
    try :
        api = client.AppsV1Api()
        deployment = api.read_namespaced_deployment(namespace=namespace, name=jupyterLabDeployment(workspaceName=workspaceName))
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)
    
    return deployment.spec.template.spec.containers[0].image


## Function for creating a new JupyterLab workspace
def createJupyterLab(workspaceName: str, workspaceSize: str, storageClass: str = None, namespace: str = "default", workspacePassword: str = None, workspaceImage: str = "jupyter/tensorflow-notebook", requestCpu: str = None, requestMemory: str = None, requestNvidiaGpu: str = None, printOutput: bool = False, pvcAlreadyExists: bool = False, labels: dict = None) -> str :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Set labels
    if not labels :
        labels = jupyterLabLabels(workspaceName=workspaceName)

    # Step 0 - Set password
    if not workspacePassword :
        while True :
            workspacePassword = getpass("Set workspace password (this password will be required in order to access the workspace): ")
            if getpass("Re-enter password: ") == workspacePassword :
                break
            else :
                print("Error: Passwords do not match. Try again.")
    hashedPassword = IPython.lib.passwd(workspacePassword)

    # Step 1 - Create PVC for workspace
    if not pvcAlreadyExists :
        if printOutput :
            print("\nCreating persistent volume for workspace...")
        try :
            createVolume(pvcName=jupyterLabWorkspacePVCName(workspaceName=workspaceName), volumeSize=workspaceSize, storageClass=storageClass, namespace=namespace, pvcLabels=labels, printOutput=printOutput)
        except :
            if printOutput :
                print("Aborting workspace creation...")
            raise

    # Step 2 - Create service for workspace

    # Construct service
    service = client.V1Service(
        metadata = client.V1ObjectMeta(
            name = jupyterLabService(workspaceName=workspaceName),
            labels = labels
        ),
        spec = client.V1ServiceSpec(
            type = "NodePort",
            selector = {
                "app": labels["app"]
            },
            ports = [
                client.V1ServicePort(
                    name = "http",
                    port = 8888,
                    target_port = 8888,
                    protocol = "TCP"
                )
            ]
        )
    )

    # Create service
    if printOutput :
        print("\nCreating Service '" + jupyterLabService(workspaceName=workspaceName) + "' in namespace '" + namespace + "'.")
    try :
        api = client.CoreV1Api()
        api.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
            print("Aborting workspace creation...")
        raise APIConnectionError(err)

    if printOutput :
        print("Service successfully created.")

    # Step 3 - Create deployment

    # Construct deployment
    deployment = client.V1Deployment(
        metadata = client.V1ObjectMeta(
            name = jupyterLabDeployment(workspaceName=workspaceName),
            labels = labels
        ),
        spec = client.V1DeploymentSpec(
            replicas = 1,
            selector = {
                "matchLabels": {
                    "app": labels["app"]
                }
            },
            template = client.V1PodTemplateSpec(
                metadata = V1ObjectMeta(
                    labels = labels
                ),
                spec = client.V1PodSpec(
                    volumes = [
                        client.V1Volume(
                            name = "workspace",
                            persistent_volume_claim = {
                                "claimName": jupyterLabWorkspacePVCName(workspaceName=workspaceName)
                            }
                        )
                    ],
                    containers = [
                        client.V1Container(
                            name = "jupyterlab",
                            image = workspaceImage,
                            env = [
                                client.V1EnvVar(
                                    name = "JUPYTER_ENABLE_LAB",
                                    value = "yes"
                                ),
                                client.V1EnvVar(
                                    name = "RESTARTABLE",
                                    value = "yes"
                                ),
                                client.V1EnvVar(
                                    name = "CHOWN_HOME",
                                    value = "yes"
                                )
                            ],
                            security_context = client.V1PodSecurityContext(
                                run_as_user = 0
                            ),
                            args = ["start-notebook.sh", "--LabApp.password="+hashedPassword, "--LabApp.ip='0.0.0.0'", "--no-browser"],
                            ports = [
                                client.V1ContainerPort(container_port=8888)
                            ],
                            volume_mounts = [
                                client.V1VolumeMount(
                                    name = "workspace",
                                    mount_path = "/home/jovyan"
                                )
                            ],
                            resources = {
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
    if requestCpu :
        deployment.spec.template.spec.containers[0].resources["requests"]["cpu"] = requestCpu
    if requestMemory :
        deployment.spec.template.spec.containers[0].resources["requests"]["memory"] = requestMemory
    if requestNvidiaGpu :
        deployment.spec.template.spec.containers[0].resources["requests"]["nvidia.com/gpu"] = requestNvidiaGpu
        deployment.spec.template.spec.containers[0].resources["limits"]["nvidia.com/gpu"] = requestNvidiaGpu

    # Create deployment
    if printOutput :
        print("\nCreating Deployment '" + jupyterLabDeployment(workspaceName=workspaceName) + "' in namespace '" + namespace + "'.")
    try :
        api = client.AppsV1Api()
        api.create_namespaced_deployment(namespace=namespace, body=deployment)
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
            print("Aborting workspace creation...")
        raise APIConnectionError(err)

    # Wait for deployment to be ready
    if printOutput :
        print("Deployment '" + jupyterLabDeployment(workspaceName=workspaceName) + "' created.")
    waitForJupyterLabDeploymentReady(workspaceName=workspaceName, namespace=namespace, printOutput=printOutput)

    if printOutput :
        print("Deployment successfully created.")

    # Step 4 - Retrieve access URL
    try :
        url = retrieveJupyterLabURL(workspaceName=workspaceName, namespace=namespace, printOutput=printOutput)
    except APIConnectionError as err :
        if printOutput :
            print("Aborting workspace creation...")
        raise

    if printOutput :
        print("\nWorkspace successfully created.")
        print("To access workspace, navigate to "+url)

    return url


# Function for deleting a JupyterLab workspace
def deleteJupyterLab(workspaceName: str, namespace: str = "default", preserveSnapshots: bool = False, printOutput: bool = False) :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Delete workspace
    if printOutput :
        print("Deleting workspace '" + workspaceName + "' in namespace '" + namespace + "'.")
    try :
        # Delete deployment
        if printOutput :
            print ("Deleting Deployment...")
        api = client.AppsV1Api()
        api.delete_namespaced_deployment(namespace=namespace, name=jupyterLabDeployment(workspaceName=workspaceName))

        # Delete service
        if printOutput :
            print ("Deleting Service...")
        api = client.CoreV1Api()
        api.delete_namespaced_service(namespace=namespace, name=jupyterLabService(workspaceName=workspaceName))

    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Delete PVC
    if printOutput :
        print ("Deleting PVC...")
    deleteVolume(pvcName=jupyterLabWorkspacePVCName(workspaceName=workspaceName), namespace=namespace, preserveSnapshots=preserveSnapshots, printOutput=printOutput)

    if printOutput :
        print("Workspace successfully deleted.")


## Function for listing all JupyterLab workspaces
def listJupyterLabs(namespace: str = "default", printOutput: bool = False) -> list :
    # Retrieve kubeconfig
    try :
        loadKubeConfig()
    except :
        if printOutput :
            printInvalidConfigError()
        raise InvalidConfigError()

    # Retrieve list of workspaces
    try :
        api = client.AppsV1Api()
        deployments = api.list_namespaced_deployment(namespace=namespace, label_selector=jupyterLabLabelSelector())
    except ApiException as err :
        if printOutput :
            print("Error: Kubernetes API Error: ", err)
        raise APIConnectionError(err)

    # Construct list of workspaces
    workspacesList = list()
    for deployment in deployments.items :
        # Construct dict containing workspace details
        workspaceDict = dict()

        # Retrieve workspace name
        workspaceName = deployment.metadata.labels["jupyterlab-workspace-name"]
        workspaceDict["Workspace Name"] = workspaceName

        # Determine readiness status
        if deployment.status.ready_replicas == 1 :
            workspaceDict["Status"] = "Ready"
        else :
            workspaceDict["Status"] = "Not Ready"

        # Retrieve PVC size and StorageClass
        try :
            api = client.CoreV1Api()
            pvc = api.read_namespaced_persistent_volume_claim(namespace=namespace, name=jupyterLabWorkspacePVCName(workspaceName=workspaceName))
            workspaceDict["Size"] = pvc.status.capacity["storage"]
            workspaceDict["StorageClass"] = pvc.spec.storage_class_name
        except :
            workspaceDict["Size"] = ""
            workspaceDict["StorageClass"] = ""

        # Retrieve access URL
        workspaceDict["Access URL"] = retrieveJupyterLabURL(workspaceName=workspaceName, namespace=namespace, printOutput=printOutput)
        
        # Retrieve clone details
        try :
            if deployment.metadata.labels["created-by-operation"] == "clone-jupyterlab" :
                workspaceDict["Clone"] = "Yes"
                workspaceDict["Source Workspace"] = pvc.metadata.labels["source-jupyterlab-workspace"]
                try :
                    api = client.AppsV1Api()
                    deployments = api.read_namespaced_deployment(namespace=namespace, name=jupyterLabDeployment(workspaceName=workspaceDict["Source Workspace"]))
                except :
                    workspaceDict["Source Workspace"] = "*deleted*"
                try :
                    workspaceDict["Source VolumeSnapshot"] = pvc.spec.data_source.name
                    try :
                        api = client.CustomObjectsApi()
                        api.get_namespaced_custom_object(group=snapshotApiGroup(), version=snapshotApiVersion(), namespace=namespace, plural="volumesnapshots", name=workspaceDict["Source VolumeSnapshot"])   # Confirm that VolumeSnapshot still exists
                    except :
                        workspaceDict["Source VolumeSnapshot"] = "*deleted*"
                except :
                    workspaceDict["Source VolumeSnapshot"] = "n/a"
            else :
                workspaceDict["Clone"] = "No"
                workspaceDict["Source Workspace"] = ""
                workspaceDict["Source VolumeSnapshot"] = ""
        except :
            workspaceDict["Clone"] = "No"
            workspaceDict["Source Workspace"] = ""
            workspaceDict["Source VolumeSnapshot"] = ""

        # Append dict to list of workspaces
        workspacesList.append(workspaceDict)

    # Print list of workspaces
    if printOutput :
        # Convert workspaces array to Pandas DataFrame
        workspacesDF = pd.DataFrame.from_dict(workspacesList, dtype="string")
        print(tabulate(workspacesDF, showindex=False, headers=workspacesDF.columns))

    return workspacesList


## Function for creating a JupyterLab snapshot
def createJupyterLabSnapshot(workspaceName: str, snapshotName: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", printOutput: bool = False) :
    # Create snapshot
    if printOutput :
        print("Creating VolumeSnapshot for JupyterLab workspace '" + workspaceName + "' in namespace '" + namespace + "'...")
    createVolumeSnapshot(pvcName=jupyterLabWorkspacePVCName(workspaceName=workspaceName), snapshotName=snapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=printOutput)


## Function for listing all JupyterLab snapshots
def listJupyterLabSnapshots(workspaceName: str = None, namespace: str = "default", printOutput: bool = False) :
    # Determine PVC name
    if workspaceName :
        pvcName = jupyterLabWorkspacePVCName(workspaceName=workspaceName)
    else :
        pvcName = None

    # List snapshots
    return listVolumeSnapshots(pvcName=pvcName, namespace=namespace, printOutput=printOutput, jupyterLabWorkspacesOnly=True)


## Function for restoring a JupyterLab snapshot
def restoreJupyterLabSnapshot(snapshotName: str = None, namespace: str = "default", printOutput: bool = False) :
    # Retrieve source PVC name
    sourcePvcName = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=snapshotName, namespace=namespace, printOutput=printOutput)[0]

    # Retrieve workspace name
    workspaceName = retrieveJupyterLabWorkspaceForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)

    # Set labels
    labels = jupyterLabLabels(workspaceName=workspaceName)
    labels["created-by-operation"] = "restore-jupyterlab-snapshot"

    if printOutput :
        print("Restoring VolumeSnapshot '" + snapshotName + "' for JupyterLab workspace '" + workspaceName + "' in namespace '" + namespace + "'...")

    # Scale deployment to 0 pods
    scaleJupyterLabDeployment(workspaceName=workspaceName, numPods=0, namespace=namespace, printOutput=printOutput)
    sleep(5)

    # Restore snapshot
    restoreVolumeSnapshot(snapshotName=snapshotName, namespace=namespace, printOutput=printOutput, pvcLabels=labels)

    # Scale deployment to 1 pod
    scaleJupyterLabDeployment(workspaceName=workspaceName, numPods=1, namespace=namespace, printOutput=printOutput)

    # Wait for deployment to reach ready state
    waitForJupyterLabDeploymentReady(workspaceName=workspaceName, namespace=namespace, printOutput=printOutput)

    if printOutput :
        print("JupyterLab workspace snapshot successfully restored.")


## Function for cloning a JupyterLab workspace
def cloneJupyterLab(newWorkspaceName: str, sourceWorkspaceName: str, sourceSnapshotName: str = None, newWorkspacePassword: str = None, volumeSnapshotClass: str = "csi-snapclass", namespace: str = "default", requestCpu: str = None, requestMemory: str = None, requestNvidiaGpu: str = None, printOutput: bool = False) :
    # Determine source PVC details
    if sourceSnapshotName :
        sourcePvcName, workspaceSize = retrieveSourceVolumeDetailsForVolumeSnapshot(snapshotName=sourceSnapshotName, namespace=namespace, printOutput=printOutput)
        if printOutput :
            print("Creating new JupyterLab workspace '" + newWorkspaceName + "' from VolumeSnapshot '" + sourceSnapshotName + "' in namespace '" + namespace + "'...\n")
    else :
        sourcePvcName = jupyterLabWorkspacePVCName(workspaceName=sourceWorkspaceName)
        workspaceSize = retrieveSizeForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)
        if printOutput :
            print("Creating new JupyterLab workspace '" + newWorkspaceName + "' from source workspace '" + sourceWorkspaceName + "' in namespace '" + namespace + "'...\n")

    # Determine source workspace details
    if not sourceWorkspaceName :
        sourceWorkspaceName = retrieveJupyterLabWorkspaceForPvc(pvcName=sourcePvcName, namespace=namespace, printOutput=printOutput)
    sourceWorkspaceImage = retrieveImageForJupyterLabDeployment(workspaceName=sourceWorkspaceName, namespace=namespace, printOutput=printOutput)

    # Set labels
    labels = jupyterLabLabels(workspaceName=newWorkspaceName)
    labels["created-by-operation"] = "clone-jupyterlab"
    labels["source-jupyterlab-workspace"] = sourceWorkspaceName
    labels["source-pvc"] = sourcePvcName

    # Clone workspace PVC
    cloneVolume(newPvcName=jupyterLabWorkspacePVCName(workspaceName=newWorkspaceName), sourcePvcName=sourcePvcName, sourceSnapshotName=sourceSnapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=printOutput, pvcLabels=labels)

    # Remove source PVC from labels
    del labels["source-pvc"]

    # Create new workspace
    print()
    createJupyterLab(workspaceName=newWorkspaceName, workspaceSize=workspaceSize, namespace=namespace, workspacePassword=newWorkspacePassword, workspaceImage=sourceWorkspaceImage, requestCpu=requestCpu, requestMemory=requestMemory, requestNvidiaGpu=requestNvidiaGpu, printOutput=printOutput, pvcAlreadyExists=True, labels=labels)

    if printOutput :
        print("JupyterLab workspace successfully cloned.")
    

## Define contents of help text
helpTextStandard = '''
The NetApp Data Science Toolkit for Kubernetes is a Python library that makes it simple for data scientists and data engineers to perform various data management tasks, such as provisioning a new data volume, near-instantaneously cloning a data volume, and near-instantaneously snapshotting a data volume for traceability/baselining.

Basic Commands:

\thelp\t\t\t\tPrint help text.
\tversion\t\t\t\tPrint version details.

JupyterLab Management Commands:
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tclone jupyterlab\t\tCreate a new JupyterLab workspace that is an exact copy of an existing workspace.
\tcreate jupyterlab\t\tProvision a JupyterLab workspace.
\tdelete jupyterlab\t\tDelete an existing JupyterLab workspace.
\tlist jupyterlabs\t\tList all JupyterLab workspaces.
\tcreate jupyterlab-snapshot\tCreate a new snapshot for a JupyterLab workspace.
\tlist jupyterlab-snapshots\tList all snapshots.
\trestore jupyterlab-snapshot\tRestore a snapshot.

Kubernetes Persistent Volume Management Commands (for advanced Kubernetes users):
Note: To view details regarding options/arguments for a specific command, run the command with the '-h' or '--help' option.

\tclone volume\t\t\tCreate a new persistent volume that is an exact copy of an existing persistent volume.
\tcreate volume\t\t\tProvision a new persistent volume.
\tdelete volume\t\t\tDelete an existing persistent volume.
\tlist volumes\t\t\tList all persistent volumes.
\tcreate volume-snapshot\t\tCreate a new snapshot for a persistent volume.
\tdelete volume-snapshot\t\tDelete an existing snapshot.
\tlist volume-snapshots\t\tList all snapshots.
\trestore volume-snapshot\t\tRestore a snapshot.
'''
helpTextCloneJupyterLab = '''
Command: clone jupyterlab

Create a new JupyterLab workspace that is an exact copy of an existing workspace.

Note: Either -s/--source-snapshot-name or -j/--source-workspace-name must be specified. However, only one of these flags (not both) should be specified for a given operation. If -j/--source-workspace-name is specified, then the clone will be created from the current state of the workspace. If -s/--source-snapshot-name is specified, then the clone will be created from a specific snapshot related the source workspace.

Required Options/Arguments:
\t-w, --new-workspace-name=\tName of new workspace (name to be applied to new JupyterLab workspace).

Optional Options/Arguments:
\t-c, --volume-snapshot-class=\tKubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
\t-g, --nvidia-gpu=\t\tNumber of NVIDIA GPUs to allocate to new JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
\t-h, --help\t\t\tPrint help text.
\t-j, --source-workspace-name=\tName of JupyterLab workspace to use as source for clone. Either -s/--source-snapshot-name or -j/--source-workspace-name must be specified.
\t-m, --memory=\t\t\tAmount of memory to reserve for new JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
\t-n, --namespace=\t\tKubernetes namespace that source workspace is located in. If not specified, namespace "default" will be used.
\t-p, --cpu=\t\t\tNumber of CPUs to reserve for new JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
\t-s, --source-snapshot-name=\tName of Kubernetes VolumeSnapshot to use as source for clone. Either -s/--source-snapshot-name or -j/--source-workspace-name must be specified.

Examples:
\t./ntap_dsutil.py clone jupyterlab --new-workspace-name=project1-experiment1 --source-workspace-name=project1 --nvidia-gpu=1
\t./ntap_dsutil.py clone jupyterlab -w project2-mike -s project2-snap1 -n team1 -g 1 -p 0.5 -m 1Gi
'''
helpTextCloneVolume = '''
Command: clone volume

Create a new persistent volume that is an exact copy of an existing persistent volume.

Note: Either -s/--source-snapshot-name or -v/--source-pvc-name must be specified. However, only one of these flags (not both) should be specified for a given operation. If -v/--source-pvc-name is specified, then the clone will be created from the current state of the volume. If -s/--source-snapshot-name is specified, then the clone will be created from a specific snapshot related the source volume.

Required Options/Arguments:
\t-p, --new-pvc-name=\t\tName of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC).

Optional Options/Arguments:
\t-c, --volume-snapshot-class=\tKubernetes VolumeSnapshotClass to use when creating clone. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
\t-h, --help\t\t\tPrint help text.
\t-n, --namespace=\t\tKubernetes namespace that source PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
\t-s, --source-snapshot-name=\tName of Kubernetes VolumeSnapshot to use as source for clone. Either -s/--source-snapshot-name or -v/--source-pvc-name must be specified.
\t-v, --source-pvc-name=\t\tName of Kubernetes PersistentVolumeClaim (PVC) to use as source for clone. Either -s/--source-snapshot-name or -v/--source-pvc-name must be specified.

Examples:
\t./ntap_dsutil.py clone volume --new-pvc-name=project1-experiment1 --source-pvc-name=project1
\t./ntap_dsutil.py clone volume -p project2-mike -s snap1 -n team1
'''
helpTextCreateJupyterLab = '''
Command: create jupyterlab

Provision a JupyterLab workspace.

Required Options/Arguments:
\t-w, --workspace-name=\tName of new JupyterLab workspace.
\t-s, --size=\t\tSize new workspace (i.e. size of backing persistent volume to be created). Format: '1024Mi', '100Gi', '10Ti', etc.

Optional Options/Arguments:
\t-c, --storage-class=\tKubernetes StorageClass to use when provisioning backing volume for new workspace. If not specified, the default StorageClass will be used. Note: The StorageClass must be configured to use Trident or the BeeGFS CSI driver.
\t-g, --nvidia-gpu=\tNumber of NVIDIA GPUs to allocate to JupyterLab workspace. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
\t-h, --help\t\tPrint help text.
\t-i, --image=\t\tContainer image to use when creating workspace. If not specified, "jupyter/tensorflow-notebook" will be used.
\t-m, --memory=\t\tAmount of memory to reserve for JupyterLab workspace. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
\t-n, --namespace=\tKubernetes namespace to create new workspace in. If not specified, workspace will be created in namespace "default".
\t-p, --cpu=\t\tNumber of CPUs to reserve for JupyterLab workspace. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.

Examples:
\t./ntap_dsutil_k8s.py create jupyterlab --workspace-name=mike --size=10Gi --nvidia-gpu=2
\t./ntap_dsutil_k8s.py create jupyterlab -n dst-test -w dave -i jupyter/scipy-notebook:latest -s 2Ti -c ontap-flexgroup -g 1 -p 0.5 -m 1Gi
'''
helpTextCreateJupyterLabSnapshot = '''
Command: create jupyterlab-snapshot

Create a new snapshot for a JupyterLab workspace.

Required Options/Arguments:
\t-w, --workspace-name=\t\tName of JupyterLab workspace.

Optional Options/Arguments:
\t-c, --volume-snapshot-class=\tKubernetes VolumeSnapshotClass to use when creating snapshot of backing volume for workspace. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
\t-h, --help\t\t\tPrint help text.
\t-n, --namespace=\t\tKubernetes namespace that workspace is located in. If not specified, namespace "default" will be used.
\t-s, --snapshot-name=\t\tName of new Kubernetes VolumeSnapshot for workspace. If not specified, will be set to 'ntap-dsutil.<timestamp>'.

Examples:
\t./ntap_dsutil.py create jupyterlab-snapshot --workspace-name=mike
\t./ntap_dsutil.py create jupyterlab-snapshot -w sathish -s snap1 -c ontap -n team1
'''
helpTextCreateVolumeSnapshot = '''
Command: create volume-snapshot

Create a new snapshot for a persistent volume.

Required Options/Arguments:
\t-p, --pvc-name=\t\t\tName of Kubernetes PersistentVolumeClaim (PVC) to create snapshot for.

Optional Options/Arguments:
\t-c, --volume-snapshot-class=\tKubernetes VolumeSnapshotClass to use when creating snapshot. If not specified, "csi-snapclass" will be used. Note: VolumeSnapshotClass must be configured to use Trident.
\t-h, --help\t\t\tPrint help text.
\t-n, --namespace=\t\tKubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
\t-s, --snapshot-name=\t\tName of new Kubernetes VolumeSnapshot. If not specified, will be set to 'ntap-dsutil.<timestamp>'.

Examples:
\t./ntap_dsutil.py create volume-snapshot --pvc-name=project1
\t./ntap_dsutil.py create volume-snapshot -p project2 -s snap1 -c ontap -n team1
'''
helpTextCreateVolume = '''
Command: create volume

Provision a new persistent volume.

Required Options/Arguments:
\t-p, --pvc-name=\t\tName of new volume (name to be applied to new Kubernetes PersistentVolumeClaim/PVC).
\t-s, --size=\t\tSize of new volume. Format: '1024Mi', '100Gi', '10Ti', etc.

Optional Options/Arguments:
\t-c, --storage-class=\tKubernetes StorageClass to use when provisioning new volume. If not specified, default StorageClass will be used. Note: The StorageClass must be configured to use Trident or the BeeGFS CSI driver.
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace to create new PersistentVolumeClaim (PVC) in. If not specified, PVC will be created in namespace "default".

Examples:
\t./ntap_dsutil.py create volume --pvc-name=project1 --size=10Gi
\t./ntap_dsutil.py create volume -p datasets -s 10Ti -n team1
\t./ntap_dsutil.py create volume --pvc-name=project2 --size=2Ti --namespace=team2 --storage-class=ontap-flexgroup
'''
helpTextDeleteJupyterLab = '''
Command: delete jupyterlab

Delete an existing JupyterLab workspace.

Required Options/Arguments:
\t-w, --workspace-name=\t\tName of JupyterLab workspace to be deleted.

Optional Options/Arguments:
\t-f, --force\t\t\tDo not prompt user to confirm operation.
\t-h, --help\t\t\tPrint help text.
\t-n, --namespace=\t\tKubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
\t-s, --preserve-snapshots\tDo not delete VolumeSnapshots associated with workspace.

Examples:
\t./ntap_dsutil.py delete jupyterlab --workspace-name=mike
\t./ntap_dsutil.py delete jupyterlab -w dave -n dst-test
'''
helpTextDeleteJupyterLabSnapshot = '''
Command: delete jupyterlab-snapshot

Delete an existing JupyterLab workspace snapshot.

Required Options/Arguments:
\t-s, --snapshot-name=\tName of Kubernetes VolumeSnapshot to be deleted.

Optional Options/Arguments:
\t-f, --force\t\tDo not prompt user to confirm operation.
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.

Examples:
\t./ntap_dsutil.py delete jupyterlab-snapshot --snapshot-name=snap1
\t./ntap_dsutil.py delete jupyterlab-snapshot -s ntap-dsutil.20210304151544 -n team1
'''
helpTextDeleteVolumeSnapshot = '''
Command: delete volume-snapshot

Delete an existing snapshot.

Required Options/Arguments:
\t-s, --snapshot-name=\tName of Kubernetes VolumeSnapshot to be deleted.

Optional Options/Arguments:
\t-f, --force\t\tDo not prompt user to confirm operation.
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.

Examples:
\t./ntap_dsutil.py delete volume-snapshot --snapshot-name=snap1
\t./ntap_dsutil.py delete volume-snapshot -s ntap-dsutil.20210304151544 -n team1
'''
helpTextDeleteVolume = '''
Command: delete volume

Delete an existing persistent volume.

Required Options/Arguments:
\t-p, --pvc-name=\t\t\tName of Kubernetes PersistentVolumeClaim (PVC) to be deleted.

Optional Options/Arguments:
\t-f, --force\t\t\tDo not prompt user to confirm operation.
\t-h, --help\t\t\tPrint help text.
\t-n, --namespace=\t\tKubernetes namespace that PersistentVolumeClaim (PVC) is located in. If not specified, namespace "default" will be used.
\t-s, --preserve-snapshots\tDo not delete VolumeSnapshots associated with PersistentVolumeClaim (PVC).

Examples:
\t./ntap_dsutil.py delete volume --pvc-name=project1
\t./ntap_dsutil.py delete volume -p project2 -n team1
'''
helpTextListJupyterLabs= '''
Command: list jupyterlabs

List all JupyterLab workspaces in a specific namespace.

No options/arguments are required.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace for which to retrieve list of workspaces. If not specified, namespace "default" will be used.

Examples:
\t./ntap_dsutil.py list jupyterlabs -n team1
\t./ntap_dsutil.py list jupyterlabs --namespace=team2
'''
helpTextListJupyterLabSnapshots = '''
Command: list jupyterlab-snapshots

List all JupyterLab workspace snapshots in a specific namespace.

No options/arguments are required.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
\t-w, --workspace-name=\tName of JupyterLab workspace to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.

Examples:
\t./ntap_dsutil.py list jupyterlab-snapshots --workspace-name=mike
\t./ntap_dsutil.py list jupyterlab-snapshots -n team2
'''
helpTextListVolumeSnapshots = '''
Command: list volume-snapshots

List all persistent volume snapshots in a specific namespace.

No options/arguments are required.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace that Kubernetes VolumeSnapshot is located in. If not specified, namespace "default" will be used.
\t-p, --pvc-name=\t\tName of Kubernetes PersistentVolumeClaim (PVC) to list snapshots for. If not specified, all VolumeSnapshots in namespace will be listed.

Examples:
\t./ntap_dsutil.py list volume-snapshots --pvc-name=project1
\t./ntap_dsutil.py list volume-snapshots -n team2
'''
helpTextListVolumes = '''
Command: list volumes

List all persistent volumes in a specific namespace.

No options/arguments are required.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace for which to retrieve list of volumes. If not specified, namespace "default" will be used.

Examples:
\t./ntap_dsutil.py list volumes -n team1
\t./ntap_dsutil.py list volumes --namespace=team2
'''
helpTextRestoreJupyterLabSnapshot = '''
Command: restore jupyterlab-snapshot

Restore a snapshot for a JupyterLab workspace.

Required Options/Arguments:
\t-s, --snapshot-name=\tName of Kubernetes VolumeSnapshot to be restored.

Optional Options/Arguments:
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.

Examples:
\t./ntap_dsutil.py restore jupyterlab-snapshot --snapshot-name=mike-snap1
\t./ntap_dsutil.py restore jupyterlab-snapshot -s ntap-dsutil.20210304151544 -n team1
'''
helpTextRestoreVolumeSnapshot = '''
Command: restore volume-snapshot

Restore a snapshot for a persistent volume.

Warning: In order to restore a snapshot, the PersistentVolumeClaim (PVC) associated the snapshot must NOT be mounted to any pods.
Tip: If the PVC associated with the snapshot is currently mounted to a pod that is managed by a deployment, you can scale the deployment to 0 pods using the command `kubectl scale --replicas=0 deployment/<deployment_name>`. After scaling the deployment to 0 pods, you will be able to restore the snapshot. After restoring the snapshot, you can use the `kubectl scale` command to scale the deployment back to the desired number of pods.

Required Options/Arguments:
\t-s, --snapshot-name=\tName of Kubernetes VolumeSnapshot to be restored.

Optional Options/Arguments:
\t-f, --force\t\tDo not prompt user to confirm operation.
\t-h, --help\t\tPrint help text.
\t-n, --namespace=\tKubernetes namespace that VolumeSnapshot is located in. If not specified, namespace "default" will be used.

Examples:
\t./ntap_dsutil.py restore volume-snapshot --snapshot-name=snap1
\t./ntap_dsutil.py restore volume-snapshot -s ntap-dsutil.20210304151544 -n team1
'''


## Function for handling situation in which user enters invalid command
def handleInvalidCommand(helpText: str = helpTextStandard, invalidOptArg: bool = False) :
    if invalidOptArg :
        print("Error: Invalid option/argument.")
    else :
        print("Error: Invalid command.")
    print(helpText)
    sys.exit(1)


## Function for getting desired target from command line args
def getTarget(args: list) -> str:
    try :
        target = args[2]
    except :
        handleInvalidCommand()
    return target


## Main function
if __name__ == '__main__' :
    import sys, getopt

    # Get desired action from command line args
    try :
        action = sys.argv[1]
    except :
        handleInvalidCommand()

    # Invoke desired action
    if action == "clone" :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("volume", "vol", "pvc", "persistentvolumeclaim") :
            newPvcName = None
            sourcePvcName = None
            sourceSnapshotName = None
            volumeSnapshotClass = "csi-snapclass"
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hp:c:n:s:v:", ["help", "new-pvc-name=", "volume-snapshot-class=", "namespace=", "source-snapshot-name=", "source-pvc-name="])
            except :
                handleInvalidCommand(helpText=helpTextCloneVolume, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCloneVolume)
                    sys.exit(0)
                elif opt in ("-p", "--new-pvc-name") :
                    newPvcName = arg
                elif opt in ("-c", "--volume-snapshot-class") :
                    volumeSnapshotClass = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-s", "--source-snapshot-name") :
                    sourceSnapshotName = arg
                elif opt in ("-v", "--source-pvc-name") :
                    sourcePvcName = arg
            
            # Check for required options
            if not newPvcName or (not sourceSnapshotName and not sourcePvcName) :
                handleInvalidCommand(helpText=helpTextCloneVolume, invalidOptArg=True)
            if sourceSnapshotName and sourcePvcName :
                print("Error: Both -s/--source-snapshot-name and -v/--source-pvc-name cannot be specified for the same operation.")
                handleInvalidCommand(helpText=helpTextCloneVolume, invalidOptArg=True)

            # Clone volume
            try :
                cloneVolume(newPvcName=newPvcName, sourcePvcName=sourcePvcName, sourceSnapshotName=sourceSnapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("jupyterlab", "jupyter") :
            newWorkspaceName = None
            sourceWorkspaceName = None
            sourceSnapshotName = None
            volumeSnapshotClass = "csi-snapclass"
            namespace = "default"
            requestNvidiaGpu = None
            requestMemory = None
            requestCpu = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hw:c:n:s:j:g:m:p:", ["help", "new-workspace-name=", "volume-snapshot-class=", "namespace=", "source-snapshot-name=", "source-workspace-name=", "nvidia-gpu=", "memory=", "cpu="])
            except :
                handleInvalidCommand(helpText=helpTextCloneJupyterLab, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCloneJupyterLab)
                    sys.exit(0)
                elif opt in ("-w", "--new-workspace-name") :
                    newWorkspaceName = arg
                elif opt in ("-c", "--volume-snapshot-class") :
                    volumeSnapshotClass = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-s", "--source-snapshot-name") :
                    sourceSnapshotName = arg
                elif opt in ("-j", "--source-workspace-name") :
                    sourceWorkspaceName = arg
                elif opt in ("-g", "--nvidia-gpu") :
                    requestNvidiaGpu = arg
                elif opt in ("-m", "--memory") :
                    requestMemory = arg
                elif opt in ("-p", "--cpu") :
                    requestCpu = arg
            
            # Check for required options
            if not newWorkspaceName or (not sourceSnapshotName and not sourceWorkspaceName) :
                handleInvalidCommand(helpText=helpTextCloneJupyterLab, invalidOptArg=True)
            if sourceSnapshotName and sourceWorkspaceName :
                print("Error: Both -s/--source-snapshot-name and -j/--source-workspace-name cannot be specified for the same operation.")
                handleInvalidCommand(helpText=helpTextCloneJupyterLab, invalidOptArg=True)

            # Clone volume
            try :
                cloneJupyterLab(newWorkspaceName=newWorkspaceName, sourceWorkspaceName=sourceWorkspaceName, sourceSnapshotName=sourceSnapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, requestCpu=requestCpu, requestMemory=requestMemory, requestNvidiaGpu=requestNvidiaGpu, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action == "create" :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("volume-snapshot", "volumesnapshot") :
            pvcName = None
            snapshotName = None
            volumeSnapshotClass = "csi-snapclass"
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hp:c:n:s:", ["help", "pvc-name=", "volume-snapshot-class=", "namespace=", "snapshot-name="])
            except :
                handleInvalidCommand(helpText=helpTextCreateVolumeSnapshot, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCreateVolumeSnapshot)
                    sys.exit(0)
                elif opt in ("-p", "--pvc-name") :
                    pvcName = arg
                elif opt in ("-c", "--volume-snapshot-class") :
                    volumeSnapshotClass = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-s", "--snapshot-name") :
                    snapshotName = arg
            
            # Check for required options
            if not pvcName  :
                handleInvalidCommand(helpText=helpTextCreateVolumeSnapshot, invalidOptArg=True)

            # Create snapshot
            try :
                createVolumeSnapshot(pvcName=pvcName, snapshotName=snapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("volume", "vol", "pvc", "persistentvolumeclaim") :
            pvcName = None
            volumeSize = None
            namespace = "default"
            storageClass = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hp:s:n:c:", ["help", "pvc-name=", "size=", "namespace=", "storage-class="])
            except :
                handleInvalidCommand(helpText=helpTextCreateVolume, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCreateVolume)
                    sys.exit(0)
                elif opt in ("-p", "--pvc-name") :
                    pvcName = arg
                elif opt in ("-s", "--size") :
                    volumeSize = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-c", "--storage-class") :
                    storageClass = arg
            
            # Check for required options
            if not pvcName or not volumeSize :
                handleInvalidCommand(helpText=helpTextCreateVolume, invalidOptArg=True)

            # Create volume
            try :
                createVolume(pvcName=pvcName, volumeSize=volumeSize, storageClass=storageClass, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("jupyterlab", "jupyter") :
            workspaceName = None
            workspaceSize = None
            namespace = "default"
            storageClass = None
            workspaceImage = "jupyter/scipy-notebook:latest"
            requestNvidiaGpu = None
            requestMemory = None
            requestCpu = None

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hw:s:n:c:i:g:m:p:", ["help", "workspace-name=", "size=", "namespace=", "storage-class=", "image=", "nvidia-gpu=", "memory=", "cpu="])
            except :
                handleInvalidCommand(helpText=helpTextCreateJupyterLab, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCreateJupyterLab)
                    sys.exit(0)
                elif opt in ("-w", "--workspace-name") :
                    workspaceName = arg
                elif opt in ("-s", "--size") :
                    workspaceSize = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-c", "--storage-class") :
                    storageClass = arg
                elif opt in ("-i", "--image") :
                    workspaceImage = arg
                elif opt in ("-g", "--nvidia-gpu") :
                    requestNvidiaGpu = arg
                elif opt in ("-m", "--memory") :
                    requestMemory = arg
                elif opt in ("-p", "--cpu") :
                    requestCpu = arg
            
            # Check for required options
            if not workspaceName or not workspaceSize :
                handleInvalidCommand(helpText=helpTextCreateJupyterLab, invalidOptArg=True)

            # Create JupyterLab workspace
            try :
                createJupyterLab(workspaceName=workspaceName, workspaceSize=workspaceSize, storageClass=storageClass, namespace=namespace, workspaceImage=workspaceImage, requestCpu=requestCpu, requestMemory=requestMemory, requestNvidiaGpu=requestNvidiaGpu, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("jupyterlab-snapshot", "jupyterlabsnapshot", "jupyter-snapshot", "jupytersnapshot") :
            workspaceName = None
            snapshotName = None
            volumeSnapshotClass = "csi-snapclass"
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hw:c:n:s:", ["help", "workspace-name=", "volume-snapshot-class=", "namespace=", "snapshot-name="])
            except :
                handleInvalidCommand(helpText=helpTextCreateJupyterLabSnapshot, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextCreateJupyterLabSnapshot)
                    sys.exit(0)
                elif opt in ("-w", "--workspace-name") :
                    workspaceName = arg
                elif opt in ("-c", "--volume-snapshot-class") :
                    volumeSnapshotClass = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-s", "--snapshot-name") :
                    snapshotName = arg
            
            # Check for required options
            if not workspaceName  :
                handleInvalidCommand(helpText=helpTextCreateJupyterLabSnapshot, invalidOptArg=True)

            # Create snapshot
            try :
                createJupyterLabSnapshot(workspaceName=workspaceName, snapshotName=snapshotName, volumeSnapshotClass=volumeSnapshotClass, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("delete", "del", "rm") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("volume-snapshot", "volumesnapshot", "jupyterlab-snapshot", "jupyterlabsnapshot") :
            helpText = helpTextDeleteVolumeSnapshot
            if target in ("jupyterlab-snapshot", "jupyterlabsnapshot") :
                helpText = helpTextDeleteJupyterLabSnapshot

            snapshotName = None
            namespace = "default"
            force = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hs:fn:", ["help", "snapshot-name=", "force", "namespace="])
            except :
                handleInvalidCommand(helpText=helpText, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpText)
                    sys.exit(0)
                elif opt in ("-s", "--snapshot-name") :
                    snapshotName = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-f", "--force") :
                    force = True
            
            # Check for required options
            if not snapshotName :
                handleInvalidCommand(helpText=helpText, invalidOptArg=True)

            # Confirm delete operation
            if not force :
                print("Warning: This snapshot will be permanently deleted.")
                while True :
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES") :
                        break
                    elif proceed in ("no", "No", "NO") :
                        sys.exit(0)
                    else :
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Delete snapshot
            try :
                deleteVolumeSnapshot(snapshotName=snapshotName, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)
        
        elif target in ("volume", "vol", "pvc", "persistentvolumeclaim") :
            pvcName = None
            namespace = "default"
            force = False
            preserveSnapshots = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hp:fn:s", ["help", "pvc-name=", "force", "namespace=", "preserve-snapshots"])
            except :
                handleInvalidCommand(helpText=helpTextDeleteVolume, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextDeleteVolume)
                    sys.exit(0)
                elif opt in ("-p", "--pvc-name") :
                    pvcName = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-f", "--force") :
                    force = True
                elif opt in ("-s", "--preserve-snapshots") :
                    preserveSnapshots = True
            
            # Check for required options
            if not pvcName :
                handleInvalidCommand(helpText=helpTextDeleteVolume, invalidOptArg=True)

            # Confirm delete operation
            if not force :
                print("Warning: All data associated with the volume will be permanently deleted.")
                while True :
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES") :
                        break
                    elif proceed in ("no", "No", "NO") :
                        sys.exit(0)
                    else :
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Delete volume
            try :
                deleteVolume(pvcName=pvcName, namespace=namespace, preserveSnapshots=preserveSnapshots, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("jupyterlab", "jupyter") :
            workspaceName = None
            namespace = "default"
            force = False
            preserveSnapshots = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hw:fn:s", ["help", "workspace-name=", "force", "namespace=", "preserve-snapshots"])
            except :
                handleInvalidCommand(helpText=helpTextDeleteJupyterLab, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextDeleteJupyterLab)
                    sys.exit(0)
                elif opt in ("-w", "--workspace-name") :
                    workspaceName = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-f", "--force") :
                    force = True
                elif opt in ("-s", "--preserve-snapshots") :
                    preserveSnapshots = True
            
            # Check for required options
            if not workspaceName :
                handleInvalidCommand(helpText=helpTextDeleteJupyterLab, invalidOptArg=True)

            # Confirm delete operation
            if not force :
                print("Warning: All data associated with the workspace will be permanently deleted.")
                while True :
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES") :
                        break
                    elif proceed in ("no", "No", "NO") :
                        sys.exit(0)
                    else :
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Delete JupyterLab workspace
            try :
                deleteJupyterLab(workspaceName=workspaceName, namespace=namespace, preserveSnapshots=preserveSnapshots, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("help", "h", "-h", "--help") :
        print(helpTextStandard)
        
    elif action in ("list", "ls") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("volume-snapshots", "volume-snapshot", "volumesnapshots", "volumesnapshot") :
            pvcName = None
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hp:n:", ["help", "pvc-name=", "namespace="])
            except :
                handleInvalidCommand(helpText=helpTextListVolumeSnapshots, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextListVolumeSnapshots)
                    sys.exit(0)
                elif opt in ("-p", "--pvc-name") :
                    pvcName = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
            
            # List volumes
            try :
                listVolumeSnapshots(pvcName=pvcName, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("volume", "vol", "volumes", "vols", "pvc", "persistentvolumeclaim", "pvcs", "persistentvolumeclaims") :
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:", ["help", "namespace="])
            except :
                handleInvalidCommand(helpText=helpTextListVolumes, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextListVolumes)
                    sys.exit(0)
                elif opt in ("-n", "--namespace") :
                    namespace = arg
            
            # List volumes
            try :
                listVolumes(namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("jupyterlab-snapshots", "jupyterlab-snapshot", "jupyterlabsnapshots", "jupyterlabsnapshot") :
            workspaceName = None
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hw:n:", ["help", "workspace-name=", "namespace="])
            except :
                handleInvalidCommand(helpText=helpTextListJupyterLabSnapshots, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextListJupyterLabSnapshots)
                    sys.exit(0)
                elif opt in ("-w", "--workspace-name") :
                    workspaceName = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
            
            # List JupyterLab snapshots
            try :
                listJupyterLabSnapshots(workspaceName=workspaceName, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("jupyterlabs", "jupyters", "jupyterlab", "jupyter") :
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hn:", ["help", "namespace="])
            except :
                handleInvalidCommand(helpText=helpTextListJupyterLabs, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextListJupyterLabs)
                    sys.exit(0)
                elif opt in ("-n", "--namespace") :
                    namespace = arg
            
            # List JupyterLab workspaces
            try :
                listJupyterLabs(namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("restore") :
        # Get desired target from command line args
        target = getTarget(sys.argv)
        
        # Invoke desired action based on target
        if target in ("volume-snapshot", "volumesnapshot") :
            snapshotName = None
            namespace = "default"
            force = False

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hs:fn:", ["help", "snapshot-name=", "force", "namespace="])
            except :
                handleInvalidCommand(helpText=helpTextRestoreVolumeSnapshot, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextRestoreVolumeSnapshot)
                    sys.exit(0)
                elif opt in ("-s", "--snapshot-name") :
                    snapshotName = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
                elif opt in ("-f", "--force") :
                    force = True
            
            # Check for required options
            if not snapshotName :
                handleInvalidCommand(helpText=helpTextRestoreVolumeSnapshot, invalidOptArg=True)

            # Confirm restore operation
            if not force :
                print("Warning: In order to restore a snapshot, the PersistentVolumeClaim (PVC) associated the snapshot must NOT be mounted to any pods.")
                while True :
                    proceed = input("Are you sure that you want to proceed? (yes/no): ")
                    if proceed in ("yes", "Yes", "YES") :
                        break
                    elif proceed in ("no", "No", "NO") :
                        sys.exit(0)
                    else :
                        print("Invalid value. Must enter 'yes' or 'no'.")

            # Restore snapshot
            try :
                restoreVolumeSnapshot(snapshotName=snapshotName, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        elif target in ("jupyterlab-snapshot", "jupyterlabsnapshot") :
            snapshotName = None
            namespace = "default"

            # Get command line options
            try :
                opts, args = getopt.getopt(sys.argv[3:], "hs:n:", ["help", "snapshot-name=", "namespace="])
            except :
                handleInvalidCommand(helpText=helpTextRestoreJupyterLabSnapshot, invalidOptArg=True)

            # Parse command line options
            for opt, arg in opts :
                if opt in ("-h", "--help") :
                    print(helpTextRestoreJupyterLabSnapshot)
                    sys.exit(0)
                elif opt in ("-s", "--snapshot-name") :
                    snapshotName = arg
                elif opt in ("-n", "--namespace") :
                    namespace = arg
            
            # Check for required options
            if not snapshotName :
                handleInvalidCommand(helpText=helpTextRestoreJupyterLabSnapshot, invalidOptArg=True)

            # Restore snapshot
            try :
                restoreJupyterLabSnapshot(snapshotName=snapshotName, namespace=namespace, printOutput=True)
            except (InvalidConfigError, APIConnectionError) :
                sys.exit(1)

        else :
            handleInvalidCommand()

    elif action in ("version", "v", "-v", "--version") :
        print("NetApp Data Science Toolkit for Kubernetes - version " + version)
        
    else :
        handleInvalidCommand()