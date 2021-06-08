# Airflow DAG Definition: Replicate Data - SnapMirror
#
# Steps:
#   1. Trigger a sync operation for an existing asynchronous NetApp SnapMirror relationship


from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago


##### DEFINE PARAMETERS: Modify parameter values in this section to match your environment #####

## Define default args for DAG
replicate_data_snapmirror_dag_default_args = {
    'owner': 'NetApp'
}

## Define DAG details
replicate_data_snapmirror_dag = DAG(
    dag_id='replicate_data_snapmirror',
    default_args=replicate_data_snapmirror_dag_default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['data-movement']
)

## Define SnapMirror details (change values as necessary to match your environment)

# Destination ONTAP system details
airflowConnectionName = 'ontap_ai'  # Name of the Airflow connection that contains connection details for the destination ONTAP system's cluster or SVM admin account
verifySSLCert = False   # Denotes whether or not to verify the SSL cert when calling the ONTAP API

# SnapMirror relationship details (existing SnapMirroer relationship for which you want to trigger an update)
snapMirrorRelationshipUuid = "1525e0b5-6b24-11eb-896a-00505693dfde"
destinationSvm = "ai221_data"

################################################################################################


# Define function that triggers a NetApp SnapMirror update
def netappSnapMirrorUpdate(**kwargs) -> int :
    import sys, subprocess, json, os, base64
    from airflow.hooks.base_hook import BaseHook

    # Install pre-requisites
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'netapp-ontap', 'pandas', 'tabulate', 'requests', 'boto3', 'pyyaml'])
    subprocess.run(['curl', '-o', '/home/airflow/.local/lib/python3.8/site-packages/ntap_dsutil.py', 'https://raw.githubusercontent.com/NetApp/netapp-data-science-toolkit/main/Traditional/ntap_dsutil.py'])
    from ntap_dsutil import syncSnapMirrorRelationship

    # Parse args
    printResponse = True # Default value
    keepCheckingUntilComplete = True # Default value
    for key, value in kwargs.items() :
        if key == 'destinationSvm' :
            destinationSvm = value
        elif key == 'snapMirrorRelationshipUuid' :
            snapMirrorRelationshipUuid = value
        elif key == 'verifySSLCert' :
            verifySSLCert = value
        elif key == 'airflowConnectionName' :
            airflowConnectionName = value
        elif key == 'printResponse' :
            printResponse = value
        elif key == 'keepCheckingUntilComplete' :
            keepCheckingUntilComplete = value

    # Retrieve Cloud Sync refresh token from Airflow connection
    ontapConnection = BaseHook.get_connection(airflowConnectionName)    # Assumes that you only have one connection with the specified conn_id configured in Airflow
    ontapAdminUsername = ontapConnection.login
    ontapAdminPasswordString = ontapConnection.password
    destinationOntapClusterOrSvmMgmtHostname = ontapConnection.host

    # Create NetApp Data Science Toolkit config file
    ontapAdminPasswordBytes = ontapAdminPasswordString.encode("ascii") 
    ontapAdminPasswordBase64Bytes = base64.b64encode(ontapAdminPasswordBytes)

    configJson = {
        "connectionType": "ONTAP", 
        "hostname": destinationOntapClusterOrSvmMgmtHostname, 
        "svm": destinationSvm, 
        "username": ontapAdminUsername, 
        "password": ontapAdminPasswordBase64Bytes.decode("ascii"),
        "verifySSLCert": verifySSLCert
    }

    configDirPath = os.path.expanduser("~/.ntap_dsutil")
    try : 
        os.mkdir(configDirPath)
    except :
        pass
    configFilePath = os.path.join(configDirPath, "config.json")
    with open(configFilePath, 'w') as configFile :
        json.dump(configJson, configFile)
    
    # Trigger sync operation
    try :
        syncSnapMirrorRelationship(uuid=snapMirrorRelationshipUuid, waitUntilComplete=keepCheckingUntilComplete, printOutput=printResponse)
    except :
        # Delete toolkit config file
        os.remove(configFilePath)
        raise

    # Delete toolkit config file
    os.remove(configFilePath)


# Define DAG steps/workflow
with replicate_data_snapmirror_dag as dag :

    # Define step to trigger a NetApp SnapMirror update
    trigger_snapmirror = PythonOperator(
        task_id='sync',
        python_callable=netappSnapMirrorUpdate,
        op_kwargs={
            'airflowConnectionName': airflowConnectionName,
            'verifySSLCert': verifySSLCert,
            'snapMirrorRelationshipUuid': snapMirrorRelationshipUuid,
            'destinationSvm': destinationSvm
        },
        dag=dag
    )