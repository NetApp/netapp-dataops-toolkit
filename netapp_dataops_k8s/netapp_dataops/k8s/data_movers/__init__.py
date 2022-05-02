"""NetApp DataOps Toolkit data mover package."""
import copy

from kubernetes import client
from kubernetes.client import (
    V1Job,
    V1JobSpec,
    V1JobStatus,
    V1ObjectMeta,
    V1PodTemplateSpec,
)

from netapp_dataops.k8s import (
    _load_kube_config2,
    APIConnectionError,
    ApiException,
)


class DataMoverJob:
    """Manage Kubernetes jobs intended for moving data between locations.

    This class is meant to provide an interface to create a K8s job to be used
    to move data to or from a volume in Kubernetes. It is unlikely that you
    want to use this class directly. Instead use a derived class from this.
    """

    def __init__(self, namespace: str = "default",
                 job_spec_template: V1JobSpec = None,
                 print_output: bool = False):
        """Initialize a DataMoverJob object.

        :param namespace: The namespace which applies to the job. Defaults to the default namespace.
        :param job_spec_template: A Kubernetes job spec object. This can be used to configure any of the
            optional properties of a job spec if desired. It is intended that this can be used as a template
            to provide optional parameters of the V1JobSpec object. Derived classes should use a copy of the
            job spec and replace the required template field with the appropriate pod template spec for the
            particular operation being performed.
        :param print_output: If True enable information to be printed to the console. Default value is False.
        """
        if namespace is None:
            self.namespace = "default"
        else:
            self.namespace = namespace

        if job_spec_template is None:
            self.__job_spec = V1JobSpec(template=V1PodTemplateSpec())
        else:
            self.__job_spec = job_spec_template

        self.print_output = print_output

    @property
    def job_spec(self) -> V1JobSpec:
        """Get a deep copy of the object's job_spec template."""
        return copy.deepcopy(self.__job_spec)

    @job_spec.setter
    def job_spec(self, spec: V1JobSpec):
        self.__job_spec = spec

    def create_job(self, job_metadata: V1ObjectMeta, job_spec: V1JobSpec) -> V1Job:
        """Create a Kubernetes job.

        :return: The V1Job object representing the created job.
        """
        job_request = V1Job(
            api_version='batch/v1',
            kind='Job',
            metadata=job_metadata,
            spec=job_spec
        )

        _load_kube_config2(print_output=self.print_output)

        try:
            batch_api = client.BatchV1Api()
            job: V1Job = batch_api.create_namespaced_job(namespace=self.namespace,
                                                         body=job_request)
        except ApiException as error:
            raise APIConnectionError(error)
        return job

    def delete_job(self, job: str):
        """Delete the Kubernetes job with the provided name.

        This will delete the job with the provided name regardless of the status of the job.
        If you want to avoid deleting a job that has not completed then make sure to check
        the status of the job before using this function.

        :param job: The name of the job to delete.
        """
        _load_kube_config2(print_output=self.print_output)

        batch_api = client.BatchV1Api()
        try:
            batch_api.delete_namespaced_job(name=job, namespace=self.namespace)
        except ApiException as error:
            raise APIConnectionError(error)

    def did_job_fail(self, job: str) -> bool:
        """Get an indication if the job failed or not.

        A job is considered failed if one or more pods associated with the job ended in a failed
        state.

        Note: If the failed status of a job is false that may not mean it succeeded. This will
        return False if the job has not completed. To be sure of the job status check if the job
        is active or not first, and then check if the job succeeded or failed.

        :param job: The name of the job.
        :return: True if the job failed and False otherwise.
        """
        job_status = self.get_job_status(job=job)
        return bool(job_status.failed)

    def did_job_succeed(self, job: str) -> bool:
        """Get an indication if the job succeeded or not.

        This will return True if one or more pods associated with the job ended with a successful
        state.

        Note: If the success status of the job is false that may not mean the job failed. This
        will return False if the job has not completed. To be sure of the job status check if the
        job is active or not first, and then check if the job succeeded or failed.

        :param job: The name of the job.
        :return: True if the job succeeded and False otherwise.
        """
        job_status = self.get_job_status(job=job)
        return bool(job_status.succeeded)

    def get_job_status(self, job: str) -> V1JobStatus:
        """Get the status of a Kubernetes job.

        :param job: The name of the job to get the status of.
        :return: The status of the requested job.
        :raises APIConnectionError: When there is a problem connecting to Kubernetes.
        """
        _load_kube_config2(print_output=self.print_output)

        try:
            batch_api = client.BatchV1Api()
            job: V1Job = batch_api.read_namespaced_job_status(name=job, namespace=self.namespace)
        except ApiException as error:
            raise APIConnectionError(error)
        return job.status

    def is_job_active(self, job: str) -> bool:
        """Get an indication if the job is active or not.

        A job is active if one or more of it's associated pods is running.

        :param job: The name of the job.
        :return: True if the job is active, meaning a pod is running, and False otherwise.
        """
        job_status = self.get_job_status(job=job)
        return bool(job_status.active)

    def is_job_started(self, job: str) -> bool:
        """Get an indication if the job has started or not.

        :param job: The name of the job.
        :return: True if the job status indicates a start time. False otherwise.
        """
        job_status = self.get_job_status(job=job)
        return bool(job_status.start_time)
