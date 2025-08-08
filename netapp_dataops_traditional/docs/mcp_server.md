# NetApp DataOps Toolkit MCP Server for ONTAP

The NetApp DataOps Toolkit MCP Server for ONTAP is an open-source server component written in Python that provides access to Traditional DataOps Toolkit capabilities through the Model Context Protocol (MCP). The server provides a set of tools for managing NetApp ONTAP storage systems, including volume creation, cloning, snapshot management, and SnapMirror relationships.

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

- Python >= 3.8
- [uv](https://docs.astral.sh/uv/) or [pip](https://pypi.org/project/pip/)

### Usage Instructions

#### Run with uv (recommended)

To run the MCP server using uv, run the following command. You do not need to install the NetApp DataOps Toolkit package before running this command.

```sh
uvx --from netapp-dataops-traditional netapp_dataops_ontap_mcp.py
```

#### Install with pip and run from PATH

To install the NetApp DataOps Toolkit for Traditional Environments, run the following command.

```sh
python3 -m pip install netapp-dataops-traditional
```

After installation, the netapp_dataops_ontap_mcp.py command will be available in your PATH for direct usage.

#### Usage

A config file must be created before the NetApp Data Management Toolkit for Traditional Environments can be used to perform data management operations. For more details [click here](https://github.com/NetApp/netapp-dataops-toolkit/tree/main/netapp_dataops_traditional#getting-started).

If you do not have a config file, you can run the following command to create one.

```sh
uvx --from netapp-dataops-traditional netapp_dataops_cli.py config
```

### Support

Report any issues via GitHub: https://github.com/NetApp/netapp-dataops-toolkit/issues.
