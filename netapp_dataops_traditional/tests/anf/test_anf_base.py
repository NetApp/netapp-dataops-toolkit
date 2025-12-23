import pytest
from netapp_dataops.traditional.anf import base


def test_serialize_dict():
    """Test serialization of dictionary objects"""
    data = {'a': 1, 'b': 2}
    assert base._serialize(data) == data


def test_serialize_list():
    """Test serialization of list objects"""
    data = [1, 2, 3]
    assert base._serialize(data) == data


def test_serialize_none():
    """Test serialization of None values"""
    assert base._serialize(None) is None


def test_validate_required_params_success():
    """Test successful validation of required parameters"""
    # Should not raise
    base.validate_required_params(a=1, b=2)


def test_validate_required_params_missing():
    """Test validation failure with missing parameters"""
    with pytest.raises(ValueError):
        base.validate_required_params(a=1, b=None)


def test_serialize_nested_dict():
    """Test serialization of nested dictionary structures"""
    data = {'a': {'b': 2, 'c': [1, 2]}, 'd': [3, 4]}
    assert base._serialize(data) == data


def test_serialize_complex_list():
    """Test serialization of complex list with mixed types"""
    data = [{'a': 1}, {'b': [2, 3]}, 4]
    assert base._serialize(data) == data


def test_validate_required_params_empty_string():
    """Test validation failure with empty string parameters"""
    with pytest.raises(ValueError):
        base.validate_required_params(a="", b=1)


def test_validate_required_params_zero():
    """Test that zero is valid for required params"""
    # Zero is valid for required params
    base.validate_required_params(a=0, b=1)


def test_validate_required_params_wrong_type():
    """Test validation failure with None parameters"""
    with pytest.raises(ValueError):
        base.validate_required_params(a=None, b=[1, 2])


def test_serialize_azure_sdk_object():
    """Test serialization of Azure SDK objects with as_dict method"""
    class MockAzureObject:
        def as_dict(self):
            return {'mock': 'object', 'value': 123}
    
    mock_obj = MockAzureObject()
    result = base._serialize(mock_obj)
    assert result == {'mock': 'object', 'value': 123}


def test_serialize_nested_azure_objects():
    """Test serialization of nested structures containing Azure SDK objects"""
    class MockAzureObject:
        def as_dict(self):
            return {'nested': 'azure_object'}
    
    data = {
        'volumes': [MockAzureObject()],
        'metadata': {'count': 1}
    }
    
    result = base._serialize(data)
    expected = {
        'volumes': [{'nested': 'azure_object'}],
        'metadata': {'count': 1}
    }
    assert result == expected


def test_serialize_primitive_types():
    """Test serialization of primitive data types"""
    assert base._serialize("string") == "string"
    assert base._serialize(42) == 42
    assert base._serialize(3.14) == 3.14
    assert base._serialize(True) is True
    assert base._serialize(False) is False


def test_validate_required_params_multiple_missing():
    """Test validation with multiple missing parameters"""
    with pytest.raises(ValueError) as exc_info:
        base.validate_required_params(a=None, b="", c=1, d=None)
    
    error_message = str(exc_info.value)
    assert "a" in error_message
    assert "b" in error_message
    assert "d" in error_message
    assert "c" not in error_message


def test_validate_required_params_boolean_false():
    """Test that False boolean values are considered valid"""
    # False is a valid value for required params
    base.validate_required_params(enabled=False, count=0, name="test")


def test_serialize_deeply_nested_structure():
    """Test serialization of deeply nested data structures"""
    data = {
        'level1': {
            'level2': [
                {'level3': {'level4': 'deep_value'}},
                {'level3': [1, 2, 3]}
            ]
        }
    }
    assert base._serialize(data) == data


# =============================================================================
# ADVANCED SERIALIZATION TESTS
# =============================================================================

