import dataclasses
import typing

from domainpy.infrastructure.transcoder import Transcoder
from domainpy.typing.application import SystemMessage
from domainpy.typing.infrastructure import SystemRecord, SystemRecordDict


class MessageTypeNotFoundError(Exception):
    pass


TSystemMessage = typing.TypeVar("TSystemMessage", bound=SystemMessage)
TSystemRecord = typing.TypeVar("TSystemRecord", bound=SystemRecord)
TSystemRecordDict = typing.TypeVar("TSystemRecordDict", bound=SystemRecordDict)


class Mapper(typing.Generic[TSystemMessage, TSystemRecord, TSystemRecordDict]):
    def __init__(self, transcoder: Transcoder) -> None:
        self.transcoder = transcoder

        self.map: typing.Dict[str, typing.Any] = {}

    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls

    def serialize_asdict(self, message: TSystemMessage) -> TSystemRecordDict:
        return typing.cast(
            TSystemRecordDict, dataclasses.asdict(self.serialize(message))
        )

    def serialize(self, message: TSystemMessage) -> TSystemRecord:
        return typing.cast(TSystemRecord, self.transcoder.serialize(message))

    def deserialize(self, record: TSystemRecord) -> TSystemMessage:
        try:
            message_type = self.map[record.topic]
        except KeyError as error:
            raise MessageTypeNotFoundError(
                f"unable to find type {record.topic}"
            ) from error

        return self.transcoder.deserialize(record, message_type)
