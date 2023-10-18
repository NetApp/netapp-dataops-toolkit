# Kubeflow Pipeline Definition: Delete Snapshot

import kfp.compiler as compiler
import kfp.dsl as dsl

# Define Kubeflow pipeline
@dsl.pipeline(
    name="Delete Snapshot",
    description="Template for deleting a snapshot in Kubernetes"
)
def delete_volume(
    # Define variables that the user can set in the pipelines UI; set default values
    volume_snapshot_name: str = "snap1"
) :
    # Pipeline Steps:

    # Delete Snapshot
    delete_snapshot = dsl.ContainerOp(
        name="delete-snapshot",
        image="python:3.11",
        command=["/bin/bash", "-c"],
        arguments=["\
            python3 -m pip install netapp-dataops-k8s && \
            echo '" + str(volume_snapshot_name) + "' > /deleted_volume_snapshot_name.txt && \
            netapp_dataops_k8s_cli.py delete volume-snapshot --snapshot-name=" + str(volume_snapshot_name) + " --namespace={{workflow.namespace}} --force"],
        file_outputs={"deleted_volume_snapshot_name": "/deleted_volume_snapshot_name.txt"}
    )

if __name__ == '__main__' :
    compiler.Compiler().compile(delete_volume, __file__ + '.yaml')
