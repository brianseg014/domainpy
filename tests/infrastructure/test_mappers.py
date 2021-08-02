
from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.infrastructure.records import CommandRecord


def test_mapper_serialize_command():
    command = ApplicationCommand(
        __timestamp__=0.0,
        __trace_id__='tid'
    )
    
    mapper = Mapper(transcoder=Transcoder())
    record = mapper.serialize(command)
    
    assert isinstance(record, CommandRecord)
    assert record.trace_id == 'tid'
    assert record.topic == 'ApplicationCommand'
    assert record.version == 1
    assert record.timestamp == 0.0
    assert record.message == 'command'
    assert record.payload == {}

def  test_mapper_deserialize():
    record = CommandRecord(
        trace_id='tid',
        topic='ApplicationCommand',
        version=1,
        timestamp=0.0,
        message='command',
        payload={ }
    )

    mapper = Mapper(transcoder=Transcoder())
    mapper.register(ApplicationCommand)
    message = mapper.deserialize(record)

    assert isinstance(message, ApplicationCommand)
    assert message.__timestamp__ == 0.0
    assert message.__version__ == 1
    assert message.__message__ == 'command'
