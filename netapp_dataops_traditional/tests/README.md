# NetApp DataOps Toolkit Traditional - GCNV Test Suite

This directory contains comprehensive unit tests for the NetApp DataOps Toolkit's Google Cloud NetApp Volumes (GCNV) Python modules and Model Context Protocol (MCP) server implementation. The test suite provides extensive coverage for all major operations with professional organization and robust testing patterns.

## Test Coverage Summary

### GCNV Traditional Modules: 136 tests
- **Base module**: 10 tests (utility functions)
- **Volume management**: 32 tests (create, clone, delete, list operations)
- **Snapshot management**: 47 tests (create, delete, list operations)
- **Replication management**: 47 tests (create operation with comprehensive coverage)

### MCP Server Integration: 22 tests
- **Server instantiation**: 3 tests (MCP server creation and configuration)
- **Business logic validation**: 12 tests (wrapper function testing for all operations)
- **Integration validation**: 4 tests (response format and error handling consistency)
- **Module structure**: 3 tests (import validation and logging configuration)

**Total Test Coverage: 158 tests**

## Test Files

### GCNV Traditional Module Tests (`gcnv/` directory)
- `gcnv/test_base.py`: Tests utility functions including parameter validation, serialization, and error handling
- `gcnv/test_volume_management.py`: Comprehensive tests for volume operations with professional formatting and complete coverage
- `gcnv/test_snapshot_management.py`: Enhanced test suite covering all snapshot operations with extensive validation scenarios
- `gcnv/test_replication_management.py`: Comprehensive replication tests including cross-region scenarios and schedule validation

### MCP Server Tests (`mcp/` directory)
- `mcp/test_gcnv_mcp.py`: Comprehensive test suite for the Model Context Protocol server implementation
  - **Basic Integration Tests**: Server instantiation, main function, and import validation
  - **Business Logic Tests**: Wrapper function testing using recreated logic patterns
  - **Error Handling Tests**: Comprehensive validation of error scenarios and logging
  - **Module Structure Tests**: Import validation, logging configuration, and response format consistency

## Test Organization

Each test file follows a consistent professional structure with:

### Comment Headers
```python
# =============================================================================
# MODULE OPERATION TESTS (e.g., CREATE SNAPSHOT TESTS)
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
```

### Test Categories
- **Success Cases**: All valid parameter combinations and optional arguments
- **Failure Cases**: API errors, resource not found, network failures
- **Input Validation**: Missing, empty, whitespace, and invalid type parameters
- **Edge Cases**: Boundary values, special characters, Unicode, cross-region scenarios

## Test Features

### Comprehensive Parameter Validation
- **Required Parameters**: Validates all mandatory parameters with ValueError exceptions
- **Empty String Handling**: Tests empty string validation for all required parameters  
- **Whitespace Validation**: Tests whitespace-only strings return appropriate API errors
- **Type Validation**: Ensures proper type checking (e.g., labels must be dict)

### API Error Simulation
- **Resource Not Found**: Tests handling of missing volumes, snapshots, and storage pools
- **Permission Denied**: Simulates authentication and authorization failures
- **Network Errors**: Tests connection and timeout scenarios
- **Unexpected Exceptions**: Validates graceful handling of unknown errors

### Edge Case Testing
- **Boundary Values**: Tests minimum/maximum values for numeric parameters
- **Special Characters**: Validates handling of special characters in IDs and descriptions
- **Unicode Support**: Tests Unicode character handling in resource names
- **Long Strings**: Validates behavior with very long input strings
- **Cross-Region Operations**: Tests replication across different Google Cloud regions

### Advanced Scenarios
- **Optional Parameters**: Comprehensive testing of all optional arguments
- **Schedule Validation**: Tests all valid replication schedules (HOURLY, DAILY, WEEKLY, MONTHLY)
- **Tiering Configuration**: Tests storage tiering with various cooling thresholds
- **Label Management**: Tests label assignment and validation up to Google Cloud limits

## Usage

### Run All Tests (GCNV + MCP)
```bash
cd /path/to/netapp-dataops-toolkit/netapp_dataops_traditional
python3 -m pytest tests/ -v
```

### Run GCNV Module Tests Only
```bash
# All GCNV tests
python3 -m pytest tests/gcnv/ -v

# Specific GCNV module tests
python3 -m pytest tests/gcnv/test_volume_management.py -v
python3 -m pytest tests/gcnv/test_snapshot_management.py -v
python3 -m pytest tests/gcnv/test_replication_management.py -v
python3 -m pytest tests/gcnv/test_base.py -v
```

### Run MCP Server Tests Only
```bash
# All MCP tests
python3 -m pytest tests/mcp/ -v

# Specific MCP test file
python3 -m pytest tests/mcp/test_gcnv_mcp.py -v
```

