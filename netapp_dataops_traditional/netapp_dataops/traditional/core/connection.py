"""Connection management utilities for NetApp DataOps operations."""

import base64
from typing import Dict, Any

import boto3
from botocore.config import Config as BotoConfig
from netapp_ontap import config as netappConfig
from netapp_ontap.host_connection import HostConnection as NetAppHostConnection

from ..exceptions import InvalidConfigError, ConnectionTypeError


def _resolve_ssl_verify(config: Dict[str, Any]) -> "bool | str":
    """Return the value to pass as ``verify`` to NetAppHostConnection.

    Supports both the new ``sslCertPath`` key and the legacy
    ``verifySSLCert`` boolean.  SSL verification is always enforced;
    the only choice is between the system CA bundle (``True``) and a
    user-supplied certificate file path.
    """
    if "sslCertPath" in config:
        path = config["sslCertPath"]
        return path if path else True

    if "verifySSLCert" in config and config["verifySSLCert"] is False:
        import logging
        logging.getLogger(__name__).warning(
            "Legacy config key 'verifySSLCert' is set to false. "
            "SSL verification can no longer be disabled; using system CA bundle."
        )

    return True


def _instantiate_connection(config: Dict[str, Any], connectionType: str = "ONTAP", print_output: bool = False) -> None:
    if connectionType == "ONTAP":
        try:
            ontapClusterMgmtHostname = config["hostname"]
            ontapClusterAdminUsername = config["username"]
            ontapClusterAdminPassword = config["password"]
        except KeyError:
            if print_output:
                from .config import _print_invalid_config_error
                _print_invalid_config_error()
            raise InvalidConfigError()

        netappConfig.CONNECTION = NetAppHostConnection(
            host=ontapClusterMgmtHostname,
            username=ontapClusterAdminUsername,
            password=ontapClusterAdminPassword,
            verify=_resolve_ssl_verify(config)
        )

    else:
        raise ConnectionTypeError()


def _instantiate_s3_session(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str, print_output: bool = False) -> Any:
    session = boto3.session.Session(aws_access_key_id=s3AccessKeyId, aws_secret_access_key=s3SecretAccessKey)
    config = BotoConfig(signature_version='s3v4')

    if s3VerifySSLCert:
        if s3CACertBundle:
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=s3CACertBundle, config=config)
        else:
            s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, config=config)
    else:
        s3 = session.resource(service_name='s3', endpoint_url=s3Endpoint, verify=False, config=config)

    return s3
