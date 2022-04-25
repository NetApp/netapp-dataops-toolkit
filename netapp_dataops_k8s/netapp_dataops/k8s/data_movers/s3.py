"""NetApp DataOps Toolkit S3 Data Mover module"""

from kubernetes.client import (
    V1ConfigMapVolumeSource,
    V1Container,
    V1EnvVar,
    V1EnvVarSource,
    V1KeyToPath,
    V1ObjectMeta,
    V1PersistentVolumeClaimVolumeSource,
    V1PodSpec,
    V1PodTemplateSpec,
    V1ResourceRequirements,
    V1SecretKeySelector,
    V1Volume,
    V1VolumeMount,
)

from netapp_dataops.k8s import (
    _get_labels,
    create_k8s_opaque_secret,
    delete_k8s_secret
)
from netapp_dataops.k8s.data_movers import DataMoverJob


class S3ConfigSecret:
    """Manage a Kubernetes Secret with S3 credentials for use with S3DataMover.

    This class can be used to help create and delete Kubernetes secrets to be used with the
    S3DataMover class. The secret holds the S3 credential information which is then provided
    to the pod used for transferring data to or from the S3 target.
    """

    def __init__(self,
                 name: str,
                 access_key: str,
                 secret_key: str,
                 namespace: str = 'default',
                 print_output: bool = False):
        """Initialize the S3ConfigSecret object.

        :param name: The name of the Kubernetes secret.
        :param access_key: The access key to use for authentication to the S3 service.
        :param secret_key: The secret key to use for authentication to the S3 service.
        :param namespace: The Kubernetes namespace to use for the secret. Defaults to the default
            namespace.
        :param print_output: If True enable information to be printed to the console. Default value is False.
        """
        # Validate we have values where required.
        for parameter in ["name", "access_key", "secret_key"]:
            if eval(parameter) is None:
                raise ValueError(
                    "Invalid value of None provided for parameter {}".format(parameter)
                )

        if namespace is None:
            self.namespace = 'default'
        else:
            self.namespace = namespace

        self.name = name
        self.secret_data = {
            "access_key": access_key,
            "secret_key": secret_key,
        }
        self.print_output = print_output

    def create(self):
        """Create the secret with the provided data."""
        labels = _get_labels(operation="s3configsecret-create")
        create_k8s_opaque_secret(name=self.name, data=self.secret_data,
                                 namespace=self.namespace, labels=labels,
                                 print_output=self.print_output)

    def delete(self):
        """Delete the secret from Kubernetes."""
        delete_k8s_secret(name=self.name, namespace=self.namespace, print_output=self.print_output)


