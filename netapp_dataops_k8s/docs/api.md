<a id="netapp_dataops.k8s.data_movers"></a>

# netapp\_dataops.k8s.data\_movers

NetApp DataOps Toolkit data mover package.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob"></a>

## DataMoverJob Objects

```python
class DataMoverJob()
```

Manage Kubernetes jobs intended for moving data between locations.

This class is meant to provide an interface to create a K8s job to be used
to move data to or from a volume in Kubernetes. It is unlikely that you
want to use this class directly. Instead use a derived class from this.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.__init__"></a>

#### \_\_init\_\_

```python
def __init__(namespace: str = "default", job_spec_template: V1JobSpec = None, print_output: bool = False)
```

Initialize a DataMoverJob object.

**Arguments**:

- `namespace`: The namespace which applies to the job. Defaults to the default namespace.
- `job_spec_template`: A Kubernetes job spec object. This can be used to configure any of the
optional properties of a job spec if desired. It is intended that this can be used as a template
to provide optional parameters of the V1JobSpec object. Derived classes should use a copy of the
job spec and replace the required template field with the appropriate pod template spec for the
particular operation being performed.
- `print_output`: If True enable information to be printed to the console. Default value is False.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.job_spec"></a>

#### job\_spec

```python
@property
def job_spec() -> V1JobSpec
```

Get a deep copy of the object's job_spec template.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.create_job"></a>

#### create\_job

```python
def create_job(job_metadata: V1ObjectMeta, job_spec: V1JobSpec) -> V1Job
```

Create a Kubernetes job.

**Returns**:

The V1Job object representing the created job.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.delete_job"></a>

#### delete\_job

```python
def delete_job(job: str)
```

Delete the Kubernetes job with the provided name.

This will delete the job with the provided name regardless of the status of the job.
If you want to avoid deleting a job that has not completed then make sure to check
the status of the job before using this function.

**Arguments**:

- `job`: The name of the job to delete.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.did_job_fail"></a>

#### did\_job\_fail

```python
def did_job_fail(job: str) -> bool
```

Get an indication if the job failed or not.

A job is considered failed if one or more pods associated with the job ended in a failed
state.

Note: If the failed status of a job is false that may not mean it succeeded. This will
return False if the job has not completed. To be sure of the job status check if the job
is active or not first, and then check if the job succeeded or failed.

**Arguments**:

- `job`: The name of the job.

**Returns**:

True if the job failed and False otherwise.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.did_job_succeed"></a>

#### did\_job\_succeed

```python
def did_job_succeed(job: str) -> bool
```

Get an indication if the job succeeded or not.

This will return True if one or more pods associated with the job ended with a successful
state.

Note: If the success status of the job is false that may not mean the job failed. This
will return False if the job has not completed. To be sure of the job status check if the
job is active or not first, and then check if the job succeeded or failed.

**Arguments**:

- `job`: The name of the job.

**Returns**:

True if the job succeeded and False otherwise.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.get_job_status"></a>

#### get\_job\_status

```python
def get_job_status(job: str) -> V1JobStatus
```

Get the status of a Kubernetes job.

**Arguments**:

- `job`: The name of the job to get the status of.

**Raises**:

- `APIConnectionError`: When there is a problem connecting to Kubernetes.

**Returns**:

The status of the requested job.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.is_job_active"></a>

#### is\_job\_active

```python
def is_job_active(job: str) -> bool
```

Get an indication if the job is active or not.

A job is active if one or more of it's associated pods is running.

**Arguments**:

- `job`: The name of the job.

**Returns**:

True if the job is active, meaning a pod is running, and False otherwise.

<a id="netapp_dataops.k8s.data_movers.DataMoverJob.is_job_started"></a>

#### is\_job\_started

```python
def is_job_started(job: str) -> bool
```

Get an indication if the job has started or not.

**Arguments**:

- `job`: The name of the job.

**Returns**:

True if the job status indicates a start time. False otherwise.

<a id="netapp_dataops.k8s.data_movers.s3"></a>

