# Using Dataset Manager in a JupyterLab Container on Kubernetes

This guide shows how to run [Dataset Manager](dataset_manager_readme.md) inside JupyterLab on Kubernetes using:

- A **custom container image** with `netapp-dataops-traditional` pre-installed
- A **Kubernetes Secret** for toolkit configuration and ONTAP credentials (no interactive `netapp_dataops_cli.py config`)
- A **Deployment manifest** that mounts the Dataset Manager root volume and starts JupyterLab
- **Memory-backed keyring + env-var injection** so ONTAP credentials are not written to persistent disk (`ONTAP_USERNAME` and `ONTAP_PASSWORD` are temporary and unset after the keyring is populated)

Example files live in [`examples/jupyterlab-k8s/`](../examples/jupyterlab-k8s/).

## Overview

Dataset Manager presents ONTAP-backed datasets as directories under a single **root volume**. Inside a Kubernetes pod, **you cannot NFS-mount volumes from within the container** — unprivileged containers cannot run `mount`. See [Mounting within Container](../troubleshooting.md#mounting-within-container).

The root volume is mounted into the pod by Kubernetes (PVC). Dataset Manager creates child datasets through the ONTAP REST API; new datasets appear as subdirectories under the mounted root path.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Pod (custom JupyterLab image)                                          │
│                                                                         │
│  /home/jovyan/work           ← workspace PVC (notebooks)                │
│    └── datasets/             ← Dataset Manager root PVC (nested mount)  │
│  /etc/netapp-dataops    ← Secret tmpfs (config.json only)               │
│  /run/netapp-keyring    ← emptyDir medium:Memory (keyring file in RAM)  │
│                                                                         │
│  netapp-dataops-traditional  →  ONTAP REST API                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Credential handling

The toolkit reads ONTAP credentials from the system keyring, not from `config.json`. The example Deployment uses two techniques to avoid leaving credentials on persistent disk:

1. **Env-var injection** — Temporary `ONTAP_USERNAME` and `ONTAP_PASSWORD` are set from the Kubernetes Secret via `secretKeyRef`. They are not mounted as files in the container. The startup script copies both values into the keyring, then **unsets both environment variables** so they do not remain in the shell environment after the keyring is populated.
2. **Memory-backed keyring** — An `emptyDir` volume with `medium: Memory` is mounted at `/run/netapp-keyring`. `XDG_DATA_HOME` points the keyring backend there, so the keyring file lives in RAM (tmpfs) rather than on the workspace PVC or container writable layer.

A startup script runs before JupyterLab: it symlinks `config.json` from the Secret mount, reads the temporary `ONTAP_USERNAME` and `ONTAP_PASSWORD` from the environment, loads them into the keyring, then unsets both.

## Prerequisites

- Kubernetes 1.20+ with a CSI driver that can provision or statically bind NFS volumes ([Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/) recommended for ONTAP).
- ONTAP 9.7+ with NFS enabled and an export policy allowing Kubernetes worker nodes.
- An ONTAP API account with Dataset Manager permissions — see [ONTAP least-privilege role](ontap_least_privilege_role.md#dataset-manager).
- Pod network access to the ONTAP **management** LIF (REST API) and **data** LIF (file I/O).
- A container registry to push your custom image.

## Step 1: Create the Dataset Manager root volume on ONTAP

Create the root volume once on ONTAP before deploying JupyterLab. The volume name and junction path must match what you put in `config.json` later.

Using the ONTAP CLI:

```bash
volume create -vserver svm1 -volume dataset_mgr_root -aggregate aggr1 -size 1g \
  -junction-path /dataset_mgr_root -unix-permissions 0444
```

Or using any other ONTAP management tool (System Manager, REST API, etc.). Requirements:

| Property | Value |
|----------|-------|
| Volume name | `dataset_mgr_root` (or your chosen name) |
| Junction path | `/<volume_name>` (e.g. `/dataset_mgr_root`) |
| Export policy | Must allow NFS from your Kubernetes nodes |
| Size | Small (1 GB is sufficient — it holds directory entries, not dataset data) |

Child datasets are separate ONTAP volumes junctioned under this root.

## Step 2: Expose the root volume to Kubernetes

Create a static NFS PersistentVolume and PVC that point at the ONTAP root volume. Use **ReadWriteMany** so multiple JupyterLab pods can share datasets.

See [`examples/jupyterlab-k8s/k8s/dataset-mgr-root-pv.yaml`](../examples/jupyterlab-k8s/k8s/dataset-mgr-root-pv.yaml). Replace `<ONTAP_DATA_LIF>` with your SVM data LIF IP or hostname.

```bash
kubectl create namespace data-science
kubectl apply -f examples/jupyterlab-k8s/k8s/dataset-mgr-root-pv.yaml
kubectl get pvc dataset-mgr-root -n data-science
```

Wait until the PVC status is `Bound`.

## Step 3: Build the container image

The image extends the [Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/) `scipy-notebook` image, installs the toolkit, bakes in the ONTAP management LIF TLS certificate, and registers a startup script that loads config from mounted Secrets.

### Obtain the ONTAP TLS certificate

Most ONTAP clusters use a self-signed certificate for the management LIF. Download it on your build host before `docker build` (replace `<ONTAP_MGMT_LIF>` with your management LIF hostname or IP):

```bash
cd examples/jupyterlab-k8s
echo | openssl s_client -connect <ONTAP_MGMT_LIF>:443 -showcerts 2>/dev/null \
  | openssl x509 > ontap_cert.pem
openssl x509 -in ontap_cert.pem -noout -subject -issuer
```

`ontap_cert.pem` must be in the build context directory. It is listed in `.gitignore` — do not commit it to git.

> **Public CA certificates:** If your ONTAP management LIF uses a certificate signed by a well-known public CA, you can leave `sslCertPath` blank in `config.json` instead. In that case, either skip copying a cert in the Dockerfile or supply any valid PEM file and set `"sslCertPath": ""`.

The certificate is installed in the image at `/usr/local/share/netapp-dataops/ontap_cert.pem`. Set `sslCertPath` in `config.json` to match:

```json
"sslCertPath": "/usr/local/share/netapp-dataops/ontap_cert.pem"
```

See [SSL Certificate Configuration](ontap_readme.md#ssl-certificate-configuration) for more detail.

### Optional: Modify Dockerfile

Modify the Dockerfile as needed (change the base image to your desired image, add additional Python packages to the `pip install` command, etc.).

[`examples/jupyterlab-k8s/Dockerfile`](../examples/jupyterlab-k8s/Dockerfile):

```dockerfile
FROM quay.io/jupyter/scipy-notebook:python-3.11

USER root

RUN pip install --no-cache-dir \
    netapp-dataops-traditional \
    keyrings.alt

RUN mkdir -p /usr/local/share/netapp-dataops
COPY ontap_cert.pem /usr/local/share/netapp-dataops/ontap_cert.pem
RUN chmod 644 /usr/local/share/netapp-dataops/ontap_cert.pem

COPY netapp-dataops-start.sh /usr/local/bin/start-notebook.d/netapp-dataops.sh
RUN chmod +x /usr/local/bin/start-notebook.d/netapp-dataops.sh

USER ${NB_UID}

ENV PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring
```

> **Note:** `keyrings.alt` provides a file-based keyring backend. At pod startup, temporary `ONTAP_USERNAME` and `ONTAP_PASSWORD` environment variables are read once, written to a keyring file on a **memory-backed tmpfs**, and then both env vars are unset. See [Credential handling](#credential-handling).

### Build and push

```bash
cd examples/jupyterlab-k8s
# ontap_cert.pem must exist in this directory (see above)
docker build -t <REGISTRY>/jupyterlab-dataset-manager:latest .
docker push <REGISTRY>/jupyterlab-dataset-manager:latest
```

## Step 4: Create Kubernetes Secrets

The toolkit stores ONTAP connection settings in `config.json` and credentials in the keyring. The Secret holds all three values, but the Deployment uses them differently:

| Secret key | How it reaches the pod |
|------------|------------------------|
| `config.json` | Mounted as a read-only file at `/etc/netapp-dataops/config.json` |
| `username` | Injected as temporary `ONTAP_USERNAME` environment variable, then stored in in-memory keyring (environment variable is subsequently unset) |
| `password` | Injected as temporary `ONTAP_PASSWORD` environment variable, then stored in in-memory keyring (environment variable is subsequently unset) |

### Toolkit config and ONTAP credentials

Edit [`config.json.example`](../examples/jupyterlab-k8s/config.json.example) for your environment. Key fields:

| Field | Description |
|-------|-------------|
| `hostname` | ONTAP management LIF |
| `sslCertPath` | Path to ONTAP cert in the image (`/usr/local/share/netapp-dataops/ontap_cert.pem`) — must match the Dockerfile `COPY` destination |
| `svm` | Storage VM name |
| `dataLif` | NFS data LIF |
| `defaultUnixUID` / `defaultUnixGID` | Match the container user (`1000` / `100` for Jupyter Docker Stacks `jovyan`) |
| `datasetManagerRootVolume` | Root volume name from Step 1 |
| `datasetManagerRootMountpoint` | Path where the root PVC is mounted in the pod (`/home/jovyan/work/datasets`) |

Create the Secret from local files (recommended — avoids committing secrets to git). The `username` and `password` literals become temporary `ONTAP_USERNAME` and `ONTAP_PASSWORD` environment variables at pod startup; both are unset once the keyring is populated:

```bash
kubectl create secret generic netapp-dataops-config \
  --namespace=data-science \
  --from-file=config.json=examples/jupyterlab-k8s/config.json \
  --from-literal=username=vsadmin \
  --from-literal=password='YOUR_ONTAP_PASSWORD'
```

Or apply the template manifest after editing placeholder values:

```bash
kubectl apply -f examples/jupyterlab-k8s/k8s/netapp-dataops-secret.yaml
```

### JupyterLab access token

Create another Secret for the JupyterLab access token.

```bash
kubectl apply -f examples/jupyterlab-k8s/k8s/jupyterlab-access-secret.yaml
# Edit the token value first, or create with:
kubectl create secret generic jupyterlab-access \
  --namespace=data-science \
  --from-literal=token="$(openssl rand -hex 32)"
```

## Step 5: Deploy JupyterLab

Apply the Deployment manifest. It creates a workspace PVC, Service, and Deployment.

[`examples/jupyterlab-k8s/k8s/jupyterlab-deployment.yaml`](../examples/jupyterlab-k8s/k8s/jupyterlab-deployment.yaml):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jupyterlab-workspace
  namespace: data-science
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  #storageClassName: <your-trident-storage-class>
---
apiVersion: v1
kind: Service
metadata:
  name: jupyterlab-dataset-manager
  namespace: data-science
spec:
  type: NodePort
  selector:
    app: jupyterlab-dataset-manager
  ports:
    - port: 8888
      targetPort: 8888
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jupyterlab-dataset-manager
  namespace: data-science
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jupyterlab-dataset-manager
  template:
    metadata:
      labels:
        app: jupyterlab-dataset-manager
    spec:
      containers:
        - name: jupyterlab
          image: <REGISTRY>/jupyterlab-dataset-manager:latest
          ports:
            - containerPort: 8888
          env:
            - name: JUPYTER_ENABLE_LAB
              value: "yes"
            - name: NETAPP_DATAOPS_SECRET_DIR
              value: /etc/netapp-dataops
            - name: XDG_DATA_HOME
              value: /run/netapp-keyring
            # Temporary: startup script loads into the keyring, then unsets ONTAP_USERNAME
            - name: ONTAP_USERNAME
              valueFrom:
                secretKeyRef:
                  name: netapp-dataops-config
                  key: username
            # Temporary: startup script loads this into the keyring, then unsets ONTAP_PASSWORD
            - name: ONTAP_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: netapp-dataops-config
                  key: password
            - name: JUPYTER_TOKEN
              valueFrom:
                secretKeyRef:
                  name: jupyterlab-access
                  key: token
          volumeMounts:
            - name: workspace
              mountPath: /home/jovyan/work
            - name: datasets
              mountPath: /home/jovyan/work/datasets
            - name: netapp-dataops-config
              mountPath: /etc/netapp-dataops
              readOnly: true
            - name: keyring-tmpfs
              mountPath: /run/netapp-keyring
      volumes:
        - name: workspace
          persistentVolumeClaim:
            claimName: jupyterlab-workspace
        - name: datasets
          persistentVolumeClaim:
            claimName: dataset-mgr-root
        - name: netapp-dataops-config
          secret:
            secretName: netapp-dataops-config
            items:
              - key: config.json
                path: config.json
        - name: keyring-tmpfs
          emptyDir:
            medium: Memory
            sizeLimit: 1Mi
```

Replace `<REGISTRY>` with your image registry, then deploy:

```bash
kubectl apply -f examples/jupyterlab-k8s/k8s/jupyterlab-deployment.yaml
kubectl rollout status deployment/jupyterlab-dataset-manager -n data-science
```

### Access JupyterLab

```bash
# Find the NodePort
kubectl get svc jupyterlab-dataset-manager -n data-science

# Open http://<node-ip>:<node-port> and enter the JUPYTER_TOKEN value
kubectl get secret jupyterlab-access -n data-science -o jsonpath='{.data.token}' | base64 -d
```

For production, use an Ingress or `LoadBalancer` Service type instead of NodePort.

### JupyterLab file browser

The Dataset Manager root PVC is mounted at `/home/jovyan/work/datasets` — a **nested mount** inside the workspace PVC (`/home/jovyan/work`). Kubernetes overlays the datasets volume on that path, so I/O under `datasets/` goes to the shared Dataset Manager root volume, not the workspace PVC.

This keeps the default `NOTEBOOK_DIR` of `/home/jovyan/work`, so `datasets/` appears in the JupyterLab file browser without any extra Jupyter configuration. Ensure `datasetManagerRootMountpoint` in `config.json` matches the mount path (`/home/jovyan/work/datasets`).

## Step 6: Use Dataset Manager in notebooks

Open a notebook and verify the setup:

```python
from netapp_dataops.traditional.datasets import Dataset, get_datasets

print(f"Existing datasets: {len(get_datasets())}")
```

### Create a dataset

```python
from netapp_dataops.traditional.datasets import Dataset
import pandas as pd

training = Dataset(name="training_v1", max_size="500GB")
print(f"Dataset path: {training.local_file_path}")  # /home/jovyan/work/datasets/training_v1

df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
df.to_parquet(f"{training.local_file_path}/data.parquet")
```

### Snapshot and clone

```python
training.snapshot(name="before_tuning")
experiment = training.clone(name="tuning_branch")
```

See the [Dataset Manager README](dataset_manager_readme.md) for the full API.

## End-to-end checklist

```bash
# 1. Create ONTAP root volume (once)
#    volume create ... -volume dataset_mgr_root -junction-path /dataset_mgr_root

# 2. Kubernetes namespace and storage
kubectl create namespace data-science
kubectl apply -f examples/jupyterlab-k8s/k8s/dataset-mgr-root-pv.yaml

# 3. Build and push image
cd examples/jupyterlab-k8s
echo | openssl s_client -connect <ONTAP_MGMT_LIF>:443 -showcerts 2>/dev/null \
  | openssl x509 > ontap_cert.pem
docker build -t <REGISTRY>/jupyterlab-dataset-manager:latest .
docker push <REGISTRY>/jupyterlab-dataset-manager:latest

# 4. Secrets (→ temporary ONTAP_USERNAME / ONTAP_PASSWORD env vars, unset after keyring load)
cp config.json.example config.json   # edit for your environment
kubectl create secret generic netapp-dataops-config \
  --namespace=data-science \
  --from-file=config.json=config.json \
  --from-literal=username=vsadmin \
  --from-literal=password='...'
kubectl create secret generic jupyterlab-access \
  --namespace=data-science \
  --from-literal=token="$(openssl rand -hex 32)"

# 5. Deploy (update image registry in manifest first)
kubectl apply -f k8s/jupyterlab-deployment.yaml
```

## Best practices

### Match UNIX permissions to the container user

Jupyter Docker Stacks runs as `jovyan` (UID `1000`, GID `100`). Set `defaultUnixUID`, `defaultUnixGID`, and `defaultUnixPermissions` in `config.json` accordingly, and ensure the ONTAP export policy allows NFS from your cluster nodes.

### Keep secrets out of the image and git

Store `config.json`, ONTAP credentials, and the Jupyter token in Kubernetes Secrets. Use `kubectl create secret --from-file` or a secrets manager (External Secrets Operator, Sealed Secrets, etc.) rather than committing plaintext values.

### Limit credential exposure on disk

Credentials must exist in the running pod for ONTAP API calls, but they do not need to be written to the workspace PVC or container image:

- Inject `username` and `password` as environment variables (`secretKeyRef`), not as mounted files. `ONTAP_USERNAME` and `ONTAP_PASSWORD` should be temporary: the example startup script loads both into the keyring and then unsets them.
- Set `XDG_DATA_HOME` to an `emptyDir` volume with `medium: Memory` so the keyring file is stored in RAM.
- Symlink `config.json` from the Secret mount instead of copying it to persistent storage.

Credentials are still visible to anyone with `kubectl exec` access (`printenv`, or reading the tmpfs keyring file). Complement this pattern with RBAC, network policies, etcd encryption at rest, and a [least-privilege ONTAP account](ontap_least_privilege_role.md).

### Separate workspace and dataset storage

Mount the workspace PVC at `/home/jovyan/work` and the Dataset Manager root PVC at `/home/jovyan/work/datasets` (nested inside `work`). Notebooks and `datasets/` both appear under the default JupyterLab file browser root. Dataset data still lives on the separate root PVC — deleting the workspace PVC does not remove datasets.

### Rotate credentials without rebuilding the image

Update the `netapp-dataops-config` Secret and restart the pod. On each container start, the startup script reloads credentials from the Secret into the keyring (using temporary `ONTAP_USERNAME` and `ONTAP_PASSWORD` env vars that are unset after loading).

```bash
kubectl rollout restart deployment/jupyterlab-dataset-manager -n data-science
```

## Troubleshooting

### `DatasetConfigError: Root mountpoint '/home/jovyan/work/datasets' is not accessible`

The root PVC is not mounted or `datasetManagerRootMountpoint` in `config.json` does not match the Deployment `volumeMount` path. Confirm both use `/home/jovyan/work/datasets` and the PVC is `Bound`.

### `Error: Missing username/password in credential manager`

The startup script did not load credentials. Verify the Secret contains `username` and `password` keys and the Deployment sets temporary `ONTAP_USERNAME` and `ONTAP_PASSWORD` from `secretKeyRef` (both should be unset after the keyring is populated). Check pod logs for `ONTAP credentials loaded into memory-backed keyring`:

```bash
kubectl logs deployment/jupyterlab-dataset-manager -n data-science
```

Also confirm `XDG_DATA_HOME` is set to `/run/netapp-keyring` and the `keyring-tmpfs` volume is mounted.

### `permission denied` writing files

ONTAP export policy or volume UNIX permissions do not match UID `1000`. Run `id` inside the pod and align `defaultUnixUID` / `defaultUnixGID` in `config.json`.

### New datasets not visible under `/home/jovyan/work/datasets`

Dataset Manager refreshes the NFS namespace after creating volumes. List the directory manually if needed:

```python
import os
os.listdir("/home/jovyan/work/datasets")
```

Verify the child volume junction in ONTAP is `/<root_volume>/<dataset_name>`.

### ONTAP API connection failures

Confirm the pod can reach the management LIF on port 443. Check `hostname` in `config.json` and cluster network policies.

### SSL certificate verification errors

**Error examples:** `CERTIFICATE_VERIFY_FAILED`, `self-signed certificate`, `no appropriate subjectAltName fields were found`

**Cause:** `sslCertPath` in `config.json` is blank or does not point to the certificate baked into the image.

**Resolution:**

1. Confirm the cert exists in the running container:
   ```bash
   kubectl exec -n data-science deployment/jupyterlab-dataset-manager -- \
     ls -la /usr/local/share/netapp-dataops/ontap_cert.pem
   ```
2. Ensure `config.json` contains:
   ```json
   "sslCertPath": "/usr/local/share/netapp-dataops/ontap_cert.pem"
   ```
3. If the ONTAP management LIF changed or the cluster certificate was rotated, re-download `ontap_cert.pem`, rebuild the image, and redeploy.

See [SSL Certificate Configuration](ontap_readme.md#ssl-certificate-configuration) and [troubleshooting](../troubleshooting.md).

## Related documentation

- [Dataset Manager README](dataset_manager_readme.md) — API reference, snapshots, clones, best practices
- [ONTAP Module README](ontap_readme.md) — ONTAP configuration details
- [Mounting within Container (troubleshooting)](../troubleshooting.md#mounting-within-container) — why in-container NFS mounts are not supported
- [Example files](../examples/jupyterlab-k8s/) — Dockerfile, startup script, and Kubernetes manifests
