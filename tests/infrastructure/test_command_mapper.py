import time
import uuid
import json

from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.mappers import CommandMapper
from domainpy.infrastructure.records import CommandRecord


def test_command_serialize():
    mapper = CommandMapper()

    @mapper.register
    class BasicCommand(ApplicationCommand):
        __version__ = 1
        some_property: str

    trace_id = uuid.uuid4()
    timestamp = time.time()
    c = BasicCommand(
        __trace_id__=trace_id,
        __timestamp__=timestamp,
        some_property='x'
    )
    rec = mapper.serialize(c)

    assert rec.topic == BasicCommand.__name__
    assert rec.version == 1
    assert rec.timestamp == timestamp
    assert rec.message == 'command'
    assert json.dumps(rec.payload) == json.dumps({ 'some_property': 'x' })

def test_command_deserialize_from_record():
    mapper = CommandMapper()

    @mapper.register
    class BasicCommand(ApplicationCommand):
        __version__ = 1
        some_property: str

    trace_id = str(uuid.uuid4())
    timestamp = time.time()
    rec = CommandRecord(
        trace_id=trace_id,
        topic=BasicCommand.__name__,
        version=1,
        timestamp=timestamp,
        message=CommandMapper.__message__,
        payload={ 'some_property': 'x' }
    )

    command = mapper.deserialize(rec)

    assert command.__trace_id__ == trace_id
    assert command.__class__ == BasicCommand
    assert command.__version__ == 1
    assert command.__timestamp__ == timestamp
    assert command.__message__ == CommandMapper.__message__
    assert command.some_property == 'x'

def test_command_make_record_from_dict():
    mapper = CommandMapper()

    @mapper.register
    class BasicCommand(ApplicationCommand):
        __version__ = 1
        some_property: str

    trace_id = str(uuid.uuid4())
    timestamp = time.time()
    deserializable = {
        'trace_id': trace_id,
        'topic': BasicCommand.__name__,
        'version': 1,
        'timestamp': timestamp,
        'message': CommandMapper.__message__,
        'payload': { 'some_property': 'x' }
    }

    rec = mapper.make_record(deserializable)

    assert rec.topic == BasicCommand.__name__
    assert rec.version == 1
    assert rec.timestamp == timestamp
    assert rec.message == CommandMapper.__message__
    assert json.dumps(rec.payload) == json.dumps({ 'some_property': 'x' })

def test_command_make_record_from_json():
    mapper = CommandMapper()

    @mapper.register
    class BasicCommand(ApplicationCommand):
        __version__ = 1
        some_property: str

    trace_id = str(uuid.uuid4())
    timestamp = time.time()
    deserializable = json.dumps({
        'trace_id': trace_id,
        'topic': BasicCommand.__name__,
        'version': 1,
        'timestamp': timestamp,
        'message': CommandMapper.__message__,
        'payload': { 'some_property': 'x' }
    })

    rec = mapper.make_record(deserializable)

    assert rec.topic == BasicCommand.__name__
    assert rec.version == 1
    assert rec.timestamp == timestamp
    assert rec.message == CommandMapper.__message__
    assert json.dumps(rec.payload) == json.dumps({ 'some_property': 'x' })
