NetApp DataOps Toolkit for Kubernetes
=========

The NetApp DataOps Toolkit for Kubernetes is a Python library that makes it simple for developers, data scientists, DevOps engineers, and data engineers to perform various data management tasks within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new persistent volume or data science workspace, the ability to almost instantaneously clone a volume or workspace, the ability to almost instantaneously save off a snapshot of a volume or workspace for traceability/baselining, and the ability to move data between S3 compatible object storage and a Kubernetes persistent volume. The toolkit also includes an [MCP Server](docs/mcp_server_k8s.md) that exposes many of the capabilities as "tools" that can be utilized by AI agents.

## Compatibility

The NetApp DataOps Toolkit for Kubernetes supports Linux and macOS hosts.

The toolkit must be used in conjunction with a Kubernetes cluster in order to be useful. Additionally, [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/), NetApp's dynamic storage orchestrator for Kubernetes, and/or the [BeeGFS CSI driver](https://github.com/NetApp/beegfs-csi-driver/) must be installed within the Kubernetes cluster. The toolkit simplifies performing of various data management tasks that are actually executed by a NetApp maintained CSI driver. In order to facilitate this, the toolkit communicates with the appropriate driver via the Kubernetes API.

The toolkit is currently compatible with Kubernetes versions 1.20 and above, and OpenShift versions 4.7 and above.

The toolkit is currently compatible with Trident versions 20.07 and above. Additionally, the toolkit is compatible with the following Trident backend types:

- ontap-nas
- ontap-nas-flexgroup
- azure-netapp-files
- google-cloud-netapp-volume
- gcp-cvs

The toolkit is currently compatible with all versions of the BeeGFS CSI driver, though not all functionality is supported by BeeGFS. Operations that are not supported by BeeGFS are noted within the documentation.

## Installation

### Prerequisites

