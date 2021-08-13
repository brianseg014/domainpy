import sys
import pytest
import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import ValueObject
from domainpy.infrastructure.tracer.tracestore import TraceResolution
from domainpy.infrastructure.transcoder import Transcoder, MessageType
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
    assert isinstance(r, CommandRecord)
    assert r.trace_id == m.__trace_id__
    assert r.version == m.__version__
    assert r.timestamp == m.__timestamp__
    assert r.payload['some_property'] == 'x'

def test_deserialize_command():
    class Command(ApplicationCommand):
        class Struct(ApplicationCommand.Struct):
            some_property: str

        __trace_id__: str
        __version__: int = 1
        __timestamp__: float
        some_property: Struct

    r = CommandRecord(
        trace_id='tid',
        topic='Command',
        version=1,
        timestamp=0.0,
        message=MessageType.APPLICATION_COMMAND.value,
        payload={ 'some_property': { 'some_property': 'x' } }
    )

    t = Transcoder()
    m = t.deserialize(r, Command)
    assert isinstance(m, Command)
    assert m.__trace_id__ == r.trace_id
    assert m.__version__ == r.version
    assert m.__timestamp__ == r.timestamp
    assert m.some_property.some_property == 'x'

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
    assert isinstance(r, IntegrationRecord)
    assert r.trace_id == m.__trace_id__
    assert r.context == m.__context__
    assert r.resolve == m.__resolve__
    assert r.error == m.__error__
    assert r.version == m.__version__
    assert r.timestamp == m.__timestamp__
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
        message=MessageType.INTEGRATION_EVENT.value,
        payload={ 'some_property': 'x' }
    )

    t = Transcoder()
    m = t.deserialize(r, Integration)
    assert isinstance(m, Integration)
    assert m.__trace_id__ == r.trace_id
    assert m.__context__ == r.context
    assert m.__resolve__ == r.resolve
    assert m.__error__ == r.error
    assert m.__version__ == r.version
    assert m.__timestamp__ == r.timestamp
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
    assert isinstance(r, EventRecord)
    assert r.stream_id == m.__stream_id__
    assert r.number == m.__number__
    assert r.version == m.__version__
    assert r.timestamp == m.__timestamp__
    assert r.trace_id == m.__trace_id__
    assert r.context == m.__context__
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
        message=MessageType.DOMAIN_EVENT.value,
        context='some_context',
        payload={ 'some_property': { 'some_property': 'x' } }
    )

    t = Transcoder()
    m = t.deserialize(r, Event)
    assert isinstance(m, Event)
    assert m.__stream_id__ == r.stream_id
    assert m.__number__ == r.number
    assert m.__version__ == r.version
    assert m.__timestamp__ == r.timestamp
    assert m.__trace_id__ == r.trace_id
    assert m.__context__ == r.context
    assert m.some_property.some_property == 'x'

def test_serialize_trace_resolution():
    m = TraceResolution(
        trace_id='tid',
        resolution='success'
    )

    t = Transcoder()
    r = t.serialize(m)
    assert r == m

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
