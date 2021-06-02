"""
The NetApp Data Science Toolkit for Kubernetes is a Python library that makes it
simple for data scientists and data engineers to perform various data management
tasks within a Kubernetes cluster, such as provisioning a new Kubernetes
persistent volume or JupyterLab workspace, near-instantaneously cloning a
Kubernetes persistent volume or JupterLab workspace, and near-instantaneously
snapshotting a Kubernetes persistent volume or JupyterLab workspace for
traceability/baselining. This Python library can function as either a command
line utility or a library of functions that can be imported into any Python 
program or Jupyter Notebook.

Refer to the documentation for a full list of available functionality.

"""
DOCLINES = (__doc__ or '').split("\n")

from setuptools import setup

setup(
    long_description="\n".join(DOCLINES[0:]),
    long_description_content_type='text/markdown',
)
