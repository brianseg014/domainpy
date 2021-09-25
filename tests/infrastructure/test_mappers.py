import pytest

from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.mappers import Mapper, MessageTypeNotFoundError
from domainpy.infrastructure.transcoder import Transcoder, MessageType
from domainpy.infrastructure.records import CommandRecord


def test_mapper_serialize_command():
    command = ApplicationCommand(
        __timestamp__=0.0,
        __trace_id__='tid',
        __version__ = 1
    )
    
    mapper = Mapper(transcoder=Transcoder())
    record = mapper.serialize(command)
    
    assert isinstance(record, CommandRecord)
    assert record.trace_id == 'tid'
    assert record.topic == 'ApplicationCommand'
    assert record.version == 1
    assert record.timestamp == 0.0
    assert record.message == MessageType.APPLICATION_COMMAND.value
    assert record.payload == {}

def test_mapper_deserialize():
    record = CommandRecord(
        trace_id='tid',
        topic='ApplicationCommand',
        version=1,
        timestamp=0.0,
        message=MessageType.APPLICATION_COMMAND.value,
        payload={ }
    )

    mapper = Mapper(transcoder=Transcoder())
    mapper.register(ApplicationCommand)
    message = mapper.deserialize(record)

    assert isinstance(message, ApplicationCommand)
    assert message.__timestamp__ == 0.0
    assert message.__version__ == 1

def test_mapper_deserializer_raises_if_not_registered():
    record = CommandRecord(
        trace_id='tid',
        topic='ApplicationCommand',
        version=1,
        timestamp=0.0,
        message=MessageType.APPLICATION_COMMAND.value,
        payload={ }
    )

    mapper = Mapper(transcoder=Transcoder())

    with pytest.raises(MessageTypeNotFoundError):
        mapper.deserialize(record)
