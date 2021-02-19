
import pytest

from .example import (
    ExampleAggregate,
    ExampleEvent,
    ExampleValueObject,
    ExampleIdentity
)

@pytest.fixture
def value_object():
    return ExampleValueObject('a')
    
@pytest.fixture
def event(value_object):
    return ExampleEvent(value_object)


def test_aggregate_apply(event):
    a = ExampleAggregate(ExampleIdentity(id="A"))
    a.__apply__(event)
    assert a.mutated

def test_aggregate_idempotent(event):
    a = ExampleAggregate(ExampleIdentity(id="A"))
    a.__route__(event)
    a.__route__(event)

    assert a.counter == 1
