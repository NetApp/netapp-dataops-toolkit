# Kubeflow Pipelines Examples
This directory contains example pipeline definitions that show how NetApp data management functions can be incorporated into automated workflows that are orchestrated using the [Kubeflow Pipelines](https://www.kubeflow.org/docs/components/pipelines/) framework.

## Getting Started

### Instructions for Use
Executing any of the scripts referenced in the [Kubeflow Pipeline Definitions](#pipeline-definitions) section will produce a Kubeflow pipeline definition in the form of a YAML file that can then be uploaded to Kubeflow via Kubeflow Pipelines UI dashboard.

#### Dependencies
The following Python modules are required in order to execute any of these scripts - kfp, kubernetes. These modules can be installed using a Python package manager, such as pip.

### Prerequisites

These pipelines require the following prerequisites in order to function correctly.

- [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/), NetApp's dynamic storage orchestrator for Kubernetes, must be installed within the Kubernetes cluster.
- A cluster role that has all of the required permissions for executing NetApp DataOps Toolkit for Kubernetes operations must be present in the Kubernetes cluster. For an example, see [cluster-role-netapp-dataops.yaml](cluster-role-netapp-dataops.yaml). This file contains the manifest for a Kubernetes ClusterRole named 'netapp-dataops' that has all of the required permissions for executing toolkit operations within the cluster.
- Your Kubeflow Pipelines service account must be bound to the the previously mentioned cluster role within the namespace that you intend to execute the pipeline in. Note that the default Kubeflow Pipelines service account is 'default-editor'. For an example, see [role-binding-kubeflow-netapp-dataops.yaml](role-binding-kubeflow-netapp-dataops.yaml). This file contains the manifest for a Kubernetes RoleBinding named 'kubeflow-netapp-dataops' that will bind the 'default-editor' ServiceAccount to the 'netapp-dataops' cluster role within the 'admin' namespace.

Some of the pipelines have additional prerequisites, which are noted under the specific pipeline definitions below.

<a name="pipeline-definitions"></a>

## Kubeflow Pipeline Definitions

### [ai-training-run.py](ai-training-run.py)

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this pipeline requires the following additional prerequisites in order to function correctly.

- Volume snapshots must be enabled within the Kubernetes cluster. Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on volume snapshots.

#### Description
Python script that creates a Kubeflow pipeline definition for an AI/ML training run with built-in, near-instantaneous, dataset and model versioning. This is intended to demonstrate how a data scientist could define an automated AI/ML workflow that incorporates automated dataset and model versioning, and dataset-to-model traceability.

#### Run-time Parameters
- dataset_volume_pvc_existing: The name of the Kubernetes PersistentVolumeClaim (PVC) that is bound to the volume that contains the data that you want to use to train your model. Note: This PVC must be a Trident-managed PVC.
- trained_model_volume_pvc_existing: The name of the Kubernetes PersistentVolumeClaim (PVC) that is bound to the volume on which you want to store your trained model. Note: This PVC must be a Trident-managed PVC.
- execute_data_prep_step__yes_or_no: Denotes whether you wish to execute a data prep step as part of this particular pipeline execution (yes/no).
- data_prep_step_container_image: The container image in which you wish to execute your data prep step.
- data_prep_step_command: The command that you want to execute as your data prep step.
- data_prep_step_dataset_volume_mountpoint: The mountpoint at which you want to mount your dataset volume for your data prep step.
- train_step_container_image: The container image in which you wish to execute your training step.
- train_step_command: The command that you want to execute as your training step.
- train_step_dataset_volume_mountpoint: The mountpoint at which you want to mount your dataset volume for your training step.
- train_step_model_volume_mountpoint: The mountpoint at which you want to mount your model volume for your training step.
- validation_step_container_image: The container image in which you wish to execute your validation step.
- validation_step_command: The command that you want to execute as your validation step.
- validation_step_dataset_volume_mountpoint: the mountpoint at which you want to mount your dataset volume for your validation step.
- validation_step_model_volume_mountpoint: The mountpoint at which you want to mount your model volume for your validation step.

#### Pipeline Steps
1. Optional: Execute a data prep step.
2. Create a Snapshot copy, using NetApp Snapshot technology, of the dataset volume. This Snapshot copy is created for traceability purposes. Each time that this pipeline workflow is executed, a Snapshot copy is created. Therefore, as long as the Snapshot copy is not deleted, it is always possible to trace a specific training run back to the exact training dataset that was used for that run.
3. Execute a training step.
4. Create a Snapshot copy, using NetApp Snapshot technology, of the trained model volume. This Snapshot copy is created for versioning purposes. Each time that this pipeline workflow is executed, a Snapshot copy is created. Therefore, for each individual training run, a read-only versioned copy of the resulting trained model is automatically saved.
5. Execute a validation step.

### [clone-volume.py](clone-volume.py)

#### Description
Python script that creates a Kubeflow pipeline definition for a workflow that can be used to near-instantaneously and efficiently clone any Trident-managed volume within the Kubernetes cluster, regardless of size. This is intended to demonstrate how a data scientist or data engineer could define an automated AI/ML workflow that incorporates the rapid cloning of datasets and/or models for use in workspaces, etc.

#### Run-time Parameters
- source_volume_pvc_name: The name of the Kubernetes PersistentVolumeClaim (PVC) that is bound to the volume that you wish to clone. Note: This PVC must be a Trident-managed PVC.
- new_volume_pvc_name: The name that you wish to give to the new Kubernetes PVC corresponding to the newly-created volume clone.
- clone_from_snapshot__yes_or_no: Denotes whether or not the clone should be created from a specific snapshot related the source volume. If "no", then the clone will be created from the current state of the volume.
- source_volume_snapshot_name: Name of Kubernetes VolumeSnapshot to use as source for clone. Only required if 'clone_from_snapshot__yes_or_no' is "yes".

#### Pipeline Steps
1. Create a clone, using NetApp FlexClone technology, of the source volume.

### [delete-volume.py](delete-volume.py)

#### Description
Python script that creates a Kubeflow pipeline definition for a workflow that can be used to delete any Trident-managed volume within the Kubernetes cluster.

#### Run-time Parameters
- pvc_name: The name of the Kubernetes PersistentVolumeClaim (PVC) that is bound to the volume that you wish to delete. Note: This PVC must be a Trident-managed PVC.

#### Pipeline Steps
1. Delete the specified volume.

### [delete-snapshot.py](delete-snapshot.py)

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this pipeline requires the following additional prerequisites in order to function correctly.

- Volume snapshots must be enabled within the Kubernetes cluster. Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on volume snapshots.

#### Description
Python script that creates a Kubeflow pipeline definition for a workflow that can be used to delete any Trident-managed volume snapshot within the Kubernetes cluster.

#### Run-time Parameters
- volume_snapshot_name: The name of the Kubernetes VolumeSnapshot that you wish to delete. Note: This VolumeSnapshot must be a Trident-managed VolumeSnapshot.

#### Pipeline Steps
1. Delete the specified volume snapshot.

### [replicate-data-cloud-sync.py](replicate-data-cloud-sync.py)

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this pipeline requires the following additional prerequisites in order to function correctly.

- A Kubernetes secret containing your Cloud Sync API refresh token must exist within the namespace that you intend to execute the pipeline in. For an example, see [secret-cloud-sync-refresh-token.yaml](secret-cloud-sync-refresh-token.yaml). This file contains the manifest for a Kubernetes secret named 'cloud-sync-refresh-token' containing a Cloud Sync API refresh token.

#### Description
Python script that creates a Kubeflow pipeline definition for a workflow that can be used to perform a sync operation for an existing [Cloud Sync](https://cloudsync.netapp.com) relationship. This is intended to demonstrate how a data scientist or data engineer could define an automated AI/ML workflow that incorporates Cloud Sync for data movement between platforms (e.g. NFS, S3) and/or across environments (e.g. edge data center, core data center, private cloud, public cloud).

#### Run-time Parameters
- cloud_sync_relationship_id: The relationship ID of the Cloud Sync relationship for which you want to perform a sync operation. If you do not know the relationship ID, you can retrieve it by using NetApp DataOps Toolkit for Traditional Environments (refer to the 'list all Cloud Sync relationships' operation).
- cloud_sync_refresh_token_k8s_secret: The name of the Kubernetes secret containing your Cloud Sync refresh token.

#### Pipeline Steps
1. Perform a sync operation for the specified Cloud Sync relationship.

### [replicate-data-snapmirror.py](replicate-data-snapmirror.py)

#### Compatiibility

This pipeline is only compatible with ONTAP storage systems/instances runnning ONTAP 9.7 or above.

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this pipeline requires the following additional prerequisites in order to function correctly.

- A Kubernetes secret containing your ONTAP cluster or SVM admin account details must exist within the namespace that you intend to execute the pipeline in. For an example, see [secret-ontap-admin-account.yaml](secret-ontap-admin-account.yaml). This file contains the manifest for a Kubernetes secret named 'ontap-admin-account' containing ONTAP admin account details.

#### Description
Python script that creates a Kubeflow pipeline definition for a workflow that can be used to perform a sync operation for an existing asynchronous SnapMirror relationship. This is intended to demonstrate how a data scientist or data engineer could define an automated AI/ML workflow that incorporates SnapMirror replication for data movement across environments (e.g. edge data center, core data center, private cloud, public cloud).

#### Run-time Parameters
- snapmirror_relationship_id: The UUID of the SnapMirror relationship for which you want to perform a sync operation. If you do not know the UUID, you can retrieve it by using NetApp DataOps Toolkit for Traditional Environments (refer to the 'list all SnapMirror relationships' operation).
- destination_ontap_cluster_or_svm_mgmt_hostname: The host name or IP address of the ONTAP cluster or SVM management LIF corresponding to the cluster/SVM on which the destination volume resides.
- destination_ontap_cluster_or_svm_admin_acct_k8s_secret: The name of the Kubernetes secret containing the ONTAP cluster or SVM admin account details for the cluster/SVM on which the destination volume resides.
- destination_svm: The name of the SVM on which the destination volume resides.
- ontap_api_verify_ssl_cert__yes_or_no: Denotes whether or not to verify the SSL certificate when communicating with the ONTAP API (yes/no).

#### Pipeline Steps
1. Perform a sync operation for the specified asynchronous SnapMirror relationship.
