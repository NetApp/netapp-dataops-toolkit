# NVIDIA Triton Inference Server management with NetApp DataOps Toolkit for Kubernetes

The NetApp DataOps Toolkit for Kubernetes can be used to manage data science workspaces and inference servers within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to deploy a new NVIDIA Triton Inference Server instance, the ability to delete existing Inference Server instances, and list Inference Servers in specified namespaces.
<a name="command-line-functionality"></a>

## Command Line Functionality

You can perform the following operation(s) using the toolkit's command line utility

| Triton Inference Server operations                                                   | Supported by BeeGFS | Supported by Trident | Requires Astra Control |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- | ---------------------- |
| [Deploy a new NVIDIA Triton Inference Server.](#cli-create-triton-server)            | Yes                 | Yes                  | No                     |
| [Delete an NVIDIA Triton Inference Server.](#cli-delete-triton-server)               | Yes                 | Yes                  | No                     |
| [List all NVIDIA Triton Inference Servers in a specific namespace.](#cli-list-triton)| Yes                 | Yes                  | No                     |

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
netapp_dataops_k8s_cli.py create triton-server --server-name=lb1 --model-repo-pvc-name=model-pvc --load-balancer
Creating Service 'ntap-dsutil-triton-lb1' in namespace 'default'.
Service successfully created.

Creating Deployment 'ntap-dsutil-triton-lb1' in namespace 'default'.
Deployment 'ntap-dsutil-triton-lb1' created.
Waiting for Deployment 'ntap-dsutil-triton-lb1' to reach Ready state.
Deployment successfully created.

Server successfully created.
Server endpoints:
http: 10.61.188.115:30601
grpc: 10.61.188.115:31835
metrics: 10.61.188.115:31880/metrics
```

<a name="cli-delete-triton-server"></a>

#### Delete an existing NVIDIA Triton Inference Server instance 

The NetApp DataOps Toolkit can enable a user to near-instantaneously delete an existing NVIDIA Triton Inference Server instance. The command for deleting an NVIDIA Triton Inference Server instance is `netapp_dataops_k8s_cli.py delete triton-server`.

The following options/arguments are required:

```
    -s, --server-name=          Name of a new Triton Inference Server.
```

The following options/arguments are optional:

```
    -f, --force                     Do not prompt user to confirm operation.
    -h, --help                      Print help text.
    -n, --namespace=                Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
```
##### Example Usage

Delete the NVIDIA Inference server 'mike' in namespace 'dsk-test'.

```sh
netapp_dataops_k8s_cli.py delete triton-server --server-name=mike --namespace=dsk-test
Warning: All data associated with the workspace will be permanently deleted.
Are you sure that you want to proceed? (yes/no): yes
Deleting server 'mike' in namespace 'dsk-test'.
Note: this operation does NOT delete the model repository PVC.
Deleting Deployment...
Deleting Service...
Triton Server instance successfully deleted.
```
<a name="cli-list-triton"></a>

#### List All NVIDIA Triton Inference Server instances

The NetApp DataOps Toolkit can be used to print a list of all existing Triton Inference Servers in a specific namespace within a Kubernetes cluster. The command for printing a list of all existing NVIDIA Triton Servers is `netapp_dataops_k8s_cli.py list trtitonservers`.

No options/arguments are required for this command.

The following options/arguments are optional:

```
    -h, --help                  Print help text.
    -n, --namespace=            Kubernetes namespace for which to retrieve list of workspaces. If not specified, namespace "default" will be used.
```

##### Example Usage

List all NVIDIA Triton Inference Server instances in namespace "dsk-test".

```sh
netapp_dataops_k8s_cli.py list triton-servers --namespace=dsk-test
Server Name    Status     HTTP Endpoints       gRPC Endpoint        Metrics Endpoint
-------------  ---------  -------------------  -------------------  -------------------
imagesufian    Ready      10.61.188.115:31102  10.61.188.115:31608  10.61.188.115:31149
imagesufian1   Not Ready  10.61.188.115:30744  10.61.188.115:32689  10.61.188.115:30772
```

<a name="library-of-functions"></a>

## Advanced: Set of Functions

The NetApp DataOps Toolkit for Kubernetes provides a set of functions that can be imported into any Python program or Jupyter Notebook. In this manner, data scientists and data engineers can easily incorporate Kubernetes-native data management tasks into their existing projects, programs, and workflows. This functionality is only recommended for advanced users who are proficient in Python.

```py
from netapp_dataops.k8s import create_triton_server
from netapp_dataops.k8s import delete_triton_server
from netapp_dataops.k8s import list_triton_servers
```

The following workspace management operations are available within the set of functions.

| Triton Inference Server operations                                                   | Supported by BeeGFS | Supported by Trident | Requires Astra Control |
| ------------------------------------------------------------------------------------ | ------------------- | -------------------- | ---------------------- |
| [Deploy a new NVIDIA Triton Inference Server.](#lib-create-triton-server)            | Yes                 | Yes                  | No                     |
| [Delete an NVIDIA Triton Inference Server.](#lib-delete-triton-server)               | Yes                 | Yes                  | No                     |
| [List all NVIDIA Triton Inference Servers in a specific namespace.](#lib-list-triton)| Yes                 | Yes                  | No                     |

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

This function will return a list of server endpoints (in string format): ['<http_uri>', '<grpc_uri>', '<metrics_uri>']

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
ServiceUnavailableError         # A Kubernetes service is not available.
```

<a name="lib-delete-triton-server"></a>

#### Delete an existing NVIDIA Triton Inference Server instance 

The NetApp DataOps Toolkit can enable a user to near-instantaneously delete an existing NVIDIA Triton Server instance.


##### Function Definition

```py
def delete_triton_server(
    server_name: str,                    # Name of NVIDIA Triton Server instance to be deleted (required).
    namespace: str = "default",          # Kubernetes namespace that the workspace is located in. If not specified, namespace "default" will be used.
    print_output: bool = False           # Denotes whether or not to print messages to the console during execution.
) :
```

##### Return Value
 
None 

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

<a name="lib-list-triton"></a>

#### List All NVIDIA Triton Server instance

The NetApp DataOps Toolkit can be used to retrieve a list of all existing NVIDIA Triton Server instances in a specific namespace within a Kubernetes cluster as part of any Python program or workflow.

##### Function Definition

```py
def list_triton_servers(
    namespace: str = "default",             # Kubernetes namespace for which to retrieve list of workspaces. If not specified, namespace "default" will be used.
    print_output: bool = False              # Denotes whether or not to print messages to the console during execution.
) -> list :
```

##### Return Value

The function returns a list of all existing NVIDIA Triton Server instances. Each item in the list will be a dictionary containing details regarding a specific server. The keys for the values in this dictionary are "Server Name", "Status", "Server Endpoints".

##### Error Handling

If an error is encountered, the function will raise an exception of one of the following types. These exception types are defined in `netapp_dataops.k8s`.

```py
InvalidConfigError              # kubeconfig file is missing or is invalid.
APIConnectionError              # The Kubernetes API returned an error.
```

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
