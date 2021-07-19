from domainpy.infrastructure.records import CommandRecord, EventRecord, IntegrationRecord
from domainpy.domain.model.event import DomainEvent
import pytest
from unittest import mock

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.transcoder import (
    BuiltinCommandTranscoder,
    BuiltinIntegrationTranscoder,
    BuiltinEventTranscoder
)


def test_command_serialize():
    command = ApplicationCommand(
        __timestamp__=0.0,
        some_property='x'
    )
    ct = BuiltinCommandTranscoder()
    record = ct.serialize(command)
    assert type(record) == CommandRecord
    assert record.timestamp == 0.0
    assert record.payload['some_property'] == 'x'

def test_command_deserialize():
    SomeCommand = type(
        'SomeCommand', 
        (ApplicationCommand,),
        {
            '__annotations__': {
                'some_property': str
            }
        }
    )

    record = """
    {
        "trace_id": "tid",
        "topic": "SomeCommand",
        "version": 1,
        "message": "command",
        "timestamp": 0.0,
        "payload": {
            "some_property": "x"
        }
    }
    """
    ct = BuiltinCommandTranscoder()
    command = ct.deserialize(record, SomeCommand)

    assert type(command) == SomeCommand
    assert command.__version__ == 1
    assert command.__message__ == 'command'
    assert command.__timestamp__ == 0.0
    assert command.some_property == 'x'

def test_command_deserialize_fail_on_mismatch_topic_type():
    record = """
    {
        "trace_id": "tid",
        "topic": "SomeCommand",
        "version": 1,
        "message": "command",
        "timestamp": 0.0,
        "payload": { }
    }
    """
    ct = BuiltinCommandTranscoder()
    with pytest.raises(TypeError):
        ct.deserialize(record, ApplicationCommand)

def test_command_deserialize_fail_on_mistmatch_message():
    record = """
    {
        "trace_id": "tid",
        "topic": "ApplicationCommand",
        "version": 1,
        "message": "some_bad_message",
        "timestamp": 0.0,
        "payload": { }
    }
    """
    ct = BuiltinCommandTranscoder()
    with pytest.raises(TypeError):
        ct.deserialize(record, ApplicationCommand)

def test_integration_serialize():
    command = IntegrationEvent(
        __resolve__=IntegrationEvent.Resolution.success,
        __error__=None,
        __timestamp__=0.0,
        __version__=1,
        some_property='x'
    )
    ct = BuiltinIntegrationTranscoder(context='some_context')
    record = ct.serialize(command)
    assert type(record) == IntegrationRecord
    assert record.resolve == 'success'
    assert record.error == None
    assert record.timestamp == 0.0
    assert record.version == 1
    assert record.payload['some_property'] == 'x'

def test_integration_deserialize():
    SomeIntegration = type(
        'SomeIntegration',
        (IntegrationEvent,),
        {
            '__annotations__': {
                'some_property': str
            }
        }
    )

    record = """
    {
        "trace_id": "tid",
        "topic": "SomeIntegration",
        "resolve": "success",
        "error": null,
        "context": "some_context",
        "message": "integration_event",
        "timestamp": 0.0,
        "version": 1,
        "payload": {
            "some_property": "x"
        }
    }
    """

    ct = BuiltinIntegrationTranscoder(context='some_context')
    integration = ct.deserialize(record, SomeIntegration)

    assert type(integration) == SomeIntegration
    assert integration.__resolve__ == 'success'
    assert integration.__error__ == None
    assert integration.__timestamp__ == 0.0
    assert integration.__version__ == 1
    assert integration.some_property == 'x'

def test_integration_deserialize_fail_on_mismatch_topic_type():
    record = """
    {
        "trace_id": "tid",
        "topic": "SomeIntegration",
        "resolve": "success",
        "error": null,
        "context": "some_context",
        "message": "integration_event",
        "timestamp": 0.0,
        "version": 1,
        "payload": { }
    }
    """
    ct = BuiltinIntegrationTranscoder(context='some_context')
    with pytest.raises(TypeError):
        ct.deserialize(record, IntegrationEvent)

