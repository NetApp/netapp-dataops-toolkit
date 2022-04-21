# Data Movement with NetApp DataOps Toolkit for Kubernetes

## Overview

Data movement with the NetApp DataOps Toolkit is available for use as a set of classes that can be imported
and used from other python programs. These operations are also available as part of the toolkit's command line utility.

The purpose of the data movement operations is to provide a mechanism to transfer data to or from a Kubernetes PVC.
In order to move the data a Kubernetes job will be created which will utilize a container with the relevant PVC 
mounted within the container. The container will then transfer the data from the original source to the destination,
either in to the PVC or out of the PVC, and the job will be completed.

## S3 Data Mover

The S3 data mover provides the mechanisms to transfer files and objects between a Kubernetes PVC and S3 buckets.

### Supported Services

The S3 data mover should work with most S3 compatible services. The implementation currently uses the minio mc docker
image for data movement, so any service compatible with that client should work with the S3 Data Mover.

The following is a support matrix based on compatibility testing.

| Service            |  Supported |
| ------------------ | ---------- |
| NetApp StorageGRID | Yes        |
| ONTAP S3           | No         |
| Amazon S3          | Yes        |

### Command Line Functionality

The netapp_dataops_k8s_cli.py script has the following commands available to perform S3 data movement operations.

| Command         | Description       |
| ---------------  | ------------------|
| create s3-secret     | Create a new K8s secret containing S3 credentials.         |
| delete s3-secret     | Delete an existing Kubernetes S3 secret.   |
| create ca-config-map | Create a Kubernetes config map object representing a Certificate Authority (CA) certificate. |
| delete ca-config-map | Delete a Kubernetes config map object representing a Certificate Authority (CA) certificate. |
| get-s3 bucket        | Get the contents of an S3 bucket and transfer the data to a specified Persistent Volume Claim (PVC). |
| get-s3 object        | Get an object (file) from an S3 bucket and transfer the file to a specified Persistent Volume Claim (PVC). |
| put-s3 bucket        | Copy the contents of a Persistent Volume Claim (PVC) to an S3 bucket. |
| put-s3 object        | Copy an object (file) from a Persistent Volume Claim (PVC) to an S3 bucket. |
| show s3-job          | Show the status of the specifed Kubernetes job. |
| delete s3-job        | Delete a Kubernetes S3 job. |

For additional details on the parameters for each command run the script with the command and the '-h' option to show the command help.

Example command help:
```
netapp_dataops_k8s_cli.py create s3-secret -h

Command: create s3-secret

Create a new K8s secret containing S3 credentials.

Required Options/Arguments:
        -d, --secret-name=              The name of the Kubernetes secret.
        -a, --access-key=               The access key for the S3 account.
        -s, --secret-key=               The secret key for the S3 account.

Optional Options/Arguments:
        -n, --namespace=                Kubernetes namespace used to store the secret.

Examples:
        netapp_dataops_k8s_cli.py create s3-secret --secret-name=mys3secret --access-key=abc --secret-key=secret123
        netapp_dataops_k8s_cli.py create s3-secret -d mys3secret -a abc -s secret123 -n team1
```

