# JupyterLab image with NetApp DataOps Toolkit (Dataset Manager) pre-installed.
#
# Build (from this directory):
#   docker build -t <registry>/jupyterlab-dataset-manager:latest .
#
# ONTAP TLS certificate is supplied at runtime via ConfigMap (not baked into the image).
# See README.md in this directory.
FROM quay.io/jupyter/scipy-notebook:python-3.11

USER root

# Dataset Manager + a file-based keyring backend for container startup
RUN pip install --no-cache-dir \
    netapp-dataops-traditional \
    keyrings.alt

COPY netapp-dataops-start.sh /usr/local/bin/start-notebook.d/netapp-dataops.sh
RUN chmod +x /usr/local/bin/start-notebook.d/netapp-dataops.sh

USER ${NB_UID}

# PlaintextKeyring stores credentials in a file under XDG_DATA_HOME.
# The Deployment mounts an emptyDir (medium: Memory) at /run/netapp-keyring and
# sets XDG_DATA_HOME so the keyring file lives in RAM, not on persistent disk.
ENV PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring
