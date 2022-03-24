# NVIDIA triton server management with NetApp DataOps Toolkit for Kubernetes

The NetApp DataOps Toolkit for Kubernetes can be used to manage data science workspaces and inference servers within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new JupyterLab workspace, the ability to almost instantaneously clone a JupyterLab workspace, the ability to almost instantaneously save off a snapshot of a JupyterLab workspace for traceability/baselining, and the ability to provision a new NVIDIA Triton Inference Server. These workspace management capabilities are available within the toolkit's command line utility and as a set of functions that can be imported and used from other Python programs

<a name="command-line-functionality"></a>

## Command Line Functionality

You can perform the following operation(s) using the toolkit's command line utility

| Triton Inference Server operations                                                   | Supported by BeeGFS | Supported by Trident | Requires Astra Control |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- | ---------------------- |
| [Deploy a new NVIDIA Triton Inference Server.](#lib-create-triton-server)            | Yes                 | Yes                  | No                     |

### NVIDIA Triton Inference Server Management Operations

<a name="cli-create-triton-server"></a>

#### Deploy a new NVIDIA Triton Inference Server instance on demand

The NetApp DataOps Toolkit can enable a user to deploy an NVIDIA Triton Inference Server instance on-demand. The command for deploying an NVIDIA Triton Inference Server instance is `netapp_dataops_k8s_cli.py create triton-server`.

The following options/arguments are required:

```
    -s, --server-name=          Name of a new Triton Inference Server.
    -v, --model-repo-pvc-name=  Name of the PVC containing the model repository.
```

The following options/arguments are optional:

```
    -g, --nvidia-gpu=           Number of NVIDIA GPUs to allocate to the Triton instance. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    -h, --help                  Print help text.
    -i, --image=                Container image to use when creating Triton instance. If not specified, "nvcr.io/nvidia/tritonserver:21.11-py3" will be used.
    -m, --memory=               Amount of memory to reserve for Triton instance. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    -n, --namespace=            Kubernetes namespace to create new workspace in. If not specified, workspace will be created in namespace "default".
    -p, --cpu=                  Number of CPUs to reserve for Triton instance. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    -b, --load-balancer         Option to use a LoadBalancer instead of using NodePort service. If not specified, NodePort service will be utilized.
```

##### Example Usage

Deploy a new NVIDIA Triton Infernece Server instance and use LoadBalancer Service.

```sh
netapp_dataops_k8s_cli.py create triton-server --server-name=Test --model-repo-pvc-name=model-pvc --load-balancer
Creating Service 'ntap-dsutil-triton-sufian-lb1' in namespace 'default'.
Service successfully created.

Creating Deployment 'ntap-dsutil-triton-sufian-lb1' in namespace 'default'.
Deployment 'ntap-dsutil-triton-sufian-lb1' created.
Waiting for Deployment 'ntap-dsutil-triton-sufian-lb1' to reach Ready state.
Deployment successfully created.

Workspace successfully created.
Server endpoints:
http: 10.61.188.118:8000
grpc: 10.61.188.118:8001
metrics: 10.61.188.118:8002/metrics
```

<a name="library-of-functions"></a>

## Advanced: Set of Functions

The NetApp DataOps Toolkit for Kubernetes provides a set of functions that can be imported into any Python program or Jupyter Notebook. In this manner, data scientists and data engineers can easily incorporate Kubernetes-native data management tasks into their existing projects, programs, and workflows. This functionality is only recommended for advanced users who are proficient in Python.

```py
from netapp_dataops.k8s import create_triton_server
```

The following workspace management operations are available within the set of functions.

| Triton Inference Server operations                                                   | Supported by BeeGFS | Supported by Trident | Requires Astra Control |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- | ---------------------- |
| [Deploy a new NVIDIA Triton Inference Server.](#lib-create-triton-server)            | Yes                 | Yes                  | No                     |

### NVIDIA Triton Inference Server instance Management Operations

<a name="lib-create-triton-server"></a>

#### Deploy a new NVIDIA Triton Inference Server

The NetApp DataOps Toolkit can enable a user to deploy an NVIDIA Triton Inference Server instance on-demand.


##### Function Definition

```py
def create_triton_server(
    server_name: str,                                           # Name of the Triton Infernce Server Instance (required).
    model_pvc_name: str                                         # Name of the PVC containing the model repository.
    load_balancer_service: bool = False,                        # Option to use a LoadBalancer instead of using NodePort service. If not specified, NodePort service will be utilized.
    namespace: str = "default",                                 # Kubernetes namespace to create new workspace in. If not specified, workspace will be created in namespace "default".
    server_image: str = "nvcr.io/nvidia/tritonserver:21.11-py3" # Container image to use when creating instance. If not specified, "nvcr.io/nvidia/tritonserver:21.11-py3" will be used.
    request_cpu: str = None,                                    # Number of CPUs to reserve for Triton instance. Format: '0.5', '1', etc. If not specified, no CPUs will be reserved.
    request_memory: str = None,                                 # Amount of memory to reserve for Triton instance. Format: '1024Mi', '100Gi', '10Ti', etc. If not specified, no memory will be reserved.
    request_nvidia_gpu: str = None,                             # Number of NVIDIA GPUs to allocate to Triton instance. Format: '1', '4', etc. If not specified, no GPUs will be allocated.
    print_output: bool = False                                  # Denotes whether or not to print messages to the console during execution.
) -> str :
```

##### Return Value

This function will return server endpoints for the triton inference server.

Example of Return Values:

Server endpoints:
http: 10.61.188.118:8000
grpc: 10.61.188.118:8001
metrics: 10.61.188.118:8002/metrics

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
ServiceUnavailableError         # A Kubernetes service is not available.
```
## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
