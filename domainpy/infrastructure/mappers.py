import dataclasses
import typing


from domainpy.exceptions import MapperNotFoundError
from domainpy.infrastructure.transcoder import ITranscoder
from domainpy.typing.infrastructure import JsonStr  # type: ignore


TMessage = typing.TypeVar("TMessage")
TRecord = typing.TypeVar("TRecord")
TRecordDict = typing.TypeVar("TRecordDict")


class Mapper(typing.Generic[TMessage, TRecord, TRecordDict]):
    def __init__(
        self, transcoder: ITranscoder[TMessage, TRecord, TRecordDict]
    ):
        self.transcoder = transcoder

        self.map: typing.Dict[str, typing.Any] = {}

    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls

    def is_deserializable(
        self, deserializable: typing.Union[TRecord, TRecordDict, JsonStr]
    ) -> bool:
        return self.transcoder.is_deserializable(deserializable, self.map)

    def serialize(self, message: TMessage) -> TRecord:
        return self.transcoder.serialize(message)

    def deserialize(
        self, deserializable: typing.Union[TRecord, TRecordDict, JsonStr]
    ) -> TMessage:
        return self.transcoder.deserialize(deserializable, self.map)

    def serialize_asdict(
        self, message: TMessage, optimized: bool = False
    ) -> TRecordDict:
        return self.asdict(self.serialize(message), optimized)

    def asdict(self, record: TRecord, optimized: bool = False) -> TRecordDict:
        if optimized:
            return typing.cast(TRecordDict, record.__dict__)
        else:
            return typing.cast(TRecordDict, dataclasses.asdict(record))


class MapperSet:
    def __init__(self, mappers: typing.Tuple[Mapper, ...]):
        self.mappers = mappers

    def is_deserializable(
        self, deserializable: typing.Union[TRecord, TRecordDict, JsonStr]
    ) -> bool:
        return any(m.is_deserializable(deserializable) for m in self.mappers)

    def deserialize(
        self, deserializable: typing.Union[TRecord, TRecordDict, JsonStr]
    ) -> TMessage:
        for m in self.mappers:
            if m.is_deserializable(deserializable):
                return m.deserialize(deserializable)
        raise MapperNotFoundError(
            f"Unable to locate a mapper for {deserializable}"
        )
