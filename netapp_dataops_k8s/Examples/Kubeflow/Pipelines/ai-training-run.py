# Kubeflow Pipeline Definition: AI Training Run

import kfp.dsl as dsl
import kfp.onprem as onprem

# Define Kubeflow Pipeline
@dsl.pipeline(
    # Define pipeline metadata
    name="AI Training Run",
    description="Template for executing an AI training run with built-in training dataset traceability and trained model versioning"
)
def ai_training_run(
    # Define variables that the user can set in the pipelines UI; set default values
    dataset_volume_pvc_existing: str = "dataset-vol",
    trained_model_volume_pvc_existing: str = "kfp-model-vol",
    execute_data_prep_step__yes_or_no: str = "yes",
    data_prep_step_container_image: str = "nvcr.io/nvidia/tensorflow:21.03-tf1-py3",
    data_prep_step_command: str = "<insert command here>",
    data_prep_step_dataset_volume_mountpoint: str = "/mnt/dataset",
    train_step_container_image: str = "nvcr.io/nvidia/tensorflow:21.03-tf1-py3",
    train_step_command: str = "<insert command here>",
    train_step_dataset_volume_mountpoint: str = "/mnt/dataset",
    train_step_model_volume_mountpoint: str = "/mnt/model",
    validation_step_container_image: str = "nvcr.io/nvidia/tensorflow:21.03-tf1-py3",
    validation_step_command: str = "<insert command here>",
    validation_step_dataset_volume_mountpoint: str = "/mnt/dataset",
    validation_step_model_volume_mountpoint: str = "/mnt/model"
) :
    # Set GPU limits; Due to SDK limitations, this must be hardcoded
    train_step_num_gpu = 0
    validation_step_num_gpu = 0

    # Pipeline Steps:

    # Execute data prep step
    with dsl.Condition(execute_data_prep_step__yes_or_no == "yes") :
        data_prep = dsl.ContainerOp(
            name="data-prep",
            image=data_prep_step_container_image,
            command=["sh", "-c"],
            arguments=[data_prep_step_command]
        )
        # Mount dataset volume/pvc
        data_prep.apply(
            onprem.mount_pvc(dataset_volume_pvc_existing, 'dataset', data_prep_step_dataset_volume_mountpoint)
        )

    # Create a snapshot of the dataset volume/pvc for traceability
    volume_snapshot_name = "dataset-{{workflow.uid}}"
    dataset_snapshot = dsl.ContainerOp(
        name="dataset-snapshot",
        image="python:3.11",
        command=["/bin/bash", "-c"],
        arguments=["\
            python3 -m pip install netapp-dataops-k8s && \
            echo '" + volume_snapshot_name + "' > /volume_snapshot_name.txt && \
            netapp_dataops_k8s_cli.py create volume-snapshot --pvc-name=" + str(dataset_volume_pvc_existing) + " --snapshot-name=" + str(volume_snapshot_name) + " --namespace={{workflow.namespace}}"],
        file_outputs={"volume_snapshot_name": "/volume_snapshot_name.txt"}
    )
    # State that snapshot should be created after the data prep job completes
    dataset_snapshot.after(data_prep)

    # Execute training step
    train = dsl.ContainerOp(
        name="train-model",
        image=train_step_container_image,
        command=["sh", "-c"],
        arguments=[train_step_command]
    )
    # Mount dataset volume/pvc
    train.apply(
        onprem.mount_pvc(dataset_volume_pvc_existing, 'datavol', train_step_dataset_volume_mountpoint)
    )
    # Mount model volume/pvc
    train.apply(
        onprem.mount_pvc(trained_model_volume_pvc_existing, 'modelvol', train_step_model_volume_mountpoint)
    )
    # Request that GPUs be allocated to training job pod
    if train_step_num_gpu > 0 :
        train.set_gpu_limit(train_step_num_gpu, 'nvidia')
    # State that training job should be executed after dataset volume snapshot is taken
    train.after(dataset_snapshot)

    # Create a snapshot of the model volume/pvc for model versioning
    volume_snapshot_name = "kfp-model-{{workflow.uid}}"
    model_snapshot = dsl.ContainerOp(
        name="model-snapshot",
        image="python:3.11",
        command=["/bin/bash", "-c"],
        arguments=["\
            python3 -m pip install netapp-dataops-k8s && \
            echo '" + volume_snapshot_name + "' > /volume_snapshot_name.txt && \
            netapp_dataops_k8s_cli.py create volume-snapshot --pvc-name=" + str(trained_model_volume_pvc_existing) + " --snapshot-name=" + str(volume_snapshot_name) + " --namespace={{workflow.namespace}}"],
        file_outputs={"volume_snapshot_name": "/volume_snapshot_name.txt"}
    )
    # State that snapshot should be created after the training job completes
    model_snapshot.after(train)

    # Execute inference validation job
    inference_validation = dsl.ContainerOp(
        name="validate-model",
        image=validation_step_container_image,
        command=["sh", "-c"],
        arguments=[validation_step_command]
    )
    # Mount dataset volume/pvc
    inference_validation.apply(
        onprem.mount_pvc(dataset_volume_pvc_existing, 'datavol', validation_step_dataset_volume_mountpoint)
    )
    # Mount model volume/pvc
    inference_validation.apply(
        onprem.mount_pvc(trained_model_volume_pvc_existing, 'modelvol', validation_step_model_volume_mountpoint)
    )
    # Request that GPUs be allocated to pod
    if validation_step_num_gpu > 0 :
        inference_validation.set_gpu_limit(validation_step_num_gpu, 'nvidia')
    # State that inference validation job should be executed after model volume snapshot is taken
    inference_validation.after(model_snapshot)

if __name__ == "__main__" :
    import kfp.compiler as compiler
    compiler.Compiler().compile(ai_training_run, __file__ + ".yaml")