Follow the [S3 data mover basic usage](#s3-data-mover-basic-usage) section for the CLI commands similarly to how the classes are used.

### API Documentation
See the [NetApp DataOps Toolkit for Kubernetes API Documentation](api.md) for full details on the
API parameters.

<a name="s3-basic-usage"></a>

### S3 Data Mover Basic Usage

#### Setup S3 account credentials

The S3 data mover utilizes a Kubernetes secret to hold the account credentials used to authorize the connection
to the S3 service. This secret must be created before any of the S3 data mover operations can be performed. You
can choose to create the secret using the S3ConfigSecret class within the DataOps Toolkit, or you can create
the secret using some other method.

NOTES: 
- The Kubernetes secret can be maintained independently of the data mover jobs. You can create it once
and keep it there for as long as you need, or you can create it and remove it as needed.
- The Kubernetes secret must exist in the same namespace used for the data movement jobs.

##### Creating the S3 credentials secret with the DataOps Toolkit

You can use the S3ConfigSecret class to create or remove a Kubernetes secret intended to be used with the S3DataMover
class.

```python
from netapp_dataops.k8s.data_movers.s3 import S3ConfigSecret

s3_secret = S3ConfigSecret(name="my_secret_name", access_key="my_access_key", secret_key="my_secret_key")
s3_secret.create()
```

This will create the appropriate Kubernetes secret in the default namespace with the required information
for authenticating with the S3 service, the access key and the secret key.

If you intend to run the data movement operations in a separate namespace you can specify the namespace 
when creating the S3ConfigSecret object. 

```python
s3_secret = S3ConfigSecret(name="my_secret_name", access_key="my_access_key", secret_key="my_secret_key", namespace="dataops")
```

##### Creating the S3 credentials secret manually

You don't have to use the S3ConfigSecret class to create the secret if you don't want to. You can use any
other method of creating the secret as long as the secret contains the appropriate data. The secret must 
contain the following keys with the appropriate data.

| Key    | Value   |
|---------|----------|
| access_key | The S3 access key |
| secret_key | The S3 secret key associated with the access key |

#### Using the S3DataMover class

To perform data movement operations start by creating an object of the S3DataMover class which requires
providing the necessary information for connecting to the S3 service.

Here is an example of creating an S3DataMover object with the minimum required parameters.

```python
from netapp_dataops.k8s.data_movers.s3 import S3DataMover

data_mover = S3DataMover(credentials_secret="my_secret_name", s3_host="s3.mycompany.example.com")
```

The S3DataMover defaults to assuming usage of HTTPS on port 443 with SSL verification enabled. These settings
and others can be modified as needed. See the [NetApp DataOps Toolkit for Kubernetes API Documentation](api.md)
for full details on the API parameters.

Once the S3DataMover object is created it can be used to initiate any of the supported data movement operations
which include:

- get_bucket - Transfer all contents of a bucket to a PVC.
- put_bucket - Transfer all contents of a PVC (or directory within a PVC) to a bucket.
- get_object - Transfer an individual object from a bucket to a PVC.
- put_object - Transfer an individual object from a PVC to a bucket.

Let's use the get_bucket operation as an example. The other methods work very similarly.

```python
from netapp_dataops.k8s.data_movers.s3 import S3DataMover

data_mover = S3DataMover(credentials_secret="my_secret_name", s3_host="s3.mycompany.example.com")
mover_job = data_mover.get_bucket(bucket="TrainingSet1", pvc="dataops-volume-1")
```
This will create a Kubernetes job in the default namespace that will transfer all the contents from 
the TrainingSet1 bucket on the S3 service at `https://s3.mycompany.example.com` to the root directory of
the dataops-volume-1 PVC.

Note that depending on the amount of data to be transferred the data movement operation may take some 
considerable time to complete. The get_bucket operation is asynchronous in that it returns when the job
is created not when the job is completed. The get_bucket method returns the name of the job which can 
then be used to inspect the status of the job to see if it has completed or not.

To determine if the job has completed or not you can get the job status. This provides the Kubernetes
job status object model which provides multiple fields relating to the job status.

```python
mover_job_status = data_mover.get_job_status(job=mover_job)
```
See the [Kubernetes JobStatus Reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/job-v1/#JobStatus)
for details on this response.

Once the job is completed it will remain in Kubernetes as a job object. If you would like to cleanup
jobs that you no longer need to reference you can use the data mover's `delete_job` method to remove
a job from Kubernetes. Note, this will remove the job regardless of the job status, so make sure the 
targeted job is complete before using this function.

```python
data_mover.delete_job(job=mover_job)
```

### S3 Data Mover Advanced Usage

#### Providing CA certificates for trusting HTTPS connections to S3

If the SSL/TLS certificate for the S3 service is not trusted by default, either because it is self-signed
or it is signed by a company or organizational certificate authority (CA), then you will need to provide
the CA certificate to the data mover in order to verify the connection to the S3 service.

In order to provide the CA certificate to the data mover jobs we need to create a Kubernetes ConfigMap
object. The ConfigMap will hold the contents of the CA certificate which will then be made available
to the containers associated with the data mover jobs.

To assist with creating the ConfigMap object use the CAConfigMap class to read the certificate file(s)
and create the ConfigMap object.

```python
from netapp_dataops.k8s import CAConfigMap

# Specify the name of the config map and the path to the certificate file.
ca_map = CAConfigMap(name="s3-service-ca-configmap", certificate_file='ca-pem.cer')
# Then create the config map object
ca_map.create()
```

Once the ConfigMap is created then make sure to identify the ConfigMap name when creating the 
S3DataMover object.

```python
data_mover = S3DataMover(
    credentials_secret="s3-credentials",
    s3_host="s3.example.com",
    use_https=True,
    verify_certificates=True,
    ca_config_maps=['s3-service-ca-configmap']
)
```

Note that the parameter `ca-config-maps` takes a list for the argument type. This way multiple 
ConfigMaps can be provided if necessary. This might be required if you need to provide intermediate
and root certificates from multiple files for a CA chain.

#### Specifying directories within the Kubernetes PVC

When transferring files to or from a Kubernetes persistent volume you may want to use a specific 
directory as the base of the directory tree to transfer other than the root directory of the PVC.

For example, imagine the PVC contains a directory structure like the following.

```
/
|
|-- models/
|   |
|   |-- alpha/
|   |   |  afile1
|   |   |  afile2
|   |
|   |-- beta/
|   |   |  bfile1
|   |   |  bfile2
```

In our example we want to transfer all the files from the /models/beta directory to the S3 bucket
recursively. In that case use the pvc_dir parameter to specify the directory to use as the base of
the recursive transfer.

```python
from netapp_dataops.k8s.data_movers.s3 import S3DataMover

data_mover = S3DataMover(credentials_secret="my_secret_name", s3_host="s3.example.com")
mover_job = data_mover.put_bucket(bucket="TrainingSet1", pvc="dataops-volume-1", pvc_dir="models/beta/")
```

#### Specifying Kubernetes resources

You can specify Kubernetes resource requests and limits with the appropriate parameters for any
of the S3 data mover operations. This will help make sure the cpu or memory used by the data mover
jobs is properly constrained.

The requests and limits are specified during the creation of the data mover object.

```python
from netapp_dataops.k8s.data_movers.s3 import S3DataMover

data_mover = S3DataMover(
    credentials_secret="my_secret_name",
    s3_host="s3.example.com",
    cpu_request="300m",
    cpu_limit="500m",
    memory_request="8000Ki",
    memory_limit="20000Ki"
)
```

Refer to the Kubernetes documentation for [managing resources for containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
for details on how to set requests and limits.