### Run Tests with Different Options
```bash
# Quick test run (no tracebacks, quiet with verbose test names)
python3 -m pytest tests/ -v --tb=no -q

# Run with coverage
python3 -m pytest tests/gcnv/ --cov=netapp_dataops.traditional.gcnv --cov-report=html

# MCP server coverage
python3 -m pytest tests/mcp/ --cov=netapp_dataops.netapp_dataops_gcnv_mcp --cov-report=html

# Complete test coverage
python3 -m pytest tests/ --cov=netapp_dataops --cov-report=html
```

## MCP Server Testing Approach

The MCP server tests use a specialized approach due to the FastMCP framework's decorator patterns:

### Business Logic Testing
Since FastMCP decorators make direct function testing complex, the test suite recreates the wrapper logic patterns to validate:
- **Function Integration**: Ensures proper integration between MCP server and GCNV modules
- **Error Handling**: Validates error logging and response formatting
- **Parameter Passing**: Tests that all parameters are correctly passed through to underlying functions
- **Response Processing**: Verifies that responses are properly formatted for MCP clients

### Testing Strategy
```python
# Example wrapper logic recreation for testing
async def create_volume_wrapper_logic(create_volume_func, logger_func, **kwargs):
    response = create_volume_func(**kwargs)
    if response['status'] == 'error':
        logger_func(f"Error creating volume: {response['message']}")
    return response
```

This approach allows comprehensive testing of:
- Success path validation
- Error handling and logging
- Parameter validation
- Response format consistency

## Test Design Principles

### Mocking Strategy
- All external Google Cloud API calls are mocked using `unittest.mock`
- Tests are completely isolated and do not require real cloud resources
- Realistic API response simulation for accurate behavior testing
- Mock configurations reflect actual Google Cloud NetApp API behavior

### Error Handling Validation
- Tests verify both error status codes and error message content
- Validates that errors are properly caught and returned in expected format
- Ensures graceful degradation for all failure scenarios

### Maintainability Features
- **REQUIRED_ARGS Constants**: Standardized test parameter sets for consistency across all test files
- **Professional Formatting**: Consistent comment headers and section organization
- **Clear Test Names**: Descriptive test function names indicating exact scenario
- **Comprehensive Documentation**: Inline comments explaining complex test scenarios

## Test File Structure

```
tests/
├── README.md                           # This file - comprehensive test documentation
├── requirements.txt                    # Test dependencies
├── gcnv/                               # GCNV traditional module tests (136 tests)
│   ├── test_base.py                    # Base utility function tests (10 tests)
│   ├── test_volume_management.py       # Volume operation tests (32 tests)
│   ├── test_snapshot_management.py     # Snapshot operation tests (47 tests)
│   └── test_replication_management.py  # Replication tests (47 tests)
└── mcp/                                # MCP server integration tests (22 tests)
    └── test_gcnv_mcp.py                # MCP server tests (22 tests)
```

## Extending the Test Suite

### Adding New Tests
1. Follow the established comment header structure
2. Use the appropriate REQUIRED_ARGS constant for parameter consistency
3. Group tests by operation and then by test category (Success, Failure, Validation, Edge)
4. Include both positive and negative test scenarios
5. Mock external dependencies appropriately

### Adding New Modules
1. Create new test file following naming convention: `test_<module_name>.py`
2. For GCNV traditional modules, place in `gcnv/` subdirectory
3. For MCP server tests, place in `mcp/` subdirectory
4. For other integration tests, place in root `tests/` directory
5. Include comprehensive coverage following the established patterns
6. Add professional comment headers and organization
7. Update this README with new test counts and descriptions

## Dependencies

### Required Python Packages
- `pytest`: Testing framework
- `unittest.mock`: For mocking Google Cloud API calls and MCP server components
- `google-cloud-netapp`: Google Cloud NetApp client library
- `fastmcp`: Model Context Protocol framework (for MCP server functionality) - **Optional**
- `mcp`: Core MCP types and utilities - **Optional**
- `asyncio`: For async function testing (MCP server tests)

**Note**: The `fastmcp` and `mcp` packages are only required for MCP server tests. GCNV traditional module tests (136 tests) will run without these dependencies.

### Test Requirements
All test dependencies are defined in `requirements.txt` in this directory

## Notes

- **Fast Execution**: All 158 tests typically complete in under 60 seconds
- **No External Dependencies**: Tests run completely offline with mocked APIs and MCP components
- **Cross-Platform**: Compatible with macOS, Linux, and Windows development environments
- **CI/CD Ready**: Designed for integration with continuous integration pipelines
- **MCP Framework Testing**: Specialized approach for testing FastMCP decorated functions through business logic validation
- **MCP Dependencies**: MCP tests require `fastmcp` and `mcp` packages. If these aren't installed, MCP tests will fail but GCNV tests will continue to work
- **Dependency Warnings**: Some harmless Marshmallow warnings may appear from NetApp ONTAP library dependencies
