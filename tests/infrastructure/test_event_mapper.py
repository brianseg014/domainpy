import time
import uuid
import json

from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.mappers import EventMapper
from domainpy.infrastructure.records import EventRecord


def test_event_serialize():
    mapper = EventMapper('some-context')

    @mapper.register
    class BasicEvent(DomainEvent):
        some_property: str

    trace_id = uuid.uuid4()
    stream_id = uuid.uuid4()
    timestamp = time.time()
    c = BasicEvent(
        __trace_id__=trace_id,
        __stream_id__=stream_id,
        __number__=0,
        __timestamp__=timestamp,
        some_property='x'
    )
    rec = mapper.serialize(c)

    assert rec.trace_id == trace_id
    assert rec.stream_id == stream_id
    assert rec.topic == BasicEvent.__name__
    assert rec.context == 'some-context'
    assert rec.version == 1
    assert rec.timestamp == timestamp
    assert rec.message == EventMapper.__message__
    assert json.dumps(rec.payload) == json.dumps({ 'some_property': 'x' })

def test_integration_deserialize_from_record():
    mapper = EventMapper('some-context')

    @mapper.register
    class BasicEvent(DomainEvent):
        some_property: str

    trace_id = str(uuid.uuid4())
    stream_id = uuid.uuid4()
    timestamp = time.time()
    deserializable = EventRecord(
        stream_id=stream_id,
        number=0,
        topic=BasicEvent.__name__,
        version=1,
        timestamp=timestamp,
        trace_id=trace_id,
        message=EventMapper.__message__,
        context=mapper.context,
        payload={ 'some_property': 'x' }
    )

    event = mapper.deserialize(deserializable)

    assert event.__trace_id__ == trace_id
    assert event.__stream_id__ == stream_id
    assert event.__class__ == BasicEvent
    assert event.__context__ == mapper.context
    assert event.__version__ == 1
    assert event.__timestamp__ == timestamp
    assert event.__message__ == EventMapper.__message__
    assert event.some_property == 'x'

def test_integration_make_record_from_dict():
    mapper = EventMapper('some-context')

    @mapper.register
    class BasicEvent(DomainEvent):
        some_property: str

    trace_id = str(uuid.uuid4())
    stream_id = uuid.uuid4()
    timestamp = time.time()
    deserializable = {
        'stream_id': stream_id,
        'number': 0,
        'topic': BasicEvent.__name__,
        'version': 1,
        'timestamp': timestamp,
        'trace_id': trace_id,
        'message': EventMapper.__message__,
        'context': mapper.context,
        'payload': { 'some_property': 'x' }
    }

    event = mapper.deserialize(deserializable)

    assert event.__trace_id__ == trace_id
    assert event.__stream_id__ == stream_id
    assert event.__class__ == BasicEvent
    assert event.__context__ == mapper.context
    assert event.__version__ == 1
    assert event.__timestamp__ == timestamp
    assert event.__message__ == EventMapper.__message__
    assert event.some_property == 'x'

def test_integration_make_record_from_json():
    mapper = EventMapper('some-context')

    @mapper.register
    class BasicEvent(DomainEvent):
        some_property: str

    trace_id = str(uuid.uuid4())
    stream_id = str(uuid.uuid4())
    timestamp = time.time()
    deserializable = json.dumps({
        'stream_id': stream_id,
        'number': 0,
        'topic': BasicEvent.__name__,
        'version': 1,
        'timestamp': timestamp,
        'trace_id': trace_id,
        'message': EventMapper.__message__,
        'context': mapper.context,
        'payload': { 'some_property': 'x' }
    })

    event = mapper.deserialize(deserializable)

    assert event.__trace_id__ == trace_id
    assert event.__stream_id__ == stream_id
    assert event.__class__ == BasicEvent
    assert event.__context__ == mapper.context
    assert event.__version__ == 1
    assert event.__timestamp__ == timestamp
    assert event.__message__ == EventMapper.__message__
    assert event.some_property == 'x'