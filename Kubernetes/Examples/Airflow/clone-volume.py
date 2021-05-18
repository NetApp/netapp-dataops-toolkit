# Airflow DAG Definition: Clone Volume
#
# Steps:
#   1. Clone source volume


from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.utils.dates import days_ago


##### DEFINE PARAMETERS: Modify parameter values in this section to match your environment #####

## Define default args for DAG
clone_volume_dag_default_args = {
    'owner': 'NetApp'
}

## Define DAG details
clone_volume_dag = DAG(
    dag_id='clone_volume',
    default_args=clone_volume_dag_default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['vol-clone']
)

# Define Kubernetes namespace to execute DAG in (volume must be located in same namespace)
namespace = 'airflow'

## Define volume details (change values as necessary to match your environment)
source_volume_pvc_name = "gold-datavol"
new_volume_pvc_name = "datavol-clone-2"
clone_from_snapshot = True
source_volume_snapshot_name = "snap1"

################################################################################################


# Construct command args
arg = "\
    python3 -m pip install ipython kubernetes pandas tabulate && \
    git clone https://github.com/NetApp/netapp-data-science-toolkit && \
    mv /netapp-data-science-toolkit/Kubernetes/ntap_dsutil_k8s.py / && \
    /ntap_dsutil_k8s.py clone volume --namespace=" + str(namespace) + " --new-pvc-name=" + str(new_volume_pvc_name)
if clone_from_snapshot :
    arg += " --source-snapshot-name=" + str(source_volume_snapshot_name)
else :
    arg += " --source-pvc-name=" + str(source_volume_pvc_name)


# Define DAG steps/workflow
with clone_volume_dag as dag :

    # Define step to clone source volume
    clone_volume = KubernetesPodOperator(
        namespace=namespace,
        image="python:3",
        cmds=["/bin/bash", "-c"],
        arguments=[arg],
        name="clone-volume-clone-volume",
        task_id="clone-volume",
        is_delete_operator_pod=True,
        hostnetwork=False
    )