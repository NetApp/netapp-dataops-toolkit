"""Connection management utilities for NetApp DataOps operations."""

import base64
import logging
import ssl
from typing import Dict, Any

import boto3
from botocore.config import Config as BotoConfig
from netapp_ontap import config as netappConfig
from netapp_ontap.host_connection import HostConnection as NetAppHostConnection

from ..exceptions import InvalidConfigError, ConnectionTypeError

logger = logging.getLogger(__name__)


def _get_ssl_cert_path(config: Dict[str, Any]) -> str:
    """Extract the SSL certificate path from config, handling legacy keys.

    Returns the cert file path if configured, or empty string for system CA.
    Legacy ``verifySSLCert: false`` is overridden -- SSL is always enforced.
    """
    if "sslCertPath" in config:
        return config["sslCertPath"]

    if "verifySSLCert" in config and config["verifySSLCert"] is False:
        logger.warning(
            "Legacy config key 'verifySSLCert' is set to false. "
            "SSL verification can no longer be disabled; using system CA bundle."
        )

    return ""


def _apply_custom_ssl_context(conn, ca_cert_path: str) -> None:
    """Patch the connection's session to pin a CA cert while skipping hostname checks.

    ONTAP clusters commonly use self-signed certificates without Subject
    Alternative Name (SAN) entries.  Modern Python/OpenSSL rejects such certs
    during hostname verification even when the CA is trusted.  This function
    reconfigures the underlying urllib3 pool manager to use a custom
    ``ssl.SSLContext`` that still verifies the certificate chain against the
    pinned CA cert but disables hostname matching at both the OpenSSL level
    (``check_hostname=False``) and the urllib3 Python level
    (``assert_hostname=False``).
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(ca_cert_path)

    session = conn.session
    adapter = session.get_adapter(conn.origin)
    adapter.init_poolmanager(
        adapter._pool_connections,
        adapter._pool_maxsize,
        adapter._pool_block,
        ssl_context=ctx,
        assert_hostname=False,
    )


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

        ssl_cert_path = _get_ssl_cert_path(config)

        netappConfig.CONNECTION = NetAppHostConnection(
            host=ontapClusterMgmtHostname,
            username=ontapClusterAdminUsername,
            password=ontapClusterAdminPassword,
            verify=True,
        )

        if ssl_cert_path:
            _apply_custom_ssl_context(netappConfig.CONNECTION, ssl_cert_path)

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
