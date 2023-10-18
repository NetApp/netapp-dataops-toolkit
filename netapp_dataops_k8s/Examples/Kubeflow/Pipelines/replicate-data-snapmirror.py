# Kubeflow Pipeline Definition: Replicate data - SnapMirror

import kfp.dsl as dsl
import kfp.components as comp
from kubernetes import client as k8s_client


# Define function that triggers a NetApp SnapMirror update
def netappSnapMirrorUpdate(
    destinationOntapClusterOrSvmMgmtHostname: str, 
    destinationSvm: str,
    uuid: str,
    verifySSLCert: str = 'no',
    waitUntilComplete: bool = True,

) :
    import sys, subprocess, json, os, base64

    # Install pre-requisites
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'netapp-dataops-traditional'])
    from netapp_dataops.traditional import syncSnapMirrorRelationship
    
    # Retrieve ONTAP admin account details from mounted K8s secrets
    with open('/mnt/secret/username', 'r') as usernameSecret :
        ontapAdminUsername = usernameSecret.read().strip()
    with open('/mnt/secret/password', 'r') as passwordSecret :
        ontapAdminPasswordString = passwordSecret.read().strip()
    
    # Create NetApp Data Science Toolkit config file
    if verifySSLCert == "no" : 
        verifySSLCertBool = False
    else : 
        verifySSLCertBool = True

    ontapAdminPasswordBytes = ontapAdminPasswordString.encode("ascii") 
    ontapAdminPasswordBase64Bytes = base64.b64encode(ontapAdminPasswordBytes)

    configJson = {
        "connectionType": "ONTAP", 
        "hostname": destinationOntapClusterOrSvmMgmtHostname, 
        "svm": destinationSvm, 
        "username": ontapAdminUsername, 
        "password": ontapAdminPasswordBase64Bytes.decode("ascii"),
        "verifySSLCert": verifySSLCertBool
    }

    configDirPath = os.path.expanduser("~/.netapp_dataops")
    os.mkdir(configDirPath)
    configFilePath = os.path.join(configDirPath, "config.json")
    with open(configFilePath, 'w') as configFile :
        json.dump(configJson, configFile)
    
    # Trigger sync operation
    syncSnapMirrorRelationship(uuid=uuid, waitUntilComplete=waitUntilComplete, printOutput=True)

# Convert netappSnapMirrorUpdate function to Kubeflow Pipeline ContainerOp named 'NetappSnapMirrorUpdateOp'
NetappSnapMirrorUpdateOp = comp.func_to_container_op(netappSnapMirrorUpdate, base_image='python:3.11')


# Define Kubeflow Pipeline
@dsl.pipeline(
    name="Replicate Data - SnapMirror",
    description="Template for triggering a a sync operation for an existing SnapMirror relationshop"
)
def replicate_data_snapmirror(
    # Define variables that the user can set in the pipelines UI; set default values
    snapmirror_relationship_uuid: str,
    destination_ontap_cluster_or_svm_mgmt_hostname: str = "10.61.188.118", 
    destination_ontap_cluster_or_svm_admin_acct_k8s_secret: str = "ontap-admin-account",
    destination_svm: str = "svm0",
    ontap_api_verify_ssl_cert__yes_or_no: str = "yes"
) :
    # Pipeline Steps:

    # Trigger SnapMirror replication
    replicate = NetappSnapMirrorUpdateOp(
        destination_ontap_cluster_or_svm_mgmt_hostname, 
        destination_svm,
        snapmirror_relationship_uuid,
        ontap_api_verify_ssl_cert__yes_or_no
    )
    # Mount k8s secret containing ONTAP cluster admin account details
    replicate.add_pvolumes({
        '/mnt/secret': k8s_client.V1Volume(
            name='ontap-cluster-admin',
            secret=k8s_client.V1SecretVolumeSource(
                secret_name=destination_ontap_cluster_or_svm_admin_acct_k8s_secret
            )
        )
    })

if __name__ == '__main__' :
    import kfp.compiler as compiler
    compiler.Compiler().compile(replicate_data_snapmirror, __file__ + '.yaml')
