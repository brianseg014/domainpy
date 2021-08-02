import sys
import pytest
import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import ValueObject
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.infrastructure.records import CommandRecord, IntegrationRecord, EventRecord


def test_serialize_command():
    class Command(ApplicationCommand):
        __trace_id__: str
        __version__: int
        __timestamp__: float
        some_property: str

    m = Command(
        __trace_id__='tid',
        __version__=1,
        __timestamp__=0.0,
        some_property='x'
    )
    
    t = Transcoder()
    r = t.serialize(m)
    assert r.payload['some_property'] == 'x'

def test_deserialize_command():
    class Command(ApplicationCommand):
        __trace_id__: str
        __version__: int
        __timestamp__: float
        some_property: str

    r = CommandRecord(
        trace_id='tid',
        topic='Command',
        version=1,
        timestamp=0.0,
        message='command',
        payload={ 'some_property': 'x' }
    )

    t = Transcoder()
    m = t.deserialize(r, Command)
    assert m.some_property == 'x'

def test_serialize_integration():
    class Integration(IntegrationEvent):
        __trace_id__: str
        __context__: str
        __resolve__: str
        __error__: typing.Optional[str]
        __version__:int
        __timestamp__: float
        some_property: str

    m = Integration(
        __trace_id__='tid',
        __context__='some_context',
        __resolve__='success',
        __error__=None,
        __version__=1,
        __timestamp__=0.0,
        some_property='x'
    )

    t = Transcoder()
    r = t.serialize(m)
    assert r.payload['some_property'] == 'x'

def test_deserialize_integration():
    class Integration(IntegrationEvent):
        some_property: str

    r = IntegrationRecord(
        trace_id='tid',
        context='some_context',
        topic='Integration',
        resolve='success',
        error=None,
        version=1,
        timestamp=0.0,
        message='integration_event',
        payload={ 'some_property': 'x' }
    )

    t = Transcoder()
    m = t.deserialize(r, Integration)
    assert m.some_property == 'x'

def test_serialize_event():
    class Attribute(ValueObject):
        some_property: str

    class Event(DomainEvent):
        __stream_id__: str
        __number__: int
        __version__: int
        __timestamp__: float
        __trace_id__: str
        __context__: str
        some_property: Attribute

    m = Event(
        __stream_id__='sid',
        __number__=1,
        __version__=1,
        __timestamp__=0.0,
        __trace_id__='tid',
        __context__='some_context',
        some_property=Attribute(some_property='x')
    )

    t = Transcoder()
    r = t.serialize(m)
    assert r.payload['some_property']['some_property'] == 'x'

def test_deserialize_event():
    class Attribute(ValueObject):
        some_property: str

    class Event(DomainEvent):
        some_property: Attribute

    r = EventRecord(
        stream_id='sid',
        number=1,
        topic='Event',
        version=1,
        timestamp=0.0,
        trace_id='tid',
        message='domain_event',
        context='some_context',
        payload={ 'some_property': { 'some_property': 'x' } }
    )

    t = Transcoder()
    m = t.deserialize(r, Event)
    assert m.some_property.some_property == 'x'

def test_encode_single_type_sequence():
    t = Transcoder()
    r = t.encode(tuple([ 'x' ]), typing.Tuple[str, ...])
    assert r == ['x',]

def test_decode_single_type_sequence():
    t = Transcoder()
    m = t.decode(tuple([ 'x' ]), typing.Tuple[str, ...])
    assert m == ('x',)

def test_encode_primitive():
    t = Transcoder()
    
    m = t.decode('x', str)
    assert m == 'x'

    m = t.decode(1, int)
    assert m == 1

    m = t.decode(1.0, int)
    assert m == 1

    m = t.decode(1.1, float)
    assert m == 1.1

    m = t.decode(1, float)
    assert m == 1.0

    m = t.decode(True, bool)
    assert m == True

def test_decode_primitive():
    t = Transcoder()
    
    m = t.encode('x', str)
    assert m == 'x'

    m = t.encode(1, int)
    assert m == 1

    m = t.encode(1.0, int)
    assert m == 1

    m = t.encode(1.1, float)
    assert m == 1.1

    m = t.encode(1, float)
    assert m == 1.0

    m = t.encode(True, bool)
    assert m == True

@pytest.mark.skipif(sys.version_info < (3,9), reason='requires python 3.9 or higher')
def test_encode_single_type_sequence_builtin():
    t = Transcoder()
    r = t.encode(tuple([ 'x' ]), tuple[str, ...])
    assert r == ['x',]

@pytest.mark.skipif(sys.version_info < (3,9), reason='requires python 3.9 or higher')
def test_decode_single_type_sequence():
    t = Transcoder()
    m = t.decode(tuple([ 'x' ]), tuple[str, ...])
    assert m == ('x',)
