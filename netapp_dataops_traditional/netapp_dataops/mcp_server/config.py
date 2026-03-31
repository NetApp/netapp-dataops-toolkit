import json
import logging
import os

logger = logging.getLogger(__name__)


def load_credentials():
    """Loads and validates the JSON configuration from the config.json file.

    Returns:
        dict: loaded configuration as a Python dictionary

    Raises:
        FileNotFoundError: If the config.json file is not found in any expected location.
        ValueError: If required keys are missing from the configuration.
    """

    # Path to the config.json credentials file in the user's home directory
    credentials_path = os.path.expanduser('~/.netapp_dataops/config.json')

    # If path not found, raise an error that config.json file doesn't exist
    if not os.path.exists(credentials_path):
        raise FileNotFoundError("Credentials file 'config.json' not found in the ~/.netapp_dataops directory.")

    # Opens the file specified, reads its contents, parses the contents as JSON, and stores the resulting data
    with open(credentials_path, 'r') as f:
        config = json.load(f)

    # List of top-level keys required in the config
    required_keys = [
        'connectionType',
        'hostname',
        'svm',
        'dataLif',
        'defaultVolumeType',
        'defaultExportPolicy',
        'defaultSnapshotPolicy',
        'defaultUnixUID',
        'defaultUnixGID',
        'defaultUnixPermissions',
        'defaultAggregate',
    ]

    # Ensures all required top-level keys are present
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key '{key}' in 'config.json' file.")

    _migrate_ssl_key(config)

    return config


def _migrate_ssl_key(config: dict) -> None:
    """Ensure ``sslCertPath`` is present, migrating from the legacy
    ``verifySSLCert`` boolean when necessary."""
    if "sslCertPath" in config:
        return

    if "verifySSLCert" in config:
        if config["verifySSLCert"] is False:
            logger.warning(
                "Legacy config key 'verifySSLCert' is set to false. "
                "SSL verification can no longer be disabled; using system CA bundle."
            )
        config["sslCertPath"] = ""
    else:
        config["sslCertPath"] = ""
