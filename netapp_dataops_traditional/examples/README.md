NetApp DataOps Toolkit for Traditional Environments - Examples
=========

This directory contains different examples including Jupyter Notebooks, YAML files, and other necessary code or setup information.

## Dataset Manager in JupyterLab on Kubernetes

[jupyterlab-k8s/](jupyterlab-k8s)

Deploy JupyterLab on Kubernetes with Dataset Manager pre-installed. The guide covers building a custom container image, mounting the Dataset Manager root volume via PVC, injecting ONTAP credentials through a memory-backed keyring, and supplying the ONTAP TLS certificate via ConfigMap.

## Dataset-to-model Traceability using MLflow with Keras

[dotk_mlflow_keras_demo.ipynb](dotk_mlflow_keras_demo.ipynb)

In this example we demonstrate an AI workflow in a Jupyter Notebook using Keras and MLflow. This notebook's goal is to give you an understanding of how to use the DataOps Toolkit with MLFlow for dataset-to-model traceability.
