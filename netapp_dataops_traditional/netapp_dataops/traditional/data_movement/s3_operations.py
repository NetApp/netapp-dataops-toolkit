"""S3 operations for NetApp DataOps traditional environments."""

import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, Optional

import boto3
from botocore.client import Config as BotoConfig

from netapp_dataops.logging_utils import setup_logger
from ..exceptions import (
    InvalidConfigError, 
    APIConnectionError
)
from ..core import (
    _retrieve_config, 
    _print_invalid_config_error,
    deprecated
)

logger = setup_logger(__name__)


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


def _download_from_s3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool,
                   s3CACertBundle: str, s3Bucket: str, s3ObjectKey: str, localFile: str, print_output: bool = False):
    # Instantiate S3 session
    try:
        s3 = _instantiate_s3_session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId,
                                  s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert,
                                  s3CACertBundle=s3CACertBundle, print_output=print_output)
    except Exception as err:
        if print_output:
            logger.error("Error: S3 API error: %s", err)
        raise APIConnectionError(err)

    if print_output:
        logger.info("Downloading object '%s' from bucket '%s' and saving as '%s'.", s3ObjectKey, s3Bucket, localFile)

    # Create directories that don't exist
    if localFile.find(os.sep) != -1:
        dirs = localFile.split(os.sep)
        dirpath = os.sep.join(dirs[:len(dirs) - 1])
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

    try:
        s3.Object(s3Bucket, s3ObjectKey).download_file(localFile)
    except Exception as err:
        if print_output:
            logger.error("Error: S3 API error: %s", err)
        raise APIConnectionError(err)


def _upload_to_s3(s3Endpoint: str, s3AccessKeyId: str, s3SecretAccessKey: str, s3VerifySSLCert: bool, s3CACertBundle: str,
               s3Bucket: str, localFile: str, s3ObjectKey: str, s3ExtraArgs: str = None, print_output: bool = False):
    # Instantiate S3 session
    try:
        s3 = _instantiate_s3_session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId,
                                  s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert,
                                  s3CACertBundle=s3CACertBundle, print_output=print_output)
    except Exception as err:
        if print_output:
            logger.error("Error: S3 API error: %s", err)
        raise APIConnectionError(err)

    if print_output:
        logger.info("Uploading file '%s' to bucket '%s' and applying key '%s'.", localFile, s3Bucket, s3ObjectKey)

    try:
        if s3ExtraArgs:
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile, ExtraArgs=json.loads(s3ExtraArgs))
        else:
            s3.Object(s3Bucket, s3ObjectKey).upload_file(localFile)
    except Exception as err:
        if print_output:
            logger.error("Error: S3 API error: %s", err)
        raise APIConnectionError(err)


def pull_bucket_from_s3(s3_bucket: str, local_directory: str, s3_object_key_prefix: str = "", print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Add slash to end of local directory path if not present
    if not local_directory.endswith(os.sep):
        local_directory += os.sep

    # Multithread the download operation
    with ThreadPoolExecutor() as executor:
        try:
            # Instantiate S3 session
            s3 = _instantiate_s3_session(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, print_output=print_output)

            # Loop through all objects with prefix in bucket and download
            bucket = s3.Bucket(s3_bucket)
            for obj in bucket.objects.filter(Prefix=s3_object_key_prefix):
                executor.submit(_download_from_s3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, s3ObjectKey=obj.key, localFile=local_directory+obj.key, print_output=print_output)

        except APIConnectionError:
            raise

        except Exception as err:
            if print_output:
                logger.error("Error: S3 API error: %s", err)
            raise APIConnectionError(err)

    logger.info("Download complete.")


def pull_object_from_s3(s3_bucket: str, s3_object_key: str, local_file: str = None, print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Set S3 object key
    if not local_file:
        local_file = s3_object_key

    # Upload file
    try:
        _download_from_s3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, s3ObjectKey=s3_object_key, localFile=local_file, print_output=print_output)
    except APIConnectionError:
        raise

    logger.info("Download complete.")


def push_directory_to_s3(s3_bucket: str, local_directory: str, s3_object_key_prefix: str = "",
                         s3_extra_args: str = None, print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Multithread the upload operation
    with ThreadPoolExecutor() as executor:
        # Loop through all files in directory
        for dirpath, dirnames, filenames in os.walk(local_directory):
            # Exclude hidden files and directories
            filenames = [filename for filename in filenames if not filename[0] == '.']
            dirnames[:] = [dirname for dirname in dirnames if not dirname[0] == '.']

            for filename in filenames:
                # Build filepath
                if local_directory.endswith(os.sep):
                    dirpathBeginIndex = len(local_directory)
                else:
                    dirpathBeginIndex = len(local_directory) + 1

                subdirpath = dirpath[dirpathBeginIndex:]

                if subdirpath:
                    filepath = subdirpath + os.sep + filename
                else:
                    filepath = filename

                # Set S3 object details
                s3ObjectKey = s3_object_key_prefix + filepath
                localFile = dirpath + os.sep + filename

                # Upload file
                try:
                    executor.submit(_upload_to_s3, s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, localFile=localFile, s3ObjectKey=s3ObjectKey, s3ExtraArgs=s3_extra_args, print_output=print_output)
                except APIConnectionError:
                    raise

    logger.info("Upload complete.")


def push_file_to_s3(s3_bucket: str, local_file: str, s3_object_key: str = None, s3_extra_args: str = None, print_output: bool = False):
    # Retrieve S3 access details from existing config file
    try:
        s3Endpoint, s3AccessKeyId, s3SecretAccessKey, s3VerifySSLCert, s3CACertBundle = _retrieve_s3_access_details(print_output=print_output)
    except InvalidConfigError:
        raise

    # Set S3 object key
    if not s3_object_key:
        s3_object_key = local_file

    # Upload file
    try:
        _upload_to_s3(s3Endpoint=s3Endpoint, s3AccessKeyId=s3AccessKeyId, s3SecretAccessKey=s3SecretAccessKey, s3VerifySSLCert=s3VerifySSLCert, s3CACertBundle=s3CACertBundle, s3Bucket=s3_bucket, localFile=local_file, s3ObjectKey=s3_object_key, s3ExtraArgs=s3_extra_args, print_output=print_output)
    except APIConnectionError:
        raise

    logger.info("Upload complete.")


@deprecated
def pullBucketFromS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "", printOutput: bool = False):
    pull_bucket_from_s3(s3_bucket=s3Bucket, local_directory=localDirectory, s3_object_key_prefix=s3ObjectKeyPrefix, print_output=printOutput)


@deprecated
def pullObjectFromS3(s3Bucket: str, s3ObjectKey: str, localFile: str = None, printOutput: bool = False):
    pull_object_from_s3(s3_bucket=s3Bucket, s3_object_key=s3ObjectKey, local_file=localFile, print_output=printOutput)


@deprecated
def pushDirectoryToS3(s3Bucket: str, localDirectory: str, s3ObjectKeyPrefix: str = "", s3ExtraArgs: str = None, printOutput: bool = False):
    push_directory_to_s3(s3_bucket=s3Bucket, local_directory=localDirectory, s3_object_key_prefix=s3ObjectKeyPrefix, s3_extra_args=s3ExtraArgs, print_output=printOutput)


@deprecated
def pushFileToS3(s3Bucket: str, localFile: str, s3ObjectKey: str = None, s3ExtraArgs: str = None, printOutput: bool = False):
    push_file_to_s3(s3_bucket=s3Bucket, s3_object_key=s3ObjectKey, local_file=localFile, s3_extra_args=s3ExtraArgs, print_output=printOutput)
