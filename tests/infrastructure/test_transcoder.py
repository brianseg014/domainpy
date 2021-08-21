import sys
import pytest
import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import ValueObject
from domainpy.infrastructure.tracer.tracestore import TraceResolution
from domainpy.infrastructure.transcoder import Transcoder, MessageType, MissingCodecError, MissingFieldValueError, ICodec, record_fromdict
from domainpy.infrastructure.records import CommandRecord, IntegrationRecord, EventRecord

def test_serialize_command():
    class Command(ApplicationCommand):
        class Struct(ApplicationCommand.Struct):
            some_property: str

        __trace_id__: str
        __version__: int = 1
        __timestamp__: float
        some_property: Struct

    m = Command(
        __trace_id__='tid',
        __version__=1,
        __timestamp__=0.0,
        some_property=Command.Struct(
            some_property='x'
        )
    )
    
    t = Transcoder()
    r = t.serialize(m)
    assert isinstance(r, CommandRecord)
    assert r.trace_id == m.__trace_id__
    assert r.version == m.__version__
    assert r.timestamp == m.__timestamp__
    assert r.payload['some_property'] == { 'some_property': 'x' }

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

def test_encode_optional():
    t = Transcoder()

    r = t.encode('text', typing.Optional[str])
    assert r == 'text'

    r = t.encode(None, typing.Optional[str])
    assert r == None

def test_decode_optional():
    t = Transcoder()

    r = t.decode('text', typing.Optional[str])
    assert r == 'text'

    r = t.decode(None, typing.Optional[str])
    assert r == None

def test_encode_none():
    t = Transcoder()
    assert t.encode(None, type(None)) is None
    
def test_decode_none():
    t = Transcoder()
    assert t.decode(None, type(None)) is None

def test_encode_dict():
    t = Transcoder()

    r = t.encode({ '0': 'True' }, typing.Dict[int, bool])
    assert r == { 0: True }

def test_decode_dict():
    t = Transcoder()

    r = t.decode({ '0': 'True' }, typing.Dict[int, bool])
    assert r == { 0: True }

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

def test_unknown_codec_raises():
    class UnknownType:
        pass

    t = Transcoder()
    with pytest.raises(MissingCodecError):
        t.encode(None, UnknownType)

def test_add_new_codec():
    NewType = type('NewType', (), {})

    class NewTypeCodec(ICodec):
        def can_handle(self, field_type: typing.Type) -> bool:
            return field_type is NewType

        def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
            return True

        def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
            return True

    t = Transcoder()
    t.add_codec(NewTypeCodec())

    assert t.encode(NewType(), NewType)
    assert t.decode({}, NewType)

def test_command_record_fromdict():
    dct = {
        'trace_id': 'tid',
        'topic': 'ApplicationCommand',
        'timestamp': 0.0,
        'version': 1,
        'message': MessageType.APPLICATION_COMMAND.value,
        'payload': { }
    }
    r = record_fromdict(dct)
    assert isinstance(r, CommandRecord)

def test_integraton_record_fromdict():
    dct = {
        'trace_id': 'tid',
        'topic': 'IntegrationEvent',
        'timestamp': 0.0,
        'version': 1,
        'resolve': 'success',
        'error': None,
        'context': 'some_context',
        'message': MessageType.INTEGRATION_EVENT.value,
        'payload': { }
    }
    r = record_fromdict(dct)
    assert isinstance(r, IntegrationRecord)

def test_event_record_fromdict():
    dct = {
        'stream_id': 'sid',
        'number': 0,
        'topic': 'DomainEvent',
        'trace_id': 'tid',
        'timestamp': 0.0,
        'version': 1,
        'context': 'some_context',
        'message': MessageType.DOMAIN_EVENT.value,
        'payload': { }
    }
    r = record_fromdict(dct)
    assert isinstance(r, EventRecord)

def test_record_fromdict_raises():
    dct = {
        'message': 'unknown message'
    }

    with pytest.raises(ValueError):
        record_fromdict(dct)

def test_message_type_of():
    UnknownType = type('UnknownType', (), {})

    Command = type('Command', (ApplicationCommand,), {})
    Integration = type('Integration', (IntegrationEvent,), {})
    Event = type('Event', (DomainEvent,), {})

    assert MessageType.of(Command) == MessageType.APPLICATION_COMMAND
    assert MessageType.of(Integration) == MessageType.INTEGRATION_EVENT
    assert MessageType.of(Event) == MessageType.DOMAIN_EVENT

    with pytest.raises(TypeError):
        MessageType.of(UnknownType)