The NetApp DataOps Toolkit for Kubernetes requires that Python 3.8, 3.9, 3.10, 3,11, 3.12, or 3.13 be installed on the local host. Additionally, the toolkit requires that pip for Python3 be installed on the local host. For more details regarding pip, including installation instructions, refer to the [pip documentation](https://pip.pypa.io/en/stable/installing/).

### Installation Instructions

To install the NetApp DataOps Toolkit for Kubernetes, run the following command.

```sh
python3 -m pip install netapp-dataops-k8s
```

<a name="getting-started"></a>

## Getting Started: Standard Usage

The NetApp DataOps Toolkit for Kubernetes can be utilized from any Linux or macOS client that has network access to the Kubernetes cluster.

The toolkit requires that a valid kubeconfig file be present on the client, located at `$HOME/.kube/config` or at another path specified by the `KUBECONFIG` environment variable. Refer to the [Kubernetes documentation](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) for more information regarding kubeconfig files.

### Security considerations

**Kubeconfig on the client:** On Linux and macOS, before loading kubeconfig from disk, the toolkit sets each kubeconfig file it finds (from `KUBECONFIG` or `~/.kube/config`) to mode `0600` (read and write for the owner only). If the process cannot apply that mode—for example, the file is owned by another user—it fails with an error that explains how to run `chmod 600` manually. That reduces the risk of unauthorized cluster access from overly permissive local files. For additional protection if a workstation is lost or stolen, use full-disk encryption—for example [LUKS / dm-crypt](https://wiki.archlinux.org/title/Dm-crypt) on Linux, or [FileVault](https://support.apple.com/guide/mac-help/protect-data-filevault-macmh11732/mac) on macOS.

**Secrets in the cluster:** Kubernetes `Secret` objects use base64 encoding in the API; that does not provide confidentiality. Cluster administrators should configure [encryption at rest for etcd](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) so sensitive data is not stored in plaintext in etcd and backups. Use [Role-Based Access Control (RBAC)](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) so only intended identities can read `Secret` objects. For operational guidance, see [Good practices for Kubernetes Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/). Example RBAC for running this toolkit inside the cluster is in [Examples/service-account-netapp-dataops.yaml](Examples/service-account-netapp-dataops.yaml).

## Getting Started: In-cluster Usage (for advanced Kubernetes users)

The NetApp DataOps Toolkit for Kubernetes can also be utilized from within a pod that is running in the Kubernetes cluster. If the toolkit is being utilized within a pod in the Kubernetes cluster, then the pod's ServiceAccount must have the following permissions:

```yaml
- apiGroups: [""]
  resources: ["persistentvolumeclaims", "persistentvolumeclaims/status", "services"]
  verbs: ["get", "list", "create", "delete"]
- apiGroups: ["snapshot.storage.k8s.io"]
  resources: ["volumesnapshots", "volumesnapshots/status", "volumesnapshotcontents", "volumesnapshotcontents/status"]
  verbs: ["get", "list", "create", "delete"]
- apiGroups: ["apps", "extensions"]
  resources: ["deployments", "deployments/scale", "deployments/status"]
  verbs: ["get", "list", "create", "delete", "patch", "update"]
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list"]
```

In the [Examples](Examples/) directory, you will find the following examples pertaining to utilizing the toolkit within a pod in the Kubernetes cluster:
- [service-account-netapp-dataops.yaml](Examples/service-account-netapp-dataops.yaml): Manifest for a Kubernetes ServiceAccount named 'netapp-dataops' with RBAC (ClusterRole and ClusterRoleBinding) scoped to the permissions required for toolkit operations. Narrow or replace these rules in production if your workflows allow.
- [job-netapp-dataops.yaml](Examples/job-netapp-dataops.yaml): Manifest for a Kubernetes Job named 'netapp-dataops' that can be used as a template for executing toolkit operations.

Refer to the [Kubernetes documentation](https://kubernetes.io/docs/tasks/run-application/access-api-from-pod/) for more information on accessing the Kubernetes API from within a pod.

## Capabilities

The NetApp DataOps Toolkit for Kubernetes provides the following capabilities.

### MCP Server

The NetApp DataOps Toolkit for Kubernetes includes an [MCP Server](docs/mcp_server_k8s.md) that exposes many of the [Workspace Management](docs/workspace_management.md) and [Volume Management](docs/volume_management.md) capabilities as tools that can be utilized by AI agents.

### Workspace Management

The NetApp DataOps Toolkit can be used to manage data science workspaces within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new JupyterLab workspace, the ability to almost instantaneously clone a JupyterLab workspace, and the ability to almost instantaneously save off a snapshot of a JupyterLab workspace for traceability/baselining.

Refer to the [NetApp DataOps Toolkit for Kubernetes Workspace Management](docs/workspace_management.md) documentation for more details.

### Volume Management

The NetApp DataOps Toolkit can be used to manage persistent volumes within a Kubernetes cluster. Some of the key capabilities that the toolkit provides are the ability to provision a new persistent volume, the ability to almost instantaneously clone a persistent volume, and the ability to almost instantaneously save off a snapshot of a persistent volume for traceability/baselining.

Refer to the [NetApp DataOps Toolkit for Kubernetes Volume Management](docs/volume_management.md) documentation for more details.

### Data Movement

The NetApp DataOps Toolkit provides the ability to facilitate data movement between Kubernetes persistent volumes
and external services. The data movement operations currently provided are for use with S3 compatible services.

Refer to the [NetApp DataOps Toolkit for Kubernetes Data Movement](docs/data_movement.md) documentation for more details.

### NVIDIA Triton Inference Server Management

The NetApp DataOps Toolkit provides the ability to manage NVIDIA Triton Inference Server instances whithin a Kubernetes cluster.  

Refer to the [NetApp DataOps Toolkit for NVIDIA Triton Inference Server Management](docs/inference_server_management.md) documentation for more details.


## SSL Certificate Configuration for ONTAP API Access

Some toolkit operations (e.g. FlexCache create/delete) connect directly to the ONTAP REST API over HTTPS. If your ONTAP cluster uses a self-signed certificate, you must provide the certificate so the toolkit can verify the server's identity.

The SSL certificate path is passed as a **command-line argument** (`--ssl-cert-path`) or **function parameter** (`ssl_cert_path`) to the operations that require it. If omitted, the system CA bundle is used.

### Obtaining the Certificate from Your ONTAP Cluster

**Step 1 — Download the certificate from any machine that can reach the ONTAP management LIF:**

```sh
echo | openssl s_client -connect <ONTAP_HOST>:443 -showcerts 2>/dev/null \
  | openssl x509 > ontap_cert.pem
```

**Step 2 — Make the certificate available inside the cluster.**

The certificate file must exist at the configured path every time a pod starts. Use one of the following approaches (listed from most to least recommended):

1. **Kubernetes Secret or ConfigMap (recommended)** — Store the certificate content in a Secret or ConfigMap and mount it as a volume. This is the most reliable approach: Kubernetes re-mounts the volume automatically on every pod start, and it works regardless of which node the pod is scheduled on.

   ```sh
   kubectl create secret generic ontap-ca-cert \
     --from-file=ontap_cert.pem=ontap_cert.pem -n <your-namespace>
   ```

   Then mount it in your pod spec:

   ```yaml
   volumes:
     - name: ontap-ca-cert
       secret:
         secretName: ontap-ca-cert
   containers:
     - volumeMounts:
         - name: ontap-ca-cert
           mountPath: /etc/ssl/certs/ontap_cert.pem
           subPath: ontap_cert.pem
           readOnly: true
   ```

2. **Container image** — Bake the certificate into a custom container image at a known path. Survives restarts but requires an image rebuild if the certificate changes.

3. **`hostPath` volume** — Place the file on the node filesystem. Survives pod restarts but **not rescheduling to a different node** unless the file is present on all nodes.

> **Note:** Do not manually copy the certificate into a running pod (e.g. via `kubectl cp`). Manually copied files are lost when the pod restarts.

**Step 3 — Pass the certificate path when running toolkit commands:**

```sh
netapp_dataops_k8s_cli.py create flexcache \
  --flexcache-vol=cache1 --flexcache-size=50Gi \
  --source-vol=origin1 --source-svm=svm1 --backend-name=backend1 \
  --ssl-cert-path=/etc/ssl/certs/ontap_cert.pem
```

Or when using the toolkit as a Python library:

```python
from netapp_dataops.k8s import create_flexcache
create_flexcache(..., ssl_cert_path="/etc/ssl/certs/ontap_cert.pem")
```

### How Certificate Verification Works

When a certificate path is provided, the toolkit verifies the ONTAP server's certificate chain against the pinned CA cert file. Hostname/SAN matching is skipped because many ONTAP self-signed certificates lack Subject Alternative Name entries. When no certificate path is provided, the system CA bundle is used with full hostname verification.

In both cases SSL verification is always enforced — the toolkit never sends credentials over an unverified connection.

## Tips and Tricks

- [Use the NetApp DataOps Toolkit in conjunction with Kubeflow.](Examples/Kubeflow/)
- [Use the NetApp DataOps Toolkit in conjunction with Apache Airflow.](Examples/Airflow/)

## Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
