# Using the NetApp Data Science Toolkit with Kubernetes

The NetApp Data Science Toolkit can be used in conjunction with Kubernetes in order to perform data management tasks from within Kubernetes-managed containers. NetApp recommends using [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/) to orchestrate storage resources within the Kubernetes environment.

## Example Use Cases

- A data scientist working within a Jupyter Notebook or JupyterLab container can use the NetApp Data Science Toolkit as a [library of functions](README.md#library-of-functions) that can be imported into any notebook in order to perform data management tasks directly from within the notebook.
- A data scientist working from an interactive terminal within a TensorFlow or PyTorch (or any other ML or DL framework) container can use the NetApp Data Science Toolkit as a [command line utility](README.md#command-line-functionality) in order to perform data management tasks directly from within the container.
- A data engineer can invoke a NetApp Data Science Toolkit operation as a step within a Apache Airflow, Kubeflow Pipeline, or Jenkins Pipeline workflow in order to incorporate data management tasks into automated workflows.

## Caveats

There are a few caveats to be aware of when using the NetApp Data Science Toolkit with Kubernetes.

### Creating and Cloning Data Volumes in a Kubernetes Environment

Data volumes that are created using the NetApp Data Science Toolkit will not automatically be represented by PVCs (PersistentVolumeClaims) in the Kubernetes cluster. In order to create a PVC for a volume that was created using the NetApp Data Science Toolkit, you will need to import the volume using Trident's volume import functionality. To avoid this extra step, NetApp recommends using Trident's native volume provisioning and volume cloning capabilities when operating in a Kubernetes environment. Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/) for more details and examples.

### Mount Operation within Container

It is not possible to mount a volume using the NetApp Data Science Toolkit while operating within a container. Mount operations are generally not permitted wtihin containers. Kubernetes handles the mounting of volume(s) at the time that a container is provisioned. Any volume mounts that are needed for a specific Kubernetes pod must be specified within the pod definition. Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/) for more details and examples.

### Trident Volume Names

The names of NetApp data volumes that are managed by [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/) will not match the names of the corresponding PVCs (PersistentVolumeClaims) in the Kubernetes environment. However, the name of the NetApp data volume can generally be derived from the PV (PersistantVolume) name. The following Python code will convert a PV name to a NetApp data volume name for a standard Trident installation:

```py
# Set pvName equal to the name of pv.
# Note: To get the name of the pv, you can run `kubectl -n <namespace> get pvc`.
#       The name of the pv that corresponds to a given pvc can be found in the 'VOLUME' column.
pvName = 'pvc-db963a53-abf2-4ffa-9c07-8815ce78d506'

# Convert the pv name to the NetApp data volume name; set volumeName equal to the name of the NetApp data volume.
# Note: The NetApp data volume name will not be accurate if you specified a custom storagePrefix when creating your Trident backend.
#       If you specified a custom storagePrefix, you will need to update this code to match your prefix.
volumeName = 'trident_%s' % pvName.replace("-", "_")
```