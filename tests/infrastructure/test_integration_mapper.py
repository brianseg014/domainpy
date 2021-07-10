import time
import uuid
import json

from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.mappers import IntegrationMapper
from domainpy.infrastructure.records import IntegrationRecord


def test_integration_serialize():
    mapper = IntegrationMapper('some-context')

    @mapper.register
    class BasicIntegration(IntegrationEvent):
        __version__ = 1
        __resolve__ = IntegrationEvent.Resolution.success
        some_property: str

    trace_id = uuid.uuid4()
    timestamp = time.time()
    c = BasicIntegration(
        __trace_id__=trace_id,
        __timestamp__=timestamp,
        some_property='x'
    )
    rec = mapper.serialize(c)

    assert rec.trace_id == trace_id
    assert rec.topic == BasicIntegration.__name__
    assert rec.context == 'some-context'
    assert rec.version == 1
    assert rec.timestamp == timestamp
    assert rec.message == IntegrationMapper.__message__
    assert rec.error == None
    assert json.dumps(rec.payload) == json.dumps({ 'some_property': 'x' })

def test_integration_deserialize_from_record():
    mapper = IntegrationMapper('some-context')

    @mapper.register
    class BasicIntegration(IntegrationEvent):
        __resolve__ = IntegrationEvent.Resolution.success
        some_property: str

    trace_id = str(uuid.uuid4())
    timestamp = time.time()
    rec = IntegrationRecord(
        trace_id=trace_id,
        context=mapper.context,
        topic=BasicIntegration.__name__,
        resolve=IntegrationEvent.Resolution.success,
        version=1,
        timestamp=timestamp,
        message=IntegrationMapper.__message__,
        error=None,
        payload={ 'some_property': 'x' }
    )

    integration = mapper.deserialize(rec)

    assert integration.__trace_id__ == trace_id
    assert integration.__class__ == BasicIntegration
    assert integration.__context__ == mapper.context
    assert integration.__version__ == 1
    assert integration.__timestamp__ == timestamp
    assert integration.__message__ == IntegrationMapper.__message__
    assert integration.__error__ == None
    assert integration.some_property == 'x'

def test_integration_make_record_from_dict():
    mapper = IntegrationMapper('some-context')

    @mapper.register
    class BasicIntegration(IntegrationEvent):
        __resolve__ = IntegrationEvent.Resolution.success
        some_property: str

    trace_id = str(uuid.uuid4())
    timestamp = time.time()
    deserializable = {
        'trace_id': trace_id,
        'context': mapper.context,
        'topic': BasicIntegration.__name__,
        'resolve': IntegrationEvent.Resolution.success,
        'version': 1,
        'timestamp':timestamp,
        'message': IntegrationMapper.__message__,
        'error': None,
        'payload': { 'some_property': 'x' }
    }

    rec = mapper.make_record(deserializable)

    assert rec.trace_id == trace_id
    assert rec.context == mapper.context
    assert rec.topic == BasicIntegration.__name__
    assert rec.version == 1
    assert rec.timestamp == timestamp
    assert rec.message == IntegrationMapper.__message__
    assert rec.error == None
    assert json.dumps(rec.payload) == json.dumps({ 'some_property': 'x' })

def test_integration_make_record_from_json():
    mapper = IntegrationMapper('some-context')

    @mapper.register
    class BasicIntegration(IntegrationEvent):
        __resolve__ = IntegrationEvent.Resolution.success
        some_property: str

    trace_id = str(uuid.uuid4())
    timestamp = time.time()
    deserializable = json.dumps({
        'trace_id': trace_id,
        'context': mapper.context,
        'topic': BasicIntegration.__name__,
        'resolve': IntegrationEvent.Resolution.success,
        'version': 1,
        'timestamp':timestamp,
        'message': IntegrationMapper.__message__,
        'error': None,
        'payload': { 'some_property': 'x' }
    })

    rec = mapper.make_record(deserializable)

    assert rec.trace_id == trace_id
    assert rec.context == mapper.context
    assert rec.topic == BasicIntegration.__name__
    assert rec.version == 1
    assert rec.timestamp == timestamp
    assert rec.message == IntegrationMapper.__message__
    assert rec.error == None
    assert json.dumps(rec.payload) == json.dumps({ 'some_property': 'x' })