import typing

from domainpy.infrastructure.transcoder import Transcoder
from domainpy.typing.infrastructure import InfrastructureMessage
from domainpy.typing.infrastructure import InfrastructureRecord


class MessageTypeNotFoundError(Exception):
    pass


class Mapper:
    def __init__(self, transcoder: Transcoder) -> None:
        self.transcoder = transcoder

        self.map: typing.Dict[str, typing.Any] = {}

    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls

    def serialize(
        self, message: InfrastructureMessage
    ) -> InfrastructureRecord:
        return typing.cast(
            InfrastructureRecord, self.transcoder.serialize(message)
        )

    def deserialize(
        self, record: InfrastructureRecord
    ) -> InfrastructureMessage:
        try:
            message_type = self.map[record.topic]
        except KeyError as error:
            raise MessageTypeNotFoundError(
                f"unable to find type {record.topic}"
            ) from error

        return self.transcoder.deserialize(record, message_type)
