# Airflow DAG Definition: Replicate Data - Cloud Sync
#
# Steps:
#   1. Trigger a sync operation for an existing NetApp Cloud Sync relationship


from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago


##### DEFINE PARAMETERS: Modify parameter values in this section to match your environment #####

## Define default args for DAG
replicate_data_cloud_sync_dag_default_args = {
    'owner': 'NetApp'
}

## Define DAG details
replicate_data_cloud_sync_dag = DAG(
    dag_id='replicate_data_cloud_sync',
    default_args=replicate_data_cloud_sync_dag_default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['data-movement']
)

## Define Cloud Sync details (change values as necessary to match your environment)

# Cloud Sync refresh token details
airflowConnectionName = 'cloud_sync'  # Name of the Airflow connection that contains your Cloud Sync refresh token

# Cloud Sync relationship details (existing Cloud Sync relationship for which you want to trigger an update)
relationshipId = '5fe2a6c597a18907ade906a4'

################################################################################################


## Function for triggering an update for a specific Cloud Sync relationship
def netappCloudSyncUpdate(**kwargs) :
    import sys, subprocess, json, os, base64
    from airflow.hooks.base_hook import BaseHook

    # Install pre-requisites
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'netapp-dataops-traditional'])
    from netapp_dataops.traditional import syncCloudSyncRelationship

    # Parse args
    printResponse = True # Default value
    keepCheckingUntilComplete = True # Default value
    for key, value in kwargs.items() :
        if key == 'relationshipId' :
            relationshipId = value
        elif key == 'printResponse' :
            printResponse = value
        elif key == 'keepCheckingUntilComplete' :
            keepCheckingUntilComplete = value
        elif key == 'airflowConnectionName' :
            airflowConnectionName = value

    # Retrieve Cloud Sync refresh token from Airflow connection
    cloudSyncConnection = BaseHook.get_connection(airflowConnectionName)    # Assumes that you only have one connection with the specified conn_id configured in Airflow
    refreshTokenString = cloudSyncConnection.password

    # Create NetApp Data Science Toolkit config file
    refreshTokenBytes = refreshTokenString.encode("ascii") 
    refreshTokenBase64Bytes = base64.b64encode(refreshTokenBytes)
    configJson = {"cloudCentralRefreshToken": refreshTokenBase64Bytes.decode("ascii")}
    configDirPath = os.path.expanduser("~/.netapp_dataops")
    try : 
        os.mkdir(configDirPath)
    except :
        pass
    configFilePath = os.path.join(configDirPath, "config.json")
    with open(configFilePath, 'w') as configFile :
        json.dump(configJson, configFile)
    
    # Trigger sync operation
    try :
        syncCloudSyncRelationship(relationshipID=relationshipId, waitUntilComplete=keepCheckingUntilComplete, printOutput=printResponse)
    except :
        # Delete toolkit config file
        os.remove(configFilePath)
        raise

    # Delete toolkit config file
    os.remove(configFilePath)


# Define DAG steps/workflow
with replicate_data_cloud_sync_dag as dag :

    # Define step to trigger a sync operation for an existing NetApp Cloud Sync relationship
    trigger_cloud_sync = PythonOperator(
        task_id='sync',
        python_callable=netappCloudSyncUpdate,
        op_kwargs={
            'airflowConnectionName': airflowConnectionName,
            'relationshipId': relationshipId
        },
        dag=dag
    )