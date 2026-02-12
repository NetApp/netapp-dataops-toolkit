import pytest
from netapp_dataops.traditional.gcnv import base


def test_serialize_dict():
    data = {'a': 1, 'b': 2}
    assert base._serialize(data) == data


def test_serialize_list():
    data = [1, 2, 3]
    assert base._serialize(data) == data


def test_serialize_none():
    assert base._serialize(None) is None


def test_validate_required_params_success():
    # Should not raise
    base.validate_required_params(a=1, b=2)


def test_validate_required_params_missing():
    with pytest.raises(ValueError):
        base.validate_required_params(a=1, b=None)


def test_serialize_nested_dict():
    data = {'a': {'b': 2, 'c': [1, 2]}, 'd': [3, 4]}
    assert base._serialize(data) == data


def test_serialize_complex_list():
    data = [{'a': 1}, {'b': [2, 3]}, 4]
    assert base._serialize(data) == data


def test_validate_required_params_empty_string():
    with pytest.raises(ValueError):
        base.validate_required_params(a="", b=1)


def test_validate_required_params_zero():
    # Zero is valid for required params
    base.validate_required_params(a=0, b=1)


def test_validate_required_params_wrong_type():
    with pytest.raises(ValueError):
        base.validate_required_params(a=None, b=[1, 2])
