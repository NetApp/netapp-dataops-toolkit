# NetApp DataOps Toolkit Traditional - ANF Test Suite

This directory contains comprehensive unit tests for the NetApp DataOps Toolkit's Azure NetApp Files (ANF) Python modules and Model Context Protocol (MCP) server implementation. The test suite provides extensive coverage for all major operations with professional organization and robust testing patterns.

## Test Coverage Summary

### ANF Traditional Modules: 236 tests
- **Base module**: 36 tests (utility functions including parameter validation, serialization, and error handling)
- **Client management**: 35 tests (Azure authentication, singleton pattern, and connection management)
- **Configuration management**: 15 tests (interactive setup, file operations, and parameter resolution)
- **Volume management**: 59 tests (create, clone, delete, list operations with Azure-specific scenarios)
- **Snapshot management**: 51 tests (create, delete, list operations with comprehensive validation)
- **Replication management**: 40 tests (cross-region replication and data protection volume creation)

### MCP Server Integration: 23 tests
- **Server instantiation**: 3 tests (MCP server creation and configuration)
- **Business logic validation**: 12 tests (wrapper function testing for all operations)
- **Integration validation**: 4 tests (response format and error handling consistency)
- **Module structure**: 4 tests (import validation and logging configuration)

**Total Test Coverage: 259 tests**

All tests are designed to be self-contained and can be run independently or as part of the complete suite.

## Test Files

### ANF Traditional Module Tests (`anf/` directory)
- `anf/test_base.py`: Tests utility functions including parameter validation, serialization, and error handling for Azure SDK objects
- `anf/test_client.py`: Comprehensive tests for Azure client authentication, singleton pattern, and connection management
- `anf/test_config.py`: Complete configuration management testing including interactive setup, file operations, and parameter resolution
- `anf/test_volume_management.py`: Complete volume operations testing with professional formatting and boundary conditions
- `anf/test_snapshot_management.py`: Enhanced snapshot test suite covering all snapshot operations with Azure-specific scenarios
- `anf/test_replication_management.py`: Cross-region replication tests including data protection volume creation and authorization

### MCP Server Tests (`mcp/` directory)
- `mcp/test_anf_mcp.py`: Comprehensive test suite for the Model Context Protocol server implementation
  - **Basic Integration Tests**: Server instantiation, main function, and import validation
  - **Business Logic Tests**: Wrapper function testing using recreated logic patterns for ANF operations
  - **Error Handling Tests**: Comprehensive validation of Azure-specific error scenarios and logging
  - **Module Structure Tests**: Import validation, logging configuration, and response format consistency


## Test Organization

Each test file follows a consistent professional structure with:

### Comment Headers
```python
# =============================================================================
# MODULE OPERATION TESTS (e.g., CREATE VOLUME TESTS)
# =============================================================================

# -----------------------------------------------------------------------------
# Success Cases
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Failure Cases  
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------
```

### Test Categories
- **Success Cases**: All valid parameter combinations and optional arguments
- **Failure Cases**: Azure API errors, resource not found, authentication failures
- **Input Validation**: Missing, empty, whitespace, and invalid type parameters
- **Edge Cases**: Boundary values, special characters, Unicode, cross-region scenarios

## Test Features

### Comprehensive Parameter Validation
- **Required Parameters**: Validates all mandatory Azure resource parameters with TypeError/ValueError exceptions
- **Empty String Handling**: Tests empty string validation for all required parameters
- **Whitespace Validation**: Tests whitespace-only strings return appropriate Azure API errors
- **Type Validation**: Ensures proper type checking (e.g., tags must be dict, protocol_types must be list)

### Azure API Error Simulation
- **Resource Not Found**: Tests handling of missing volumes, snapshots, accounts, and pools
- **Authentication Errors**: Simulates Azure credential and permission failures
- **Resource Exists**: Tests handling of duplicate resource creation attempts
- **Network Errors**: Tests Azure service connection and timeout scenarios
- **Quota Exceeded**: Validates handling of Azure subscription limits and quotas

### Edge Case Testing
- **Boundary Values**: Tests minimum/maximum values for usage thresholds and sizes
- **Special Characters**: Validates handling of special characters in resource names and tags
- **Unicode Support**: Tests Unicode character handling in Azure resource metadata
- **Long Strings**: Validates behavior with very long input strings for descriptions and labels
- **Cross-Region Operations**: Tests replication across different Azure regions
- **Cross-Subscription**: Tests operations across different Azure subscriptions

### Advanced ANF-Specific Scenarios
- **Service Levels**: Comprehensive testing of Standard, Premium, and Ultra service levels
- **Protocol Types**: Tests NFSv3, NFSv4.1, SMB, and dual-protocol configurations
- **Availability Zones**: Tests zone-specific deployments and zone-redundant configurations
- **Data Protection**: Tests backup policies and cross-region replication setups
- **Capacity Pools**: Tests capacity pool management and volume placement
- **Snapshot Policies**: Tests automated snapshot scheduling and retention policies

## Usage

### Run All Tests (ANF + MCP)
```bash
cd /path/to/netapp-dataops-toolkit/netapp_dataops_traditional
python3 -m pytest tests/ -v
```

### Run ANF Module Tests Only
```bash
# All ANF tests
python3 -m pytest tests/anf/ -v

# Specific ANF module tests
python3 -m pytest tests/anf/test_volume_management.py -v
python3 -m pytest tests/anf/test_snapshot_management.py -v
python3 -m pytest tests/anf/test_replication_management.py -v
python3 -m pytest tests/anf/test_client.py -v
python3 -m pytest tests/anf/test_config.py -v
python3 -m pytest tests/anf/test_base.py -v
```

