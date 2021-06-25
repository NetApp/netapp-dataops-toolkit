# Kubeflow Pipeline Definition: Trigger a Sync Operation for an Existing Cloud Sync Relationship

import kfp.dsl as dsl
import kfp.components as comp
import kubernetes.client as k8s_client

## Function for triggering an update for a specific Cloud Sync relationship
def netappCloudSyncUpdate(relationshipId: str, printResponse: bool = True, keepCheckingUntilComplete: bool = True) :
    import sys, subprocess, json, os, base64

    # Install pre-requisites
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'netapp-ontap', 'pandas', 'tabulate', 'requests', 'boto3', 'pyyaml'])
    subprocess.run(['git', 'clone', 'https://github.com/NetApp/netapp-data-science-toolkit'])
    subprocess.run(['cp', '-a', '/netapp-data-science-toolkit/Traditional/ntap_dsutil.py', '/tmp/'])
    from ntap_dsutil import syncCloudSyncRelationship

    # Retrieve Cloud Sync refresh token from mounted k8s secret
    with open('/mnt/secret/refreshToken', 'r') as refreshTokenSecret :
        refreshTokenString = refreshTokenSecret.read().strip()

    # Create NetApp Data Science Toolkit config file
    refreshTokenBytes = refreshTokenString.encode("ascii") 
    refreshTokenBase64Bytes = base64.b64encode(refreshTokenBytes)
    configJson = {"cloudCentralRefreshToken": refreshTokenBase64Bytes.decode("ascii")}
    configDirPath = os.path.expanduser("~/.ntap_dsutil")
    os.mkdir(configDirPath)
    configFilePath = os.path.join(configDirPath, "config.json")
    with open(configFilePath, 'w') as configFile :
        json.dump(configJson, configFile)
    
    # Trigger sync operation
    syncCloudSyncRelationship(relationshipID=relationshipId, waitUntilComplete=keepCheckingUntilComplete, printOutput=printResponse)

# Convert netappCloudSyncUpdate function to Kubeflow Pipeline ContainerOp named 'NetappCloudSyncUpdateOp'
NetappCloudSyncUpdateOp = comp.func_to_container_op(netappCloudSyncUpdate, base_image='python:3')


# Define Kubeflow Pipeline
@dsl.pipeline(
    name="Replicate Data - Cloud Sync",
    description="Template for triggering a sync operation for an existing NetApp Cloud Sync relationship"
)
def replicate_data_cloud_sync(
    # Define variables that the user can set in the pipelines UI; set default values
    cloud_sync_relationship_id: str,
    cloud_sync_refresh_token_k8s_secret: str = "cloud-sync-refresh-token"
) :
    # Pipeline Steps:

    # Trigger Cloud Sync update
    replicate = NetappCloudSyncUpdateOp(
        cloud_sync_relationship_id
    )
    # Mount k8s secret containing Cloud Sync refresh token
    replicate.add_pvolumes({
        '/mnt/secret': k8s_client.V1Volume(
            name='cloud-sync-refresh-token',
            secret=k8s_client.V1SecretVolumeSource(
                secret_name=cloud_sync_refresh_token_k8s_secret
            )
        )
    })

if __name__ == '__main__' :
    import kfp.compiler as compiler
    compiler.Compiler().compile(replicate_data_cloud_sync, __file__ + '.yaml')