def test_serialize_unicode_strings():
    """Test serialization with Unicode characters"""
    data = {
        'chinese': '测试数据',
        'emoji': '🗃️📊',
        'arabic': 'بيانات الاختبار',
        'russian': 'тестовые данные'
    }
    result = base._serialize(data)
    assert result == data
    assert result['chinese'] == '测试数据'
    assert result['emoji'] == '🗃️📊'


def test_serialize_large_numbers():
    """Test serialization with large numeric values"""
    data = {
        'large_int': 9223372036854775807,  # Max int64
        'large_float': 1.7976931348623157e+308,  # Near max float64
        'scientific': 1.23e-10,
        'negative_large': -9223372036854775808
    }
    result = base._serialize(data)
    assert result == data


def test_serialize_special_float_values():
    """Test serialization with special float values"""
    import math
    data = {
        'zero': 0.0,
        'negative_zero': -0.0,
        'infinity': math.inf,
        'negative_infinity': -math.inf,
        'nan': math.nan
    }
    result = base._serialize(data)
    assert result['zero'] == 0.0
    assert result['negative_zero'] == -0.0
    assert math.isinf(result['infinity'])
    assert math.isinf(result['negative_infinity'])
    assert math.isnan(result['nan'])


def test_serialize_empty_containers():
    """Test serialization of empty containers"""
    data = {
        'empty_dict': {},
        'empty_list': [],
        'empty_string': '',
        'nested_empty': {
            'inner_empty': {},
            'inner_list': []
        }
    }
    result = base._serialize(data)
    assert result == data


def test_serialize_mixed_types_complex():
    """Test serialization with complex mixed type structures"""
    data = {
        'metadata': {
            'version': 1.0,
            'enabled': True,
            'tags': ['production', 'database'],
            'config': {
                'timeout': 30,
                'retries': 3,
                'endpoints': [
                    {'name': 'primary', 'url': 'https://primary.example.com'},
                    {'name': 'backup', 'url': 'https://backup.example.com'}
                ]
            }
        },
        'data': [
            {'id': 1, 'value': 'test'},
            {'id': 2, 'value': None}
        ]
    }
    result = base._serialize(data)
    assert result == data


def test_serialize_azure_response_like():
    """Test serialization of Azure-like response structures"""
    data = {
        'id': '/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.NetApp/netAppAccounts/test-account',
        'name': 'test-account',
        'type': 'Microsoft.NetApp/netAppAccounts',
        'location': 'eastus',
        'properties': {
            'provisioningState': 'Succeeded',
            'activeDirectories': [],
            'encryption': {
                'keySource': 'Microsoft.NetApp'
            }
        },
        'tags': {
            'environment': 'test',
            'team': 'devops'
        }
    }
    result = base._serialize(data)
    assert result == data

# =============================================================================
# ADVANCED VALIDATION TESTS
# =============================================================================

def test_validate_required_params_whitespace_strings():
    """Test validation with whitespace-only strings"""
    with pytest.raises(ValueError):
        base.validate_required_params(name="   ", value="test")
    
    with pytest.raises(ValueError):
        base.validate_required_params(name="\t\n  ", value="test")


def test_validate_required_params_zero_values():
    """Test that zero values are considered valid"""
    # These should all pass
    base.validate_required_params(
        count=0,
        percentage=0.0,
        index=0,
        enabled=False
    )


def test_validate_required_params_nested_validation():
    """Test validation with nested parameter structures"""
    # Test that we only validate top-level parameters
    base.validate_required_params(
        config={'nested_empty': '', 'nested_none': None},
        name="test"
    )


def test_validate_required_params_large_parameter_set():
    """Test validation with many parameters"""
    params = {f'param_{i}': f'value_{i}' for i in range(50)}
    params['valid_param'] = 'valid_value'
    
    # Should not raise
    base.validate_required_params(**params)


def test_validate_required_params_special_characters():
    """Test validation with special characters in parameter names/values"""
    base.validate_required_params(
        **{
            'param-with-dashes': 'value',
            'param_with_underscores': 'value',
            'param.with.dots': 'value',
            'normal_param': 'value-with-special-chars!@#$%'
        }
    )


