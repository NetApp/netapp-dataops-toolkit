# Azure NetApp Files (ANF) Unit Tests

This directory contains comprehensive unit tests for the Azure NetApp Files (ANF) module and MCP server implementation.

## Test Summary Statistics

### Total Test Count
- **ANF Traditional Tests**: 214 tests
- **ANF MCP Server Tests**: 28 tests  
- **Total ANF Tests**: 242 tests

### Test Breakdown by Module

#### Traditional ANF Tests (214 total)
- `test_base.py`: 36 tests - Core utility and serialization functions with advanced scenarios
- `test_client.py`: 35 tests - Azure authentication and client management with edge cases
- `test_volume_management.py`: 59 tests - Volume lifecycle operations with comprehensive scenarios  
- `test_snapshot_management.py`: 48 tests - Snapshot operations with advanced workflows
- `test_replication_management.py`: 36 tests - Cross-region replication with service levels and protocols

#### MCP Server Tests (28 total)  
- `test_anf_mcp.py`: 28 tests - Model Context Protocol server functionality

## Test Structure

The tests follow the same structure and patterns established by the GCNV tests, ensuring consistency across the codebase.

### ANF Module Tests

#### `test_base.py`
Tests for base utility functions:
- **Success Cases**: Serialization of different data types, parameter validation
- **Failure Cases**: Missing parameters, invalid inputs
- **Input Validation**: Type checking, None handling
- **Edge Cases**: Complex nested structures, Azure SDK object serialization

#### `test_volume_management.py` & `test_volume_management_comprehensive.py`
Tests for volume management operations:
- **Success Cases**: 
  - Volume creation with minimal and comprehensive parameters
  - Volume cloning from existing volumes and snapshots
  - Volume listing and retrieval
  - Volume deletion
- **Failure Cases**:
  - Resource already exists errors
  - Resource not found errors
  - Client exceptions and network errors
- **Input Validation**:
  - Missing required parameters
  - Invalid parameter types and values
  - Empty protocol types
- **Edge Cases**:
  - Boundary usage threshold values (50 GiB to 100 TiB)
  - Multiple protocol types (NFSv3, NFSv4.1, CIFS)
  - Cross-subscription operations

#### `test_snapshot_management.py`
Tests for snapshot management operations:
- **Success Cases**:
  - Snapshot creation with tags and metadata
  - Snapshot listing and retrieval
  - Volume restore from snapshots
  - Snapshot deletion
- **Failure Cases**:
  - Snapshot already exists
  - Source volume not found
  - Client exceptions
- **Input Validation**:
  - Missing snapshot names
  - Empty or None parameters
- **Edge Cases**:
  - Maximum length snapshot names (64 characters)
  - Special characters in snapshot names
  - Comprehensive tagging scenarios

#### `test_replication_management.py`
Tests for replication management operations:
- **Success Cases**:
  - Replication creation with different schedules (hourly, daily, 10-minutely)
  - Data protection volume creation
  - Replication status monitoring
  - Replication break and resync operations
- **Failure Cases**:
  - Source volume not found
  - Replication already exists
  - Invalid replication schedules
- **Input Validation**:
  - Missing destination parameters
  - Invalid schedule values
  - Empty location parameters
- **Edge Cases**:
  - Cross-subscription replication
  - Same-region replication handling
  - Disaster recovery workflows

#### `test_client.py`
Tests for Azure NetApp Files client management:
- **Success Cases**:
  - Client creation with default credentials
  - Client creation with custom credentials
  - Client caching mechanisms
- **Failure Cases**:
  - Authentication errors
  - Azure service errors
  - Network connectivity issues
- **Input Validation**:
  - Missing subscription IDs
  - Invalid subscription ID formats
- **Edge Cases**:
  - Concurrent client creation
  - Different credential types (ClientSecret, ManagedIdentity)
  - Multiple subscription handling

### ANF MCP Server Tests

#### `test_anf_mcp.py`
Tests for the ANF MCP server implementation:

##### Server Instantiation
- MCP server creation and initialization
- Tool registration verification
- Metadata and description validation

##### Business Logic Validation
- **Volume Management Tools**:
  - Create volume tool success and failure scenarios
  - Clone volume tool validation
  - List volumes tool with empty and populated results
- **Snapshot Management Tools**:
  - Create snapshot tool execution
  - List snapshots tool with various result sets
- **Replication Management Tools**:
  - Create replication tool functionality
  - Data protection volume tool testing

##### Integration Validation
- Complete volume lifecycle through MCP tools
- Snapshot lifecycle integration testing
- Disaster recovery workflow validation
- Concurrent tool execution testing

##### Module Structure
- Import validation for all dependencies
- Module structure and attribute verification
- Tool parameter validation
- Error handling consistency across tools
- Logging configuration verification

## Test Categories

### Success Cases
Each module includes comprehensive success case testing covering:
- Minimal required parameter scenarios
- Optional parameter inclusion
- Comprehensive parameter combinations
- Boundary value testing

### Failure Cases  
Systematic failure testing including:
- Resource already exists conditions
- Resource not found scenarios
- Client authentication failures
- Network and service errors
- Generic exception handling

### Input Validation
Thorough input validation covering:
- Missing required parameters
- Empty string and None value handling
- Invalid parameter types
- Parameter format validation

### Edge Cases
Advanced scenario testing including:
- Boundary values (minimum/maximum sizes)
- Cross-subscription operations
- Concurrent operation handling
- Complex data structure serialization
- Multiple protocol and service level combinations

## Integration Tests

The test suite includes integration tests that validate:
- Complete resource lifecycles (create → get → list → delete)
- Cross-module interactions
- MCP server tool orchestration
- Disaster recovery workflows
- Backup and restore scenarios

## Test Execution

Tests are designed to be executed using pytest:

```bash
# Run all ANF tests
pytest tests/anf/

# Run specific test modules
pytest tests/anf/test_volume_management.py
pytest tests/anf/test_snapshot_management.py
pytest tests/anf/test_replication_management.py
pytest tests/anf/test_base.py
pytest tests/anf/test_client.py

# Run MCP server tests
pytest tests/mcp/test_anf_mcp.py

# Run with coverage
pytest tests/anf/ --cov=netapp_dataops.traditional.anf
pytest tests/mcp/test_anf_mcp.py --cov=netapp_dataops.mcp_server.netapp_dataops_anf_mcp
```

## Mock Strategy

The tests use comprehensive mocking to:
- Isolate units under test
- Simulate Azure API responses
- Test error conditions safely
- Avoid actual Azure resource creation
- Enable fast test execution

Key mocking patterns:
- Azure NetApp Files client mocking
- Azure credential mocking
- Exception simulation
- Response object mocking
- Async function mocking for MCP tools

## Coverage Goals

The test suite aims for high coverage across:
- All public function interfaces
- Error handling paths
- Parameter validation logic
- Integration scenarios
- Edge case handling

## Consistency with GCNV Tests

The ANF tests maintain consistency with the existing GCNV test structure:
- Similar file organization and naming
- Consistent comment structure and documentation
- Matching test categorization (Success, Failure, Input Validation, Edge Cases)
- Similar mock patterns and assertions
- Equivalent integration test coverage

This ensures maintainability and makes it easy for developers familiar with the GCNV tests to work with the ANF tests.