class S3DataMover(DataMoverJob):
    """Used to move data between an S3 service and Kubernetes volumes.

    This data mover utilizes the Minio Client (MC) tool to transfer data.
    """

    def __init__(self, credentials_secret,
                 s3_host: str,
                 s3_port: str = None,
                 use_https: bool = True,
                 verify_certificates: bool = True,
                 image_name: str = None,
                 job_spec_template=None,
                 namespace: str = "default",
                 ca_config_maps: list = None,
                 cpu_request: str = None,
                 cpu_limit: str = None,
                 memory_request: str = None,
                 memory_limit: str = None,
                 print_output: bool = False):
        """Initialize the S3DataMover object.

        :param credentials_secret: The name of the Kubernetes secret which contains the S3 credentials.
        :param s3_host: The hostname or IP address to use for connecting to the S3 service.
        :param s3_port: The TCP port on the host to connect to for the S3 service. If None is set the default
            port associated with the protocol (http or https) will be used. The default is None.
        :param use_https: Specify True to use HTTPS for the S3 requests. Otherwise HTTP will be used. Defaults to
            True.
        :param verify_certificates: If True then the certificates will be verified when connecting to the S3 service.
            If False then the SSL/TLS certificates will not be verified. Defaults to True.
        :param image_name: The name of the image to use. By default the latest minio/mc image is used. This
            parameter may be used to specify a specific image tag or if the image needs to be found in a non-default
            repository. The specified image should be based on the minio/mc image or contain the minio client in order
            to work with the S3DataMover.
        :param job_spec_template: An optional V1JobSpec object to be used with any job created by the object. This
            is to be used to provide default values for an optional V1JobSpec properties. This should generally not
            be needed.
        :param namespace: The namespace used for the related Kubernetes objects, including the secret, the data mover
            job, and the volumes and volume claims used.
        :param ca_config_maps: A list of names of config maps containing trusted CA certificates to use with the data
            mover. This is only needed if the S3 service is using a certificate signed by a CA that is not trusted by
            default. For example if the S3 service is using a self-signed certificate.
        :param cpu_request: The amount of cpu to request for the container associated with a job. The request
            is used to help schedule the job's pod placement and reserves resources for the job. The value is
            the Kubernetes cpu unit as a string. An example would be "200m". If the cpu_request parameter is not
            set then no cpu request is used with the jobs.
        :param cpu_limit: The amount of cpu to use as a maximum limit for the container associated with a job.
            The job will not be allowed to use more cpu than what is specified here. The value is the Kubernetes
            cpu unit as a string. An example would be "500m". If the cpu_limit parameter is not set then no cpu
            limit is used with the jobs.
        :param memory_request: The amount of memory to request for use for the container associated with a job.
            The request is used to help schedule the job's pod placement and reserve resources for the job. The
            value is a string representing the amount of memory in bytes, or in the unit specified by the suffix
            used. An example would be "100M". If the memory_request parameter is not set then no memory request
            is used with the jobs.
        :param memory_limit: The amount of memory to set as the limit of memory used by a job. The job will not
            be allowed to use more memory than what is specified as the memory limit. The value is a string
            representing the amount of memory in bytes, or in the unit specified by the suffux used. An
            example would be "500M". If the memory_limit parameter is not set then no memory limit is used
            with the jobs.
        :param print_output: If True enable information to be printed to the console. Default value is False.
        """
        self.data_volume_name = "s3mc-data-volume"
        self.data_volume_path = "/mnt/data"
        self.config_map_path = "/mnt/config_maps"
        self.s3_alias = "DATAOPS"

        # Validate we have values where required.
        for parameter in ["s3_host", "credentials_secret", "use_https", "verify_certificates"]:
            if eval(parameter) is None:
                raise ValueError(
                    "Invalid value of None provided for parameter {}".format(parameter)
                )

        self.credentials_secret_name = credentials_secret
        self.s3_host = s3_host
        self.use_https = use_https
        self.verify_certificates = verify_certificates
        self.ca_config_maps = ca_config_maps
        self.cpu_request = cpu_request
        self.cpu_limit = cpu_limit
        self.memory_request = memory_request
        self.memory_limit = memory_limit

        if s3_port is None:
            if self.use_https:
                self.s3_port = "443"
            else:
                self.s3_port = "80"
        else:
            self.s3_port = s3_port

        if image_name is None:
            self.image = "minio/mc"
        else:
            self.image = f"{image_name}"

        super().__init__(namespace=namespace, job_spec_template=job_spec_template, print_output=print_output)

    def _get_container(self, command: str, config_map_volume_names: list = None) -> V1Container:
        """Get the K8s container object to be used by by a PodSpec.

        :param command: The command to run in the container.
        :return: The V1Container object definition to run the command.
        """
        if self.use_https:
            protocol = "https"
        else:
            protocol = "http"

        config_map_mounts = []
        if config_map_volume_names:
            for map_number, map_volume in enumerate(config_map_volume_names):
                mount_dir = self.config_map_path + f"/{map_number}"
                config_map_mounts.append(
                    V1VolumeMount(name=map_volume, mount_path=mount_dir)
                )
            env_setup_ca1 = "mkdir -p /root/.mc/certs/CAs; "
            # The find command doesn't exist by default in the minio container
            env_setup_ca2 = f"cp {self.config_map_path}/*/* /root/.mc/certs/CAs/; "
            env_setup_ca = env_setup_ca1 + env_setup_ca2
        else:
            env_setup_ca = ""

        env_setup1 = f"export MC_HOST_{self.s3_alias}={protocol}://${{S3_ACCESSKEY}}:${{S3_SECRETKEY}}@"
        env_setup2 = f"{self.s3_host}:{self.s3_port}; "
        container_setup = env_setup_ca + env_setup1 + env_setup2

        container = V1Container(
            name="netapp-dataops-s3mc-container",
            image=self.image,
            env=[
                V1EnvVar(
                    name="S3_ACCESSKEY",
                    value_from=V1EnvVarSource(
                        secret_key_ref=V1SecretKeySelector(
                            name=self.credentials_secret_name,
                            key="access_key"
                        )
                    )
                ),
                V1EnvVar(
                    name="S3_SECRETKEY",
                    value_from=V1EnvVarSource(
                        secret_key_ref=V1SecretKeySelector(
                            name=self.credentials_secret_name,
                            key="secret_key"
                        )
                    )
                ),
            ],
            command=["/bin/bash"],
            args=["-c", container_setup + command],
            volume_mounts=[
                              V1VolumeMount(mount_path=self.data_volume_path, name=self.data_volume_name)
                          ] + config_map_mounts,
            resources=self._get_resource_requirements()
        )

        return container

    def _get_pod_spec(self, container_command: str, pvc: str) -> V1PodSpec:
        config_map_volume_names = []
        config_map_volumes = []
        if self.ca_config_maps:
            for map_number, config_map in enumerate(self.ca_config_maps):
                config_map_name = f"ca-config-map-{map_number}"
                config_map_volumes.append(
                    V1Volume(
                        name=config_map_name,
                        config_map=V1ConfigMapVolumeSource(
                            name=config_map,
                            items=[V1KeyToPath(key="ca_cert", path=config_map)]
                        )
                    )
                )
                config_map_volume_names.append(config_map_name)

        pod_spec = V1PodSpec(
            containers=[
                self._get_container(command=container_command,
                                    config_map_volume_names=config_map_volume_names)
            ],
            volumes=[
                        V1Volume(name=self.data_volume_name,
                                 persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
                                     claim_name=pvc)
                                 )
                    ] + config_map_volumes,
            restart_policy="Never"
        )

        return pod_spec

    def _get_pod_template_spec(self, container_command: str, pvc: str,
                               operation: str,
                               metadata: V1ObjectMeta = None) -> V1PodTemplateSpec:
        """Get a K8s PodTemplateSpec to use with the given command.

        :param container_command: The command to use in the container. This is passed on.
        :param pvc: The name of the Kubernetes persistent volume claim to use in the data movement.
        :param operation: The name of the operation being used. This is used in the creation of the
            labels for the default pod metadata. If metadata is explicitly provided that will be used
            and won't contain the 'created-by-operation' label in the metadata.
        :param metadata: Optional metadata for the PodTemplateSpec.
        :return: The pod template spec definition for the provided command.
        """
        if metadata is None:
            metadata = V1ObjectMeta(
                labels=_get_labels(operation=operation)
            )
        return V1PodTemplateSpec(
            metadata=metadata,
            spec=self._get_pod_spec(container_command=container_command, pvc=pvc)
        )

    def _get_resource_requirements(self):
        """Get the resource requirements that are configured.

        This will construct and return the V1ResourceRequirements object to be used as the value
        of resource property of a container. The resource values are those provided when the S3
        data mover was initialized.
        """
        resources = V1ResourceRequirements()

        requests = {}
        if self.cpu_request is not None:
            requests['cpu'] = self.cpu_request
        if self.memory_request is not None:
            requests['memory'] = self.memory_request

        if requests:
            resources.requests = requests

        limits = {}
        if self.cpu_limit is not None:
            limits['cpu'] = self.cpu_limit
        if self.memory_limit is not None:
            limits['memory'] = self.memory_limit

        if limits:
            resources.limits = limits

        return resources

    def get_bucket(self, bucket: str, pvc: str, pvc_dir: str = None) -> str:
        """Start a job to transfer the contents of a bucket to a PVC.

        This will transfer the entire contents of the bucket to the PVC maintaining the relative
        directory structure of the files as they exist in the bucket.

        :param bucket: The name of the bucket that will be the source of the data transfer.
        :param pvc: The name of the Persistent Volume Claim that will be the destination of the
            data transfer.
        :param pvc_dir: An optional directory path to use as the base directory within the PVC
            for the destination of the files to be transferred. If no directory is specified here
            the root of the PVC is the base path used.
        :return: The name of the job created to transfer data.
        """
        if self.verify_certificates:
            verify_flag = ""
        else:
            verify_flag = "--insecure"

        if pvc_dir:
            sub_dir = pvc_dir
        else:
            sub_dir = ""

        operation = "get-bucket"
        command = f"mc cp {verify_flag} -r {self.s3_alias}/{bucket}/ {self.data_volume_path}/{sub_dir}"
        job_spec = self.job_spec
        job_spec.template = self._get_pod_template_spec(container_command=command, pvc=pvc, operation=operation)
        job_metadata = V1ObjectMeta(generate_name="s3mover-{}-".format(operation),
                                    namespace=self.namespace,
                                    labels=_get_labels(operation=operation))
        job = self.create_job(job_metadata=job_metadata, job_spec=job_spec)
        return job.metadata.name

    def get_object(self, bucket: str, pvc: str, object_key: str, file_location: str = None) -> str:
        """Start a job to transfer an object from a bucket to a PVC.

        This will transfer the specified object from the S3 bucket to the PVC.

        :param bucket: The name of the bucket where the object is located.
        :param pvc: The name of the Persistent Volume Claim where the object will be copied to.
        :param object_key: The value of the object key to copy from the bucket to the PVC.
        :param file_location: The location within the PVC to save the file, including the file name.
         If no location is specified the object will be copied to the PVC relative to the root of the PVC
         with any pathing retained from the object's key name. The default is None.
        :return: The name of the job created to transfer data.
        """
        if self.verify_certificates:
            verify_flag = ""
        else:
            verify_flag = "--insecure"

        operation = "get-object"

        if not file_location:
            file_location = object_key

        command = f"mc cp {verify_flag} {self.s3_alias}/{bucket}/{object_key} {self.data_volume_path}/{file_location}"
        job_spec = self.job_spec
        job_spec.template = self._get_pod_template_spec(container_command=command, pvc=pvc, operation=operation)
        job_metadata = V1ObjectMeta(generate_name="s3mover-{}-".format(operation),
                                    namespace=self.namespace,
                                    labels=_get_labels(operation=operation))
        job = self.create_job(job_metadata=job_metadata, job_spec=job_spec)
        return job.metadata.name

    def put_bucket(self, bucket: str, pvc: str, pvc_dir: str = None) -> str:
        """Start a job to transfer all files from a PVC to the named bucket.

        This will transfer all files recursively from the PVC to the S3 bucket and maintain any directory structure
        of the files in the bucket.

        :param bucket: The name of the bucket to which the files will be copied.
        :param pvc: The name of the Persistent Volume Claim where files will be copied from.
        :param pvc_dir: An optional path and directory name to specify the directory to use as the
            base for uploading objects to the S3 bucket. If this is not specified then the root of
            the PVC is used as the base directory.
        :return: The name of the job created.
        """
        if self.verify_certificates:
            verify_flag = ""
        else:
            verify_flag = "--insecure"

        if pvc_dir:
            sub_dir = pvc_dir
        else:
            sub_dir = ""
        operation = "put-bucket"
        # If we don't change directories the cp will copy files in to a 'data' directory within the bucket
        command = f"cd {self.data_volume_path}/{sub_dir};mc cp {verify_flag} -r * {self.s3_alias}/{bucket}"
        job_spec = self.job_spec
        job_spec.template = self._get_pod_template_spec(container_command=command, pvc=pvc, operation=operation)
        job_metadata = V1ObjectMeta(generate_name="s3mover-{}-".format(operation),
                                    namespace=self.namespace,
                                    labels=_get_labels(operation=operation))
        job = self.create_job(job_metadata=job_metadata, job_spec=job_spec)
        return job.metadata.name

    def put_object(self, bucket: str, pvc: str, file_location: str, object_key: str) -> str:
        """Start a job to transfer an object from a PVC to the named bucket.

        This will transfer a file from the the PVC to the S3 bucket and maintain any directory
        structure of the file relative to the root of the PVC.

        :param bucket: The name of the bucket to which the file will be copied.
        :param pvc: The name of the Persistent Volume Claim where the file will be copied from.
        :param file_location: The path and name of the source file to copy.
        :param object_key: The value of the object's key in the bucket.
        :return: The name of the job created.
        """
        if self.verify_certificates:
            verify_flag = ""
        else:
            verify_flag = "--insecure"
        operation = "put-object"
        command = f"mc cp {verify_flag} {self.data_volume_path}/{file_location} {self.s3_alias}/{bucket}/{object_key}"
        job_spec = self.job_spec
        job_spec.template = self._get_pod_template_spec(container_command=command, pvc=pvc, operation=operation)
        job_metadata = V1ObjectMeta(generate_name="s3mover-{}-".format(operation),
                                    namespace=self.namespace,
                                    labels=_get_labels(operation=operation))
        job = self.create_job(job_metadata=job_metadata, job_spec=job_spec)
        return job.metadata.name