# netapp\_dataops.k8s.data\_movers.s3

NetApp DataOps Toolkit S3 Data Mover module

<a id="netapp_dataops.k8s.data_movers.s3.S3ConfigSecret"></a>

## S3ConfigSecret Objects

```python
class S3ConfigSecret()
```

Manage a Kubernetes Secret with S3 credentials for use with S3DataMover.

This class can be used to help create and delete Kubernetes secrets to be used with the
S3DataMover class. The secret holds the S3 credential information which is then provided
to the pod used for transferring data to or from the S3 target.

<a id="netapp_dataops.k8s.data_movers.s3.S3ConfigSecret.__init__"></a>

#### \_\_init\_\_

```python
def __init__(name: str, access_key: str, secret_key: str, namespace: str = 'default', print_output: bool = False)
```

Initialize the S3ConfigSecret object.

**Arguments**:

- `name`: The name of the Kubernetes secret.
- `access_key`: The access key to use for authentication to the S3 service.
- `secret_key`: The secret key to use for authentication to the S3 service.
- `namespace`: The Kubernetes namespace to use for the secret. Defaults to the default
namespace.
- `print_output`: If True enable information to be printed to the console. Default value is False.

<a id="netapp_dataops.k8s.data_movers.s3.S3ConfigSecret.create"></a>

#### create

```python
def create()
```

Create the secret with the provided data.

<a id="netapp_dataops.k8s.data_movers.s3.S3ConfigSecret.delete"></a>

#### delete

```python
def delete()
```

Delete the secret from Kubernetes.

<a id="netapp_dataops.k8s.data_movers.s3.S3DataMover"></a>

## S3DataMover Objects

```python
class S3DataMover(DataMoverJob)
```

Used to move data between an S3 service and Kubernetes volumes.

This data mover utilizes the Minio Client (MC) tool to transfer data.

<a id="netapp_dataops.k8s.data_movers.s3.S3DataMover.__init__"></a>

#### \_\_init\_\_

```python
def __init__(credentials_secret, s3_host: str, s3_port: str = None, use_https: bool = True, verify_certificates: bool = True, image_tag: str = None, job_spec_template=None, namespace: str = "default", ca_config_maps: list = None, cpu_request: str = None, cpu_limit: str = None, memory_request: str = None, memory_limit: str = None, print_output: bool = False)
```

Initialize the S3DataMover object.

**Arguments**:

- `credentials_secret`: The name of the Kubernetes secret which contains the S3 credentials.
- `s3_host`: The hostname or IP address to use for connecting to the S3 service.
- `s3_port`: The TCP port on the host to connect to for the S3 service. If None is set the default
port associated with the protocol (http or https) will be used. The default is None.
- `use_https`: Specify True to use HTTPS for the S3 requests. Otherwise HTTP will be used. Defaults to
True.
- `verify_certificates`: If True then the certificates will be verified when connecting to the S3 service.
If False then the SSL/TLS certificates will not be verified. Defaults to True.
- `image_tag`: This is a string representing the tag for the image to pull. The S3DataMover uses the
minio/mc docker image to transfer data. This value must be a valid tag for this image. See hub.docker.com
for a list of valid tags.
- `job_spec_template`: An optional V1JobSpec object to be used with any job created by the object. This
is to be used to provide default values for an optional V1JobSpec properties. This should generally not
be needed.
- `namespace`: The namespace used for the related Kubernetes objects, including the secret, the data mover
job, and the volumes and volume claims used.
- `ca_config_maps`: A list of names of config maps containing trusted CA certificates to use with the data
mover. This is only needed if the S3 service is using a certificate signed by a CA that is not trusted by
default. For example if the S3 service is using a self-signed certificate.
- `cpu_request`: The amount of cpu to request for the container associated with a job. The request
is used to help schedule the job's pod placement and reserves resources for the job. The value is
the Kubernetes cpu unit as a string. An example would be "200m". If the cpu_request parameter is not
set then no cpu request is used with the jobs.
- `cpu_limit`: The amount of cpu to use as a maximum limit for the container associated with a job.
The job will not be allowed to use more cpu than what is specified here. The value is the Kubernetes
cpu unit as a string. An example would be "500m". If the cpu_limit parameter is not set then no cpu
limit is used with the jobs.
- `memory_request`: The amount of memory to request for use for the container associated with a job.
The request is used to help schedule the job's pod placement and reserve resources for the job. The
value is a string representing the amount of memory in bytes, or in the unit specified by the suffix
used. An example would be "100M". If the memory_request parameter is not set then no memory request
is used with the jobs.
- `memory_limit`: The amount of memory to set as the limit of memory used by a job. The job will not
be allowed to use more memory than what is specified as the memory limit. The value is a string
representing the amount of memory in bytes, or in the unit specified by the suffux used. An
example would be "500M". If the memory_limit parameter is not set then no memory limit is used
with the jobs.
- `print_output`: If True enable information to be printed to the console. Default value is False.

<a id="netapp_dataops.k8s.data_movers.s3.S3DataMover.get_bucket"></a>

#### get\_bucket

```python
def get_bucket(bucket: str, pvc: str, pvc_dir: str = None) -> str
```

Start a job to transfer the contents of a bucket to a PVC.

This will transfer the entire contents of the bucket to the PVC maintaining the relative
directory structure of the files as they exist in the bucket.

**Arguments**:

- `bucket`: The name of the bucket that will be the source of the data transfer.
- `pvc`: The name of the Persistent Volume Claim that will be the destination of the
data transfer.
- `pvc_dir`: An optional directory path to use as the base directory within the PVC
for the destination of the files to be transferred. If no directory is specified here
the root of the PVC is the base path used.

**Returns**:

The name of the job created to transfer data.

<a id="netapp_dataops.k8s.data_movers.s3.S3DataMover.get_object"></a>

#### get\_object

```python
def get_object(bucket: str, pvc: str, object_key: str, file_location: str = None) -> str
```

Start a job to transfer an object from a bucket to a PVC.

This will transfer the specified object from the S3 bucket to the PVC.

**Arguments**:

- `bucket`: The name of the bucket where the object is located.
- `pvc`: The name of the Persistent Volume Claim where the object will be copied to.
- `object_key`: The value of the object key to copy from the bucket to the PVC.
- `file_location`: The location within the PVC to save the file, including the file name.
If no location is specified the object will be copied to the PVC relative to the root of the PVC
with any pathing retained from the object's key name. The default is None.

**Returns**:

The name of the job created to transfer data.

<a id="netapp_dataops.k8s.data_movers.s3.S3DataMover.put_bucket"></a>

#### put\_bucket

```python
def put_bucket(bucket: str, pvc: str, pvc_dir: str = None) -> str
```

Start a job to transfer all files from a PVC to the named bucket.

This will transfer all files recursively from the PVC to the S3 bucket and maintain any directory structure
of the files in the bucket.

**Arguments**:

- `bucket`: The name of the bucket to which the files will be copied.
- `pvc`: The name of the Persistent Volume Claim where files will be copied from.
- `pvc_dir`: An optional path and directory name to specify the directory to use as the
base for uploading objects to the S3 bucket. If this is not specified then the root of
the PVC is used as the base directory.

**Returns**:

The name of the job created.

<a id="netapp_dataops.k8s.data_movers.s3.S3DataMover.put_object"></a>

#### put\_object

```python
def put_object(bucket: str, pvc: str, file_location: str, object_key: str) -> str
```

Start a job to transfer an object from a PVC to the named bucket.

This will transfer a file from the the PVC to the S3 bucket and maintain any directory
structure of the file relative to the root of the PVC.

**Arguments**:

- `bucket`: The name of the bucket to which the file will be copied.
- `pvc`: The name of the Persistent Volume Claim where the file will be copied from.
- `file_location`: The path and name of the source file to copy.
- `object_key`: The value of the object's key in the bucket.

**Returns**:

The name of the job created.

