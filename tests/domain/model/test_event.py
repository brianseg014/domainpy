import pytest 

from .example import (
    ExampleValueObject,
    ExampleEvent
)

@pytest.fixture
def value_object():
    return ExampleValueObject('a')
    
@pytest.fixture
def event(value_object):
    return ExampleEvent(something=value_object)
    
def test_event_property_acccess(event, value_object):
    assert event.something.__class__ is ExampleValueObject
    assert event.something == value_object
