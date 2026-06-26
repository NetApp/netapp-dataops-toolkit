# JupyterLab image with NetApp DataOps Toolkit (Dataset Manager) pre-installed.
#
# Build (from this directory):
#   1. Place your ONTAP management LIF certificate at ./ontap_cert.pem
#   2. docker build -t <registry>/jupyterlab-dataset-manager:latest .
#
# See docs/dataset_manager_jupyterlab_k8s.md for certificate download instructions.
FROM quay.io/jupyter/scipy-notebook:python-3.11

USER root

# Dataset Manager + a file-based keyring backend for container startup
RUN pip install --no-cache-dir \
    netapp-dataops-traditional \
    keyrings.alt

# ONTAP API TLS certificate (self-signed or private-CA clusters).
# Installed outside /etc/netapp-dataops so the runtime Secret mount does not hide it.
RUN mkdir -p /usr/local/share/netapp-dataops
COPY ontap_cert.pem /usr/local/share/netapp-dataops/ontap_cert.pem
RUN chmod 644 /usr/local/share/netapp-dataops/ontap_cert.pem

COPY netapp-dataops-start.sh /usr/local/bin/start-notebook.d/netapp-dataops.sh
RUN chmod +x /usr/local/bin/start-notebook.d/netapp-dataops.sh

USER ${NB_UID}

# PlaintextKeyring stores credentials in a file under XDG_DATA_HOME.
# The Deployment mounts an emptyDir (medium: Memory) at /run/netapp-keyring and
# sets XDG_DATA_HOME so the keyring file lives in RAM, not on persistent disk.
ENV PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring
