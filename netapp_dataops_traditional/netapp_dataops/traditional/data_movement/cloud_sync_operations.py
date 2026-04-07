"""Cloud Sync operations for NetApp DataOps traditional environments."""

import base64
import json
import time
from typing import List, Dict, Any, Tuple

import requests
import yaml

from netapp_dataops.logging_utils import setup_logger
from ..exceptions import (
    InvalidConfigError, 
    APIConnectionError,
    CloudSyncSyncOperationError
)
from ..core import (
    _retrieve_cloud_central_refresh_token,
    deprecated
)

logger = setup_logger(__name__)


def _print_api_response(response: requests.Response) -> None:
    logger.info("API Response:")
    logger.info("Status Code: %s", response.status_code)
    logger.info("Header: %s", response.headers)
    if response.text:
        logger.info("Body: %s", response.text)


def _get_cloud_central_access_token(refreshToken: str, print_output: bool = False) -> str:
    url = "https://netapp-cloud-account.auth0.com/oauth/token"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refreshToken,
        "client_id": "Mu0V1ywgYteI6w1MbD15fKfVIUrNXGWC"
    }

    response = requests.post(url=url, headers=headers, data=json.dumps(data))

    try:
        responseBody = json.loads(response.text)
        accessToken = responseBody["access_token"]
    except (KeyError, json.JSONDecodeError):
        errorMessage = "Error obtaining access token from Cloud Sync API"
        if print_output:
            logger.error("Error: %s", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    return accessToken


def _get_cloud_sync_access_parameters(refreshToken: str, print_output: bool = False) -> Tuple[str, str]:
    try:
        accessToken = _get_cloud_central_access_token(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    url = "https://cloudsync.netapp.com/api/accounts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + accessToken
    }

    response = requests.get(url=url, headers=headers)

    try:
        responseBody = json.loads(response.text)
        accountId = responseBody[0]["accountId"]
    except (KeyError, IndexError, json.JSONDecodeError):
        errorMessage = "Error obtaining account ID from Cloud Sync API"
        if print_output:
            logger.error("Error: %s", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    return accessToken, accountId


def list_cloud_sync_relationships(print_output: bool = False) -> List[Dict[str, Any]]:
    try:
        refreshToken = _retrieve_cloud_central_refresh_token(print_output=print_output)
    except InvalidConfigError:
        raise

    try:
        accessToken, accountId = _get_cloud_sync_access_parameters(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    url = "https://cloudsync.netapp.com/api/relationships-v2"
    headers = {
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    response = requests.get(url=url, headers=headers)

    if response.status_code != 200:
        errorMessage = "Error calling Cloud Sync API to retrieve list of relationships."
        if print_output:
            logger.error("Error: %s", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    relationships = json.loads(response.text)
    relationshipsList = list()
    for relationship in relationships:
        relationshipDetails = dict()
        relationshipDetails["id"] = relationship["id"]
        relationshipDetails["source"] = relationship["source"]
        relationshipDetails["target"] = relationship["target"]
        relationshipsList.append(relationshipDetails)

    if print_output:
        logger.info("\n%s", yaml.dump(relationshipsList))

    return relationshipsList


def sync_cloud_sync_relationship(relationship_id: str, wait_until_complete: bool = False, print_output: bool = False) -> None:
    try:
        refreshToken = _retrieve_cloud_central_refresh_token(print_output=print_output)
    except InvalidConfigError:
        raise

    try:
        accessToken, accountId = _get_cloud_sync_access_parameters(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    url = "https://cloudsync.netapp.com/api/relationships/%s/sync" % relationship_id
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    if print_output:
        logger.info("Triggering sync operation for Cloud Sync relationship (ID = %s).", relationship_id)
    response = requests.put(url=url, headers=headers)

    if response.status_code != 202:
        errorMessage = "Error calling Cloud Sync API to trigger sync operation."
        if print_output:
            logger.error("Error: %s", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    if print_output:
        logger.info("Sync operation successfully triggered.")

    if wait_until_complete:
        while True:
            url = "https://cloudsync.netapp.com/api/relationships-v2/%s" % relationship_id
            headers = {
                "Accept": "application/json",
                "x-account-id": accountId,
                "Authorization": "Bearer " + accessToken
            }

            response = requests.get(url=url, headers=headers)

            try:
                responseBody = json.loads(response.text)
                latestActivityType = responseBody["activity"]["type"]
                latestActivityStatus = responseBody["activity"]["status"]
            except (KeyError, json.JSONDecodeError):
                errorMessage = "Error obtaining status of sync operation from Cloud Sync API."
                if print_output:
                    logger.error("Error: %s", errorMessage)
                    _print_api_response(response)
                raise APIConnectionError(errorMessage, response)

            if latestActivityType == "Sync":
                if latestActivityStatus == "DONE":
                    if print_output:
                        logger.info("Success: Sync operation is complete.")
                    break
                elif latestActivityStatus == "FAILED":
                    if print_output:
                        failureMessage = responseBody["activity"]["failureMessage"]
                        logger.error("Error: Sync operation failed.")
                        logger.error("Message: %s", failureMessage)
                    raise CloudSyncSyncOperationError(latestActivityStatus, failureMessage)
                elif latestActivityStatus == "RUNNING":
                    if print_output:
                        logger.info("Sync operation is not yet complete. Status: %s", latestActivityStatus)
                        logger.info("Checking again in 60 seconds...")
                else:
                    if print_output:
                        logger.error("Error: Unknown sync operation status (%s) returned by Cloud Sync API.", latestActivityStatus)
                    raise CloudSyncSyncOperationError(latestActivityStatus)

            time.sleep(60)


@deprecated
def listCloudSyncRelationships(printOutput: bool = False) -> list:
    return list_cloud_sync_relationships(print_output=printOutput)


@deprecated
def syncCloudSyncRelationship(relationshipID: str, waitUntilComplete: bool = False, printOutput: bool = False):
    sync_cloud_sync_relationship(relationship_id=relationshipID, wait_until_complete=waitUntilComplete, print_output=printOutput)
