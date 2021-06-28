# Airflow DAG Definition: AI Training Run
#
# Steps:
#   1. Data prep job
#   2. Dataset snapshot (for traceability)
#   3. Training job
#   4. Model snapshot (for versioning/baselining)
#   5. Inference validation job


from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from kubernetes.client import models as k8s
import uuid


##### DEFINE PARAMETERS: Modify parameter values in this section to match your environment #####

## Define default args for DAG
ai_training_run_dag_default_args = {
    'owner': 'NetApp'
}

## Define DAG details
ai_training_run_dag = DAG(
    dag_id='ai_training_run',
    default_args=ai_training_run_dag_default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['training']
)

# Define Kubernetes namespace to execute DAG in
namespace = 'airflow'

## Define volume details (change values as necessary to match your environment)

# Dataset volume
dataset_volume_pvc_existing = 'dataset-vol'
dataset_volume = k8s.V1Volume(
    name=dataset_volume_pvc_existing,
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name=dataset_volume_pvc_existing),
)
dataset_volume_mount = k8s.V1VolumeMount(
    name=dataset_volume_pvc_existing, 
    mount_path='/mnt/dataset', 
    sub_path=None, 
    read_only=False
)

# Model volume
model_volume_pvc_existing = 'airflow-model-vol'
model_volume = k8s.V1Volume(
    name=model_volume_pvc_existing,
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name=model_volume_pvc_existing),
)
model_volume_mount = k8s.V1VolumeMount(
    name=model_volume_pvc_existing, 
    mount_path='/mnt/model', 
    sub_path=None, 
    read_only=False
)

## Define job details (change values as needed)

# Data prep step
data_prep_step_container_image = "nvcr.io/nvidia/tensorflow:21.03-tf1-py3"
data_prep_step_command = ["echo", "'No data prep command entered'"] # Replace this echo command with the data prep command that you wish to execute
data_prep_step_resources = {} # Hint: To request that 1 GPU be allocated to job pod, change to: {'limit_gpu': 1}

# Training step
train_step_container_image = "nvcr.io/nvidia/tensorflow:21.03-tf1-py3"
train_step_command = ["echo", "'No training command entered'"] # Replace this echo command with the training command that you wish to execute
train_step_resources = {} # Hint: To request that 1 GPU be allocated to job pod, change to: {'limit_gpu': 1}

# Inference validation step
validate_step_container_image = "nvcr.io/nvidia/tensorflow:21.03-tf1-py3"
validate_step_command = ["echo", "'No inference validation command entered'"] # Replace this echo command with the inference validation command that you wish to execute
validate_step_resources = {} # Hint: To request that 1 GPU be allocated to job pod, change to: {'limit_gpu': 1}

################################################################################################


# Define DAG steps/workflow
with ai_training_run_dag as dag :

    # Define step to generate uuid for run
    generate_uuid = PythonOperator(
        task_id='generate-uuid',
        python_callable=lambda: str(uuid.uuid4())
    )

    # Define data prep step using Kubernetes Pod operator (https://airflow.apache.org/docs/stable/kubernetes.html#kubernetespodoperator)
    data_prep = KubernetesPodOperator(
        namespace=namespace,
        image=data_prep_step_container_image,
        cmds=data_prep_step_command,
        resources = data_prep_step_resources,
        volumes=[dataset_volume, model_volume],
        volume_mounts=[dataset_volume_mount, model_volume_mount],
        name="ai-training-run-data-prep",
        task_id="data-prep",
        is_delete_operator_pod=True,
        hostnetwork=False
    )

    # Define step to take a snapshot of the dataset volume for traceability
    dataset_snapshot = KubernetesPodOperator(
        namespace=namespace,
        image="python:3",
        cmds=["/bin/bash", "-c"],
        arguments=["\
            python3 -m pip install netapp-dataops-k8s && \
            netapp_dataops_k8s_cli.py create volume-snapshot --pvc-name=" + str(dataset_volume_pvc_existing) + " --snapshot-name=dataset-{{ task_instance.xcom_pull(task_ids='generate-uuid', dag_id='ai_training_run', key='return_value') }} --namespace=" + namespace],
        name="ai-training-run-dataset-snapshot",
        task_id="dataset-snapshot",
        is_delete_operator_pod=True,
        hostnetwork=False
    )

    # State that the dataset snapshot should be created after the data prep job completes and the uuid job completes
    data_prep >> dataset_snapshot
    generate_uuid >> dataset_snapshot

    # Define training step using Kubernetes Pod operator (https://airflow.apache.org/docs/stable/kubernetes.html#kubernetespodoperator)
    train = KubernetesPodOperator(
        namespace=namespace,
        image=train_step_container_image,
        cmds=train_step_command,
        resources = train_step_resources,
        volumes=[dataset_volume, model_volume],
        volume_mounts=[dataset_volume_mount, model_volume_mount],
        name="ai-training-run-train",
        task_id="train",
        is_delete_operator_pod=True,
        hostnetwork=False
    )

    # State that training job should be executed after dataset volume snapshot is taken
    dataset_snapshot >> train

    # Define step to take a snapshot of the model volume for versioning/baselining
    model_snapshot = KubernetesPodOperator(
        namespace=namespace,
        image="python:3",
        cmds=["/bin/bash", "-c"],
        arguments=["\
            python3 -m pip install netapp-dataops-k8s && \
            netapp_dataops_k8s_cli.py create volume-snapshot --pvc-name=" + str(model_volume_pvc_existing) + " --snapshot-name=model-{{ task_instance.xcom_pull(task_ids='generate-uuid', dag_id='ai_training_run', key='return_value') }} --namespace=" + namespace],
        name="ai-training-run-model-snapshot",
        task_id="model-snapshot",
        is_delete_operator_pod=True,
        hostnetwork=False
    )

    # State that the model snapshot should be created after the training job completes
    train >> model_snapshot

    # Define inference validation step using Kubernetes Pod operator (https://airflow.apache.org/docs/stable/kubernetes.html#kubernetespodoperator)
    validate = KubernetesPodOperator(
        namespace=namespace,
        image=validate_step_container_image,
        cmds=validate_step_command,
        resources = validate_step_resources,
        volumes=[dataset_volume, model_volume],
        volume_mounts=[dataset_volume_mount, model_volume_mount],
        name="ai-training-run-validate",
        task_id="validate",
        is_delete_operator_pod=True,
        hostnetwork=False
    )

    # State that inference validation job should be executed after model volume snapshot is taken
    model_snapshot >> validate
