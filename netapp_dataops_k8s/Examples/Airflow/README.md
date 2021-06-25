# Apache Airflow Examples
This directory contains example [DAG](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html#dags) definitions that show how NetApp data management functions can be incorporated into automated workflows that are orchestrated using the [Apache Airflow](https://airflow.apache.org) framework.

## Getting Started

### Instructions for Use
The Python files referenced in the [DAG Definitions](#dag-definitions) section contain Airflow DAG definitions. To utilize one of these example DAGs, define your parameters within the Python code as indicated in the comments and then upload the Python file to Airflow. The method of uploading the file to Airflow will depend on your specific Airflow deployment. Typically, Airflow is configured to automatically pull DAG definitions from a specific Git repo or persistent volume.

### Prerequisites

These DAGs require the following prerequisites in order to function correctly.

- Airflow must be deployed within a Kubernetes cluster. These example DAGs do not support Airflow deployments that are not Kubernetes-based.
- Airflow must be configured to use the [Celery Executor](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html). Although they may work with other executors, these DAGs have only been validated with the Celery Executor.
- [Trident](https://netapp.io/persistent-storage-provisioner-for-kubernetes/), NetApp's dynamic storage orchestrator for Kubernetes, must be installed within the Kubernetes cluster.
- A cluster role that has all of the required permissions for executing NetApp Data Science Toolkit for Kubernetes operations must be present in the Kubernetes cluster. For an example, see [cluster-role-ntap-dsutil.yaml](cluster-role-ntap-dsutil.yaml). This file contains the manifest for a Kubernetes ClusterRole named 'ntap-dsutil' that has all of the required permissions for executing toolkit operations within the cluster.
- Your Airflow [Kubernetes Pod Operator](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/operators.html#kubernetespodoperator) service account must be bound to the the previously mentioned cluster role within the namespace that you intend to execute the DAGs in. Note that the default Airflow Kubernetes Pod Operator service account is 'default'. For an example, see [role-binding-airflow-ntap-dsutil.yaml](role-binding-airflow-ntap-dsutil.yaml). This file contains the manifest for a Kubernetes RoleBinding named 'airflow-ntap-dsutil' that will bind the 'default' ServiceAccount to the 'ntap-dsutil' cluster role within the 'airflow' namespace.

Some of the DAGs have additional prerequisites, which are noted under the specific DAG definitions below.

<a name="dag-definitions"></a>

## DAG Definitions

### [ai-training-run.py](ai-training-run.py)

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this DAG requires the following additional prerequisites in order to function correctly.

- Volume snapshots must be enabled within the Kubernetes cluster. Refer to the [Trident documentation](https://netapp-trident.readthedocs.io/en/latest/kubernetes/operations/tasks/volumes/snapshots.html) for more information on volume snapshots.

#### Description
DAG definition for an AI/ML training run with built-in, near-instantaneous, dataset and model versioning. This is intended to demonstrate how a data scientist could define an automated AI/ML workflow that incorporates automated dataset and model versioning, and dataset-to-model traceability.

#### Workflow Steps
1. Optional: Execute a data prep step.
2. Create a Snapshot copy, using NetApp Snapshot technology, of the dataset volume. This Snapshot copy is created for traceability purposes. Each time that this pipeline workflow is executed, a Snapshot copy is created. Therefore, as long as the Snapshot copy is not deleted, it is always possible to trace a specific training run back to the exact training dataset that was used for that run.
3. Execute a training step.
4. Create a Snapshot copy, using NetApp Snapshot technology, of the trained model volume. This Snapshot copy is created for versioning purposes. Each time that this pipeline workflow is executed, a Snapshot copy is created. Therefore, for each individual training run, a read-only versioned copy of the resulting trained model is automatically saved.
5. Execute a validation step.

### [clone-volume.py](clone-volume.py)

#### Description
DAG definition for a workflow that can be used to near-instantaneously and efficiently clone any Trident-managed volume within the Kubernetes cluster, regardless of size. This is intended to demonstrate how a data scientist or data engineer could define an automated workflow that incorporates the rapid cloning of datasets and/or models for use in workspaces, etc.

#### Workflow Steps
1. Create a clone, using NetApp FlexClone technology, of the source volume.

### [replicate-data-cloud-sync.py](replicate-data-cloud-sync.py)

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this DAG requires the following additional prerequisites in order to function correctly.

- An Airflow connection of type "http" containing your Cloud Sync API refresh token must exist within the Airflow connections database. This connection can be created via the Airflow UI dashboard by navigating to 'Admin' -> 'Connections' using the main menu. When creating this connection, enter your Cloud Sync API refresh token into the 'Password' field.

#### Description
DAG definition for a workflow that can be used to perform a sync operation for an existing [Cloud Sync](https://cloudsync.netapp.com) relationship. This is intended to demonstrate how a data scientist or data engineer could define an automated AI/ML workflow that incorporates Cloud Sync for data movement between platforms (e.g. NFS, S3) and/or across environments (e.g. edge data center, core data center, private cloud, public cloud).

#### Workflow Steps
1. Perform a sync operation for the specified Cloud Sync relationship.

> Tip: If you do not know the Cloud Sync relationship ID for a specific relationship, you can retrieve it by using NetApp Data Science Toolkit for Traditional Environments (refer to the 'list all Cloud Sync relationships' operation).

### [replicate-data-snapmirror.py](replicate-data-snapmirror.py)

#### Compatiibility

This DAG is only compatible with ONTAP storage systems/instances runnning ONTAP 9.7 or above.

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this DAG requires the following additional prerequisites in order to function correctly.

- An Airflow connection of type "http" containing your ONTAP cluster or SVM admin account details must exist within the Airflow connections database. This connection can be created via the Airflow UI dashboard by navigating to 'Admin' -> 'Connections' using the main menu. When creating this connection, enter your ONTAP cluster or SVM management LIF into the 'Host' field, your ONTAP cluster/SVM admin username into the 'Login' field, and your ONTAP cluster/SVM admin password into the 'Password' field.

#### Description
DAG definition for a workflow that can be used to perform a sync operation for an existing asynchronous SnapMirror relationship. This is intended to demonstrate how a data scientist or data engineer could define an automated AI/ML workflow that incorporates SnapMirror replication for data movement across environments (e.g. edge data center, core data center, private cloud, public cloud).

#### Pipeline Steps
1. Perform a sync operation for the specified asynchronous SnapMirror relationship.

> Tip: If you do not know the SnapMirror relationship UUID for a specific relationship, you can retrieve it by using NetApp Data Science Toolkit for Traditional Environments (refer to the 'list all SnapMirror relationships' operation).

### [replicate-data-xcp.py](replicate-data-xcp.py)

#### Additional Prerequisites

In addition to the standard prerequisites outlined above, this DAG requires the following additional prerequisites in order to function correctly.

- An Airflow connection of type "SSH", containing SSH access details for a Linux host on which NetApp XCP is installed and configured, must exist within the Airflow connections database. This connection can be created via the Airflow UI dashboard by navigating to 'Admin' -> 'Connections' using the main menu.

#### Description
DAG definition for a workflow that that invokes NetApp XCP to quickly and reliably replicate data between NFS endpoints. Potential use cases include the following:
- Replicating newly acquired sensor data gathered at the edge back to the core data center or to the cloud to be used for AI/ML model training or retraining.
- Replicating a newly trained or newly updated model from the core data center to the edge or to the cloud to be deployed as part of an inferencing application.
- Copying data from a Hadoop data lake (through Hadoop NFS Gateway) to a high-performance AI/ML training environment for use in the training of an AI/ML model.
- Copying NFS-accessible data from a legacy or non-NetApp system of record to a high-performance AI/ML training environment for use in the training of an AI/ML model.

#### Workflow Steps
1. Invoke an XCP copy or sync operation.