def test_integration_deserialize_fail_on_mismatch_message():
    record = """
    {
        "trace_id": "tid",
        "topic": "IntegrationEvent",
        "resolve": "success",
        "error": null,
        "context": "some_context",
        "message": "some_bad_message",
        "timestamp": 0.0,
        "version": 1,
        "payload": { }
    }
    """
    ct = BuiltinIntegrationTranscoder(context='some_context')
    with pytest.raises(TypeError):
        ct.deserialize(record, IntegrationEvent)

def test_integration_deserialize_fail_on_mismatch_context():
    record = """
    {
        "trace_id": "tid",
        "topic": "IntegrationEvent",
        "resolve": "success",
        "error": null,
        "context": "some_other_context",
        "message": "integration_event",
        "timestamp": 0.0,
        "version": 1,
        "payload": { }
    }
    """
    ct = BuiltinIntegrationTranscoder(context='some_context')
    with pytest.raises(TypeError):
        ct.deserialize(record, IntegrationEvent)

def test_event_serialize():
    event = DomainEvent(
        __stream_id__ = 'sid',
        __number__=1,
        __timestamp__=0.0,
        __version__=1,
        some_property='x'
    )
    ct = BuiltinEventTranscoder('some_context')
    record = ct.serialize(event)

    assert type(record) == EventRecord
    assert record.stream_id == 'sid'
    assert record.number == 1
    assert record.timestamp == 0.0
    assert record.payload['some_property'] == 'x'

def test_event_deserialize():
    SomeEvent = type(
        'SomeEvent',
        (DomainEvent,),
        {
            '__annotations__': {
                'some_property': str
            }
        }
    )

    record = """
    {
        "trace_id": "tid",
        "stream_id": "sid",
        "number": 1,
        "topic": "SomeEvent",
        "context": "some_context",
        "version": 1,
        "timestamp": 0.0,
        "message": "domain_event",
        "payload": {
            "some_property": "x"
        }
    }
    """

    ct = BuiltinEventTranscoder('some_context')
    event = ct.deserialize(record, SomeEvent)

    assert event.__stream_id__ == 'sid'
    assert event.__number__ == 1
    assert type(event) == SomeEvent
    assert event.__version__ == 1
    assert event.__timestamp__ == 0.0
    assert event.some_property == 'x'

def test_event_deserialize_fail_on_mismatch_topic_type():
    record = """
    {
        "trace_id": "tid",
        "stream_id": "sid",
        "number": 1,
        "topic": "SomeEvent",
        "context": "some_context",
        "version": 1,
        "timestamp": 0.0,
        "message": "domain_event",
        "payload": { }
    }
    """

    ct = BuiltinEventTranscoder('some_context')
    with pytest.raises(TypeError):
        ct.deserialize(record, DomainEvent)

def test_event_deserialize_fail_on_mismatch_message():
    record = """
    {
        "trace_id": "tid",
        "stream_id": "sid",
        "number": 1,
        "topic": "DomainEvent",
        "context": "some_context",
        "version": 1,
        "timestamp": 0.0,
        "message": "some_bad_message",
        "payload": { }
    }
    """

    ct = BuiltinEventTranscoder('some_context')
    with pytest.raises(TypeError):
        event = ct.deserialize(record, DomainEvent)

def test_event_deserialize_fail_on_mismatch_context():
    record = """
    {
        "trace_id": "tid",
        "stream_id": "sid",
        "number": 1,
        "topic": "DomainEvent",
        "context": "some_other_context",
        "version": 1,
        "timestamp": 0.0,
        "message": "domain_event",
        "payload": { }
    }
    """

    ct = BuiltinEventTranscoder('some_context')
    with pytest.raises(TypeError):
        ct.deserialize(record, DomainEvent)