def test_validate_required_params_unicode_parameters():
    """Test validation with Unicode parameter names and values"""
    base.validate_required_params(
        **{
            'name': '测试参数',
            'description': 'Test with emoji 🧪',
            'config': 'Тест кириллицей'
        }
    )


def test_validate_required_params_error_message_formatting():
    """Test that error messages are properly formatted"""
    with pytest.raises(ValueError) as exc_info:
        base.validate_required_params(
            valid_param="test",
            empty_param="",
            none_param=None,
            whitespace_param="   "
        )
    
    error_message = str(exc_info.value)
    assert "empty_param" in error_message
    assert "none_param" in error_message
    assert "whitespace_param" in error_message
    assert "valid_param" not in error_message


def test_validate_required_params_case_sensitivity():
    """Test parameter validation is case sensitive"""
    # These are different parameters
    base.validate_required_params(
        Name="test1",
        name="test2", 
        NAME="test3"
    )

# =============================================================================
# EDGE CASE AND STRESS TESTS
# =============================================================================

def test_serialize_extremely_large_structure():
    """Test serialization with very large data structures"""
    # Create a large nested structure
    data = {}
    current = data
    
    # Create 100 levels of nesting
    for i in range(100):
        current[f'level_{i}'] = {}
        current = current[f'level_{i}']
    
    # Add some data at the deepest level
    current['deep_data'] = [i for i in range(1000)]
    
    result = base._serialize(data)
    assert result == data


def test_serialize_circular_reference_safety():
    """Test that serialization handles potential circular references gracefully"""
    # Create a structure that could potentially cause issues
    data = {
        'self_reference': None,
        'data': [1, 2, 3]
    }
    data['self_reference'] = data['data']  # Reference to same list
    
    result = base._serialize(data)
    assert result == data
    # Note: Serialization creates new objects, so identity may not be preserved
    assert result['self_reference'] == result['data']  # Content equality is sufficient


def test_validate_required_params_stress_test():
    """Stress test validation with many invalid parameters"""
    invalid_params = {}
    for i in range(100):
        invalid_params[f'param_{i}'] = None if i % 2 == 0 else ""
    
    with pytest.raises(ValueError) as exc_info:
        base.validate_required_params(**invalid_params)
    
    # Should contain information about invalid parameters
    error_message = str(exc_info.value)
    assert len(error_message) > 0


def test_serialize_memory_efficiency():
    """Test that serialization doesn't create unnecessary copies"""
    original_data = {
        'large_list': list(range(10000)),
        'nested': {
            'another_list': list(range(5000))
        }
    }
    
    serialized = base._serialize(original_data)
    
    # Serialization should produce equivalent results 
    assert serialized == original_data
    assert serialized['large_list'] == original_data['large_list']


def test_validate_params_performance():
    """Test validation performance with many parameters"""
    import time
    
    # Create a large set of valid parameters
    params = {f'param_{i}': f'value_{i}' for i in range(1000)}
    
    start_time = time.time()
    base.validate_required_params(**params)
    end_time = time.time()
    
    # Validation should be fast (less than 1 second for 1000 params)
    assert end_time - start_time < 1.0


def test_serialize_concurrent_access():
    """Test serialization thread safety"""
    import threading
    import time
    
    data = {
        'counter': 0,
        'threads': []
    }
    
    results = []
    exceptions = []
    
    def serialize_thread():
        try:
            for i in range(100):
                thread_data = {
                    'thread_id': threading.current_thread().ident,
                    'iteration': i,
                    'data': data
                }
                result = base._serialize(thread_data)
                results.append(result)
        except Exception as e:
            exceptions.append(e)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=serialize_thread)
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Verify no exceptions occurred
    assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
    assert len(results) == 500  # 5 threads × 100 iterations
