"""Configuration management utilities for NetApp DataOps operations."""

import base64
import json
import os
from typing import Dict, Tuple

from netapp_dataops.logging_utils import setup_logger
from ..exceptions import InvalidConfigError

logger = setup_logger(__name__)


def _print_invalid_config_error() -> None:
    logger.error("Error: Missing or invalid config file. Run `netapp_dataops_cli.py config` to create config file.")


def _retrieve_config(configDirPath: str = "~/.netapp_dataops", configFilename: str = "config.json",
                   print_output: bool = False) -> Dict:
    configDirPath = os.path.expanduser(configDirPath)
    configFilePath = os.path.join(configDirPath, configFilename)
    try:
        with open(configFilePath, 'r') as configFile:
            config = json.load(configFile)
    except (FileNotFoundError, json.JSONDecodeError):
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()
    return config


def _retrieve_cloud_central_refresh_token(print_output: bool = False) -> str:
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        refreshTokenBase64 = config["cloudCentralRefreshToken"]
    except KeyError:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    refreshTokenBase64Bytes = refreshTokenBase64.encode("ascii")
    refreshTokenBytes = base64.b64decode(refreshTokenBase64Bytes)
    refreshToken = refreshTokenBytes.decode("ascii")

    return refreshToken


def _retrieve_s3_access_details(print_output: bool = False) -> Tuple[str, str, str, bool, str]:
    try:
        config = _retrieve_config(print_output=print_output)
    except InvalidConfigError:
        raise
    try:
        s3Endpoint = config["s3Endpoint"]
        s3AccessKeyId = config["s3AccessKeyId"]
        s3SecretAccessKeyBase64 = config["s3SecretAccessKey"]
        s3VerifySSLCert = config["s3VerifySSLCert"]
        s3CACertBundle = config["s3CACertBundle"]
    except KeyError:
        if print_output:
            _print_invalid_config_error()
        raise InvalidConfigError()

    s3SecretAccessKeyBase64Bytes = s3SecretAccessKeyBase64.encode("ascii")
    s3SecretAccessKeyBytes = base64.b64decode(s3SecretAccessKeyBase64Bytes)
    s3SecretAccessKey = s3SecretAccessKeyBytes.decode("ascii")

    return s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle
