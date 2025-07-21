# NetApp DataOps Toolkit Traditional MCP Server

The NetApp DataOps Toolkit Traditional MCP Server is an open-source server component written in Python that provides access to Traditional DataOps Toolkit through the Model Context Protocol (MCP). The server provides a set of tools for managing NetApp ONTAP storage systems, including volume creation, cloning, snapshot management, and SnapMirror relationships.

>[!NOTE]
>This MCP server uses the stdio transport, as shown in the [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server), making it a "local MCP server".

### Tools

- **Create Volume**: Rapidly provision new data volumes with customizable configurations.
- **Clone Volume**: Create near-instantaneous, space-efficient clones of existing volumes using NetApp FlexClone technology.
- **List Volumes**: Retrieve a list of all existing data volumes, with optional space usage details.
- **Mount Volume**: Mount existing data volumes locally as read-only or read-write.
- **Create Snapshot**: Create space-efficient, read-only copies of data volumes for versioning and traceability.
- **List Snapshots**: Retrieve a list of all snapshots for a specific volume.
- **Create SnapMirror Relationship**: Set up SnapMirror relationships for efficient data replication.
- **List SnapMirror Relationships**: Retrieve a list of all SnapMirror relationships on the storage system.

### Prerequisites

The NetApp DataOps Toolkit for Traditional Environments requires that Python 3.8, 3.9, 3.10, or 3.11 be installed on the local host. Additionally, the toolkit requires that pip for Python3 be installed on the local host. For more details regarding pip, including installation instructions, refer to the [pip documentation](https://pip.pypa.io/en/stable/installing/).

### Installation Instructions
To install the NetApp DataOps Toolkit for Traditional Environments, run the following command.

```sh
python3 -m pip install netapp-dataops-traditional
```

### Usage

Start the MCP server:
    ```
    netapp_dataops_mcp.py
    ```

### Support

Report any issues via GitHub: https://github.com/NetApp/netapp-data-science-toolkit/issues.
