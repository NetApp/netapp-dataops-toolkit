NetApp DataOps Toolkit for Traditional Environments
=========

The NetApp DataOps Toolkit for Traditional Environments is a Python library that makes it simple for developers, data scientists, DevOps engineers, and data engineers to perform various data management tasks, such as provisioning a new data volume, near-instantaneously cloning a data volume, and near-instantaneously snapshotting a data volume for traceability/baselining. This Python library can function as either a command line utility or a library of functions that can be imported into any Python program or Jupyter Notebook. The toolkit also includes [MCP Servers](../mcp_servers.md) that expose many of the capabilities as "tools" that can be utilized by AI agents.

## Compatibility

The NetApp DataOps Toolkit for Traditional Environments supports Linux and macOS hosts.

The toolkit must be used in conjunction with a data storage system or service in order to be useful. The toolkit simplifies the performing of various data management tasks that are actually executed by the data storage system or service. In order to facilitate this, the toolkit communicates with the data storage system or service via API. The toolkit is currently compatible with the following storage systems and services:

- NetApp AFX
- NetApp AFF (running ONTAP 9.7 and above)
- NetApp FAS (running ONTAP 9.7 and above)
- Amazon FSx for NetApp ONTAP
- Google Cloud NetApp Volumes
- NetApp Cloud Volumes ONTAP (running ONTAP 9.7 and above)
- NetApp ONTAP Select (running ONTAP 9.7 and above)

## Getting Started.

If you are working with AFX, AFF, FAS, Amazon FSx for NetApp ONTAP, Cloud Volumes ONTAP, or ONTAP Select, use the [ONTAP module](docs/ontap_readme.md).

If you are working with Google Cloud NetApp Volumes, use the [GCNV module](docs/gcnv_readme.md).
