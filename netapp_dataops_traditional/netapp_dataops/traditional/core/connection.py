"""
Connection management utilities for NetApp DataOps operations.

This module handles connection instantiation and management for ONTAP and other
NetApp services.
"""

import base64
import boto3
from botocore.config import Config as BotoConfig
from netapp_ontap import config as netappConfig
from netapp_ontap.host_connection import HostConnection as NetAppHostConnection

from ..exceptions import InvalidConfigError, ConnectionTypeError


def _instantiate_connection(config: dict, connectionType: str = "ONTAP", print_output: bool = False):
    if connectionType == "ONTAP":
        ## Connection details for ONTAP cluster
        try:
            ontapClusterMgmtHostname = config["hostname"]
            ontapClusterAdminUsername = config["username"]
            ontapClusterAdminPasswordBase64 = config["password"]
            verifySSLCert = config["verifySSLCert"]
        except:
            if print_output:
                from .config import _print_invalid_config_error
                _print_invalid_config_error()
            raise InvalidConfigError()

        # Decode base64-encoded password
        ontapClusterAdminPasswordBase64Bytes = ontapClusterAdminPasswordBase64.encode("ascii")
        ontapClusterAdminPasswordBytes = base64.b64decode(ontapClusterAdminPasswordBase64Bytes)
        ontapClusterAdminPassword = ontapClusterAdminPasswordBytes.decode("ascii")

        # Instantiate connection to ONTAP cluster
        netappConfig.CONNECTION = NetAppHostConnection(
            host=ontapClusterMgmtHostname,
            username=ontapClusterAdminUsername,
            password=ontapClusterAdminPassword,
            verify=verifySSLCert
        )

    else:
        raise ConnectionTypeError()


def _instantiate_s3_session(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str, print_output: bool = False):
    # Instantiate session
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
