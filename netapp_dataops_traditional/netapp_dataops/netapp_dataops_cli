#!/usr/bin/env bash

export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

docker run -v /root/.netapp_dataops:/root/.netapp_dataops -v $SCRIPT_DIR/netapp_dataops_cli.py:/usr/bin/netapp_dataops_cli.py -v $SCRIPT_DIR/traditional.py:/usr/lib/python3.9/site-packages/netapp_dataops/traditional.py --privileged=true -it --rm --network=host hmarko75/netapp-data-ops /usr/bin/netapp_dataops_cli.py "$@"
