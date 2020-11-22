import pytest

from .example import ExampleValueObject

@pytest.fixture
def value_object_1():
    return ExampleValueObject('a')

@pytest.fixture
def value_object_2():
    return ExampleValueObject('a')

def test_value_object_equality(value_object_1, value_object_2):
    assert value_object_1 == value_object_2

def test_value_object_immutable(value_object_1):
    with pytest.raises(Exception):
        value_object_1.something = 'b'
