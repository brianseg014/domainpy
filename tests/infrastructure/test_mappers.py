import pytest
import dataclasses
from unittest import mock

from domainpy.infrastructure.mappers import Mapper


@dataclasses.dataclass
class Record:
    topic: str


def test_mapper_serialize_command():
    transcoder = mock.MagicMock()
    transcoder.serialize = mock.Mock()
    
    message = mock.MagicMock()
    
    mapper = Mapper(transcoder=transcoder)
    mapper.serialize(message)

    transcoder.serialize.assert_called()

def  test_mapper_deserialize():
    transcoder = mock.MagicMock()
    transcoder.serialize = mock.Mock()
    
    mapper = Mapper(transcoder=transcoder)
    mapper.register(type('Message', (mock.MagicMock,), {}))

    record = Record(topic='Message')
    mapper.deserialize(record)

    transcoder.deserialize.assert_called()
