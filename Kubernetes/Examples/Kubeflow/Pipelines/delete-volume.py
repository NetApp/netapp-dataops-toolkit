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
        image="python:3",
        command=["/bin/bash", "-c"],
        arguments=["\
            python3 -m pip install ipython kubernetes pandas tabulate && \
            git clone https://github.com/NetApp/netapp-data-science-toolkit && \
            mv /netapp-data-science-toolkit/Kubernetes/ntap_dsutil_k8s.py / && \
            echo '" + str(pvc_name) + "' > /deleted_pvc_name.txt && \
            /ntap_dsutil_k8s.py delete volume --pvc-name=" + str(pvc_name) + " --namespace={{workflow.namespace}} --force"],
        file_outputs={"deleted_pvc_name": "/deleted_pvc_name.txt"}
    )

if __name__ == '__main__' :
    compiler.Compiler().compile(delete_volume, __file__ + '.yaml')