### Run MCP Server Tests Only
```bash
# All MCP tests
python3 -m pytest tests/mcp/ -v

# Specific MCP test file
python3 -m pytest tests/mcp/test_anf_mcp.py -v
```

### Run Tests with Different Options
```bash
# Quick test run (no tracebacks, quiet with verbose test names)
python3 -m pytest tests/ -v --tb=no -q

# Run with coverage
python3 -m pytest tests/anf/ --cov=netapp_dataops.traditional.anf --cov-report=html

# MCP server coverage
python3 -m pytest tests/mcp/ --cov=netapp_dataops.mcp_server.netapp_dataops_anf_mcp --cov-report=html

# Complete test coverage
python3 -m pytest tests/ --cov=netapp_dataops --cov-report=html
```

## MCP Server Testing Approach

The MCP server tests use a specialized approach due to the FastMCP framework's decorator patterns:

### Business Logic Testing
Since FastMCP decorators make direct function testing complex, the test suite recreates the wrapper logic patterns to validate:
- **Function Integration**: Ensures proper integration between MCP server and ANF modules
- **Azure Error Handling**: Validates Azure-specific error logging and response formatting
- **Parameter Passing**: Tests that all Azure resource parameters are correctly passed through
- **Response Processing**: Verifies that Azure API responses are properly formatted for MCP clients

### Testing Strategy
```python
# Example wrapper logic recreation for testing Azure operations
async def create_volume_wrapper_logic(create_volume_func, logger_func, **kwargs):
    response = create_volume_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error creating ANF volume: {response['message']}")
    return response
```

This approach allows comprehensive testing of:
- Azure success path validation
- Azure-specific error handling and logging
- ANF parameter validation
- Azure API response format consistency

## Test Design Principles

### Mocking Strategy
- All external Azure NetApp Files API calls are mocked using `unittest.mock`
- Tests are completely isolated and do not require real Azure resources or credentials
- Realistic Azure API response simulation for accurate behavior testing
- Mock configurations reflect actual Azure NetApp Files REST API behavior

### Azure Error Handling Validation
- Tests verify both Azure error status codes and error message content
- Validates that Azure-specific errors are properly caught and returned in expected format
- Ensures graceful degradation for all Azure service failure scenarios
- Tests authentication failures, quota exceeded, and resource conflicts

### Maintainability Features
- **REQUIRED_ARGS Constants**: Standardized test parameter sets for ANF resource consistency
- **Professional Formatting**: Consistent comment headers and section organization
- **Clear Test Names**: Descriptive test function names indicating exact Azure scenario
- **Comprehensive Documentation**: Inline comments explaining complex Azure-specific test scenarios

## Test File Structure

```
tests/
├── anf_tests_readme.md                # This file - comprehensive ANF test documentation
├── requirements.txt                   # Test dependencies
├── anf/                               # ANF traditional module tests (236 tests)
│   ├── test_base.py                   # Base utility function tests (36 tests)
│   ├── test_client.py                 # Azure client management tests (35 tests)
│   ├── test_config.py                 # Configuration management tests (15 tests)
│   ├── test_volume_management.py      # Volume operation tests (59 tests)
│   ├── test_snapshot_management.py    # Snapshot operation tests (51 tests)
│   └── test_replication_management.py # Replication tests (40 tests)
└── mcp/                               # MCP server integration tests (23 tests)
    └── test_anf_mcp.py                # ANF MCP server tests (23 tests)
```

## Extending the Test Suite

### Adding New Tests
1. Follow the established comment header structure with ANF-specific sections
2. Use the appropriate REQUIRED_ARGS constant for Azure parameter consistency
3. Group tests by operation and then by test category (Success, Failure, Validation, Edge)
4. Include both positive and negative test scenarios with Azure-specific error handling
5. Mock Azure API dependencies appropriately with realistic response simulation

### Adding New ANF Modules
1. Create new test file following naming convention: `test_<module_name>.py`
2. For ANF traditional modules, place in `anf/` subdirectory
3. For MCP server tests, place in `mcp/` subdirectory
4. For other integration tests, place in root `tests/` directory
5. Include comprehensive coverage following established ANF patterns
6. Add professional comment headers with Azure-specific organization
7. Update this README with new test counts and descriptions

## Dependencies

### Required Python Packages
- `pytest`: Testing framework
- `unittest.mock`: For mocking Azure NetApp Files API calls and MCP server components
- `azure-mgmt-netapp`: Azure NetApp Files management client library
- `azure-identity`: Azure authentication library for credential testing
- `azure-core`: Azure core library for exception handling
- `fastmcp`: Model Context Protocol framework (for MCP server functionality) - **Optional**
- `mcp`: Core MCP types and utilities - **Optional**
- `asyncio`: For async function testing (MCP server tests)

**Note**: The `fastmcp` and `mcp` packages are only required for MCP server tests. ANF traditional module tests (236 tests) will run without these dependencies.

### Test Requirements
All test dependencies are defined in `requirements.txt` in this directory

## Notes

- **Fast Execution**: All 259 tests typically complete in under 90 seconds
- **No External Dependencies**: Tests run completely offline with mocked Azure APIs and MCP components
- **Cross-Platform**: Compatible with macOS, Linux, and Windows development environments
- **CI/CD Ready**: Designed for integration with continuous integration pipelines
- **MCP Framework Testing**: Specialized approach for testing FastMCP decorated functions through business logic validation
- **MCP Dependencies**: MCP tests require `fastmcp` and `mcp` packages. If these aren't installed, MCP tests will fail but ANF tests will continue to work
- **Dependency Warnings**: Some harmless Marshmallow warnings may appear from NetApp ONTAP library dependencies
