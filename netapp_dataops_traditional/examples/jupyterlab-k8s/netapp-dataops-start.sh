#!/bin/bash
# Sourced by Jupyter Docker Stacks before JupyterLab starts.
#
# - Symlinks config.json from the mounted Secret (no copy to workspace disk)
# - Loads ONTAP credentials from environment variables into the keyring
# - Keyring data is stored on a memory-backed tmpfs via XDG_DATA_HOME

# Do not use `set -u` (nounset): this script is sourced by Jupyter Docker Stacks'
# start.sh, and nounset would leak into that shell and break optional vars like GRANT_SUDO.
set -eo pipefail

SECRET_DIR="${NETAPP_DATAOPS_SECRET_DIR:-/etc/netapp-dataops}"
CONFIG_DEST="${HOME}/.netapp_dataops/config.json"

if [[ -f "${SECRET_DIR}/config.json" ]]; then
    mkdir -p "$(dirname "${CONFIG_DEST}")"
    ln -sf "${SECRET_DIR}/config.json" "${CONFIG_DEST}"
    echo "NetApp DataOps Toolkit config linked at ${CONFIG_DEST}"
else
    echo "WARNING: ${SECRET_DIR}/config.json not found; Dataset Manager will not be configured." >&2
fi

if [[ -z "${XDG_DATA_HOME:-}" ]]; then
    echo "WARNING: XDG_DATA_HOME is not set; keyring may write credentials to container disk." >&2
    echo "         Mount an emptyDir with medium: Memory and set XDG_DATA_HOME in the Deployment." >&2
fi

if [[ -n "${ONTAP_USERNAME:-}" && -n "${ONTAP_PASSWORD:-}" ]]; then
    python - <<'PY'
import os
import keyring
from netapp_dataops.constants import KEYRING_SERVICE_NAME

keyring.set_password(KEYRING_SERVICE_NAME, "username", os.environ["ONTAP_USERNAME"])
keyring.set_password(KEYRING_SERVICE_NAME, "password", os.environ["ONTAP_PASSWORD"])
print("ONTAP credentials loaded into memory-backed keyring")
PY
    unset ONTAP_USERNAME ONTAP_PASSWORD
else
    echo "WARNING: ONTAP_USERNAME/ONTAP_PASSWORD not set; API calls will fail." >&2
fi
