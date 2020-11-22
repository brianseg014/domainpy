
import pytest

from .example import (
    ExampleAggregate,
    ExampleEvent,
    ExampleValueObject
)

@pytest.fixture
def value_object():
    return ExampleValueObject('a')
    
@pytest.fixture
def event(value_object):
    return ExampleEvent(value_object)


def test_aggregate_apply(event):
    a = ExampleAggregate()
    a.__apply__(event)
    assert a.mutated