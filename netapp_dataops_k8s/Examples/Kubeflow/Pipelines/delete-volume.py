# Kubeflow Pipeline Definition: Delete Volume

import kfp.compiler as compiler
import kfp.dsl as dsl

# Define Kubeflow pipeline
@dsl.pipeline(
    name="Delete volume",
    description="Template for deleting a volume in Kubernetes"
)
def delete_volume(
    # Define variables that the user can set in the pipelines UI; set default values
    pvc_name: str = "datavol"
) :
    # Pipeline Steps:

    # Delete Volume
    delete_volume = dsl.ContainerOp(
        name="delete-volume",
        image="python:3.11",
        command=["/bin/bash", "-c"],
        arguments=["\
            python3 -m pip install netapp-dataops-k8s && \
            echo '" + str(pvc_name) + "' > /deleted_pvc_name.txt && \
            netapp_dataops_k8s_cli.py delete volume --pvc-name=" + str(pvc_name) + " --namespace={{workflow.namespace}} --force"],
        file_outputs={"deleted_pvc_name": "/deleted_pvc_name.txt"}
    )

if __name__ == '__main__' :
    compiler.Compiler().compile(delete_volume, __file__ + '.yaml')
