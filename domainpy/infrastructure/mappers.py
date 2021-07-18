import dataclasses
import typing

from domainpy.exceptions import MapperNotFoundError
from domainpy.infrastructure.transcoder import (
    ITranscoder,
    JsonStr,
    Message,
    Record,
    RecordDict,
)


class Mapper(typing.Generic[Message, Record, RecordDict]):
    def __init__(self, transcoder: ITranscoder[Message, Record, RecordDict]):
        self.transcoder = transcoder

        self.map = {}

    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls

    def is_deserializable(
        self, deserializable: typing.Union[Record, RecordDict, JsonStr]
    ) -> bool:
        return self.transcoder.is_deserializable(deserializable, self.map)

    def serialize(self, message: Message) -> Record:
        return self.transcoder.serialize(message)

    def deserialize(
        self, deserializable: typing.Union[Record, RecordDict, JsonStr]
    ) -> Message:
        return self.transcoder.deserialize(deserializable, self.map)

    def serialize_asdict(
        self, message: Message, optimized: bool = False
    ) -> dict:
        return self.asdict(self.serialize(message), optimized)

    def asdict(self, record: Record, optimized: bool = False) -> RecordDict:
        if optimized:
            return record.__dict__
        else:
            return dataclasses.asdict(record)


class MapperSet:
    def __init__(self, mappers: tuple[Mapper]):
        self.mappers = mappers

    def is_deserializable(
        self, deserializable: typing.Union[Record, RecordDict, JsonStr]
    ) -> bool:
        return any(m.is_deserializable(deserializable) for m in self.mappers)

    def deserialize(
        self, deserializable: typing.Union[Record, RecordDict, JsonStr]
    ) -> Message:
        for m in self.mappers:
            if m.is_deserializable(deserializable):
                return m.deserialize(deserializable)
        raise MapperNotFoundError(
            f"Unable to locate a mapper for {deserializable}"
        )
