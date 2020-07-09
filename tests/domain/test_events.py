import pytest
from unittest.mock import Mock

from domainpy.domain.events import (
    DomainEvent,
    mutatorfor
)


class Event(DomainEvent):
    id: str
        

def test_event_with_keyword_constructor():
    e = Event(id='id')
    assert e.id == 'id'
    

def test_event_is_immutable():
    e = Event(id='id')
    with pytest.raises(AttributeError):
        e.id = 'id-2'


def test_event_equality():
    e1 = Event(id='id')
    e2 = Event(id='id')
    assert e1 == e2


def test_event_inequality():
    e1 = Event(id='id')
    e2 = Event(id='id-2')
    assert not (e1 == e2)


def test_apply_event_changes_state_with_decorator():
    mock_method = Mock()
    mutatorfor(Event)(mock_method)
    
    e1 = Event(id='id')
    e1.__mutate__(None)
    assert mock_method.called_once_with(e1)