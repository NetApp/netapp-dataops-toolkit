# Airflow DAG Definition: Replicate Data - XCP
#
# Steps:
#   1. Invoke NetApp XCP copy or sync operation


from airflow.utils.dates import days_ago
from airflow.models import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator


##### DEFINE PARAMETERS: Modify parameter values in this section to match your environment #####

## Define default args for DAG
replicate_data_xcp_dag_default_args = {
    'owner': 'NetApp'
}

## Define DAG details
replicate_data_xcp_dag = DAG(
    dag_id='replicate_data_xcp',
    default_args=replicate_data_xcp_dag_default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['data-movement']
)

## Define xcp operation details (change values as necessary to match your environment and desired operation)

# Define xcp operation to perform
xcpOperation = 'sync' # Must be 'copy' or 'sync'

# Define source and destination for copy operation
xcpCopySource = '192.168.200.41:/trident_pvc_957318e1_9b73_4e16_b857_dca7819dd263'
xcpCopyDestination = '192.168.200.41:/trident_pvc_9e7607c2_29c8_4dbf_9b08_551ba72d0273'

# Define catalog id for sync operation
xcpSyncId = 'autoname_copy_2020-10-06_16.37.44.963391'

## Define xcp host details (change values as necessary to match your environment)
xcpAirflowConnectionName = 'xcp_host' # Name of the Airflow connection of type 'ssh' that contains connection details for a host on which xcp is installed, configured, and accessible within $PATH

################################################################################################


# Construct xcp command
xcpCommand = 'xcp help'
if xcpOperation == 'copy' :
    xcpCommand = 'xcp copy ' + xcpCopySource + ' ' + xcpCopyDestination
elif xcpOperation == 'sync' :
    xcpCommand = 'xcp sync -id ' + xcpSyncId


# Define DAG steps/workflow
with replicate_data_xcp_dag as dag :

    # Define step to invoke a NetApp XCP copy or sync operation
    invoke_xcp = SSHOperator(
        task_id="invoke-xcp",
        command=xcpCommand,
        ssh_conn_id=xcpAirflowConnectionName
    )