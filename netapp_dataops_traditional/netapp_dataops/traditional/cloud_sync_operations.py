"""
Cloud Sync operations for NetApp DataOps traditional environments.

This module contains all Cloud Sync-related operations including list relationships,
sync operations, and access token management.
"""

import base64
import json
import time

import requests
import yaml

from .exceptions import (
    InvalidConfigError, 
    APIConnectionError,
    CloudSyncSyncOperationError
)
from .core import (
    _retrieve_config, 
    _print_invalid_config_error,
    _retrieve_cloud_central_refresh_token
)


def _print_api_response(response: requests.Response):
    print("API Response:")
    print("Status Code: ", response.status_code)
    print("Header: ", response.headers)
    if response.text:
        print("Body: ", response.text)


def _get_cloud_central_access_token(refreshToken: str, print_output: bool = False) -> str:
    # Define parameters for API call
    url = "https://netapp-cloud-account.auth0.com/oauth/token"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refreshToken,
        "client_id": "Mu0V1ywgYteI6w1MbD15fKfVIUrNXGWC"
    }

    # Call API to optain access token
    response = requests.post(url=url, headers=headers, data=json.dumps(data))

    # Parse response to retrieve access token
    try:
        responseBody = json.loads(response.text)
        accessToken = responseBody["access_token"]
    except:
        errorMessage = "Error obtaining access token from Cloud Sync API"
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    return accessToken


def _get_cloud_sync_access_parameters(refreshToken: str, print_output: bool = False) -> tuple[str, str]:
    try:
        accessToken = _get_cloud_central_access_token(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/accounts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + accessToken
    }

    # Call API to obtain account ID
    response = requests.get(url=url, headers=headers)

    # Parse response to retrieve account ID
    try:
        responseBody = json.loads(response.text)
        accountId = responseBody[0]["accountId"]
    except:
        errorMessage = "Error obtaining account ID from Cloud Sync API"
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    # Return access token and account ID
    return accessToken, accountId


def list_cloud_sync_relationships(print_output: bool = False) -> list:
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API

    # Retrieve refresh token
    try:
        refreshToken = _retrieve_cloud_central_refresh_token(print_output=print_output)
    except InvalidConfigError:
        raise

    # Obtain access token and account ID
    try:
        accessToken, accountId = _get_cloud_sync_access_parameters(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    # Step 2: Retrieve list of relationships

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/relationships-v2"
    headers = {
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    # Call API to retrieve list of relationships
    response = requests.get(url = url, headers = headers)

    # Check for API response status code of 200; if not 200, raise error
    if response.status_code != 200:
        errorMessage = "Error calling Cloud Sync API to retrieve list of relationships."
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    # Constrict list of relationships
    relationships = json.loads(response.text)
    relationshipsList = list()
    for relationship in relationships:
        relationshipDetails = dict()
        relationshipDetails["id"] = relationship["id"]
        relationshipDetails["source"] = relationship["source"]
        relationshipDetails["target"] = relationship["target"]
        relationshipsList.append(relationshipDetails)

    # Print list of relationships
    if print_output:
        print(yaml.dump(relationshipsList))

    return relationshipsList


def sync_cloud_sync_relationship(relationship_id: str, wait_until_complete: bool = False, print_output: bool = False):
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API

    # Retrieve refresh token
    try:
        refreshToken = _retrieve_cloud_central_refresh_token(print_output=print_output)
    except InvalidConfigError:
        raise

    # Obtain access token and account ID
    try:
        accessToken, accountId = _get_cloud_sync_access_parameters(refreshToken=refreshToken, print_output=print_output)
    except APIConnectionError:
        raise

    # Step 2: Trigger Cloud Sync sync

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/relationships/%s/sync" % relationship_id
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    # Call API to trigger sync
    if print_output:
        print("Triggering sync operation for Cloud Sync relationship (ID = " + relationship_id + ").")
    response = requests.put(url = url, headers = headers)

    # Check for API response status code of 202; if not 202, raise error
    if response.status_code != 202:
        errorMessage = "Error calling Cloud Sync API to trigger sync operation."
        if print_output:
            print("Error:", errorMessage)
            _print_api_response(response)
        raise APIConnectionError(errorMessage, response)

    if print_output:
        print("Sync operation successfully triggered.")

    # Step 3: Obtain status of the sync operation; keep checking until the sync operation has completed

    if wait_until_complete:
        while True:
            # Define parameters for API call
            url = "https://cloudsync.netapp.com/api/relationships-v2/%s" % relationship_id
            headers = {
                "Accept": "application/json",
                "x-account-id": accountId,
                "Authorization": "Bearer " + accessToken
            }

            # Call API to obtain status of sync operation
            response = requests.get(url = url, headers = headers)

            # Parse response to retrieve status of sync operation
            try:
                responseBody = json.loads(response.text)
                latestActivityType = responseBody["activity"]["type"]
                latestActivityStatus = responseBody["activity"]["status"]
            except:
                errorMessage = "Error obtaining status of sync operation from Cloud Sync API."
                if print_output:
                    print("Error:", errorMessage)
                    _print_api_response(response)
                raise APIConnectionError(errorMessage, response)

            # End execution if the latest update is complete
            if latestActivityType == "Sync":
                if latestActivityStatus == "DONE":
                    if print_output:
                        print("Success: Sync operation is complete.")
                    break
                elif latestActivityStatus == "FAILED":
                    if print_output:
                        failureMessage = responseBody["activity"]["failureMessage"]
                        print("Error: Sync operation failed.")
                        print("Message:", failureMessage)
                    raise CloudSyncSyncOperationError(latestActivityStatus, failureMessage)
                elif latestActivityStatus == "RUNNING":
                    # Print message re: progress
                    if print_output:
                        print("Sync operation is not yet complete. Status:", latestActivityStatus)
                        print("Checking again in 60 seconds...")
                else:
                    if print_output:
                        print ("Error: Unknown sync operation status (" + latestActivityStatus + ") returned by Cloud Sync API.")
                    raise CloudSyncSyncOperationError(latestActivityStatus)

            # Sleep for 60 seconds before checking progress again
            time.sleep(60)


# Deprecated functions for backward compatibility  
def listCloudSyncRelationships(printOutput: bool = False) -> list:
    return list_cloud_sync_relationships(print_output=printOutput)


def syncCloudSyncRelationship(relationshipID: str, waitUntilComplete: bool = False, printOutput: bool = False):
    sync_cloud_sync_relationship(relationship_id=relationshipID, wait_until_complete=waitUntilComplete, print_output=printOutput)
