from __future__ import annotations

import abc
import enum
import functools

import domainpy.compat_typing as typing

from domainpy.application.integration import IntegrationEvent
from domainpy.application.command import ApplicationCommand
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import ValueObject
from domainpy.infrastructure.records import (
    CommandRecord,
    EventRecord,
    IntegrationRecord,
    asdict,
)
from domainpy.typing.application import SystemMessage
from domainpy.typing.infrastructure import SystemRecord
from domainpy.utils.data import get_fields, Field, MISSING


def isgenerictype(objtype) -> bool:
    return typing.get_origin(objtype) is not None


class MissingCodecError(Exception):
    pass


class MissingFieldValueError(Exception):
    pass


class MessageType(enum.Enum):
    APPLICATION_COMMAND = "application_command"
    INTEGRATION_EVENT = "integration_event"
    DOMAIN_EVENT = "domain_event"


TSystemMessage = typing.TypeVar("TSystemMessage", bound=SystemMessage)
TSystemRecord = typing.TypeVar("TSystemRecord", bound=SystemRecord)


class Transcoder(abc.ABC):
    def __init__(self):
        self.codecs: typing.List[ICodec] = [
            _PrimitiveCodec(self),
            _NoneCodec(),
            _DictCodec(self),
            _SingleTypeInfiteSequenceCodec(self),
            _OptionalCodec(self),
            _ApplicationCommandCodec(self),
            _IntegrationEventCodec(self),
            _DomainEventCodec(self),
            _ValueObjectCodec(self),
        ]

    def add_codec(self, codec: ICodec) -> None:
        self.codecs.append(codec)

    def serialize(self, message: SystemMessage) -> SystemRecord:
        return typing.cast(SystemRecord, self.encode(message, type(message)))

    def deserialize(
        self, record: TSystemRecord, message_type: typing.Type[TSystemMessage]
    ) -> TSystemMessage:
        return self.decode(asdict(record), message_type)

    def encode(self, obj, objtype):
        codec = self._get_codec(objtype)
        return codec.encode(obj, objtype)

    def decode(self, data, objtype):
        codec = self._get_codec(objtype)
        return codec.decode(data, objtype)

    @functools.lru_cache(maxsize=None)
    def _get_codec(self, objtype: typing.Type) -> ICodec:
        try:
            return next(c for c in self.codecs if c.can_handle(objtype))
        except StopIteration as error:
            raise MissingCodecError(f"unknown codec for {objtype}") from error


class ICodec(abc.ABC):
    @abc.abstractmethod
    def can_handle(self, field_type: typing.Type) -> bool:
        pass

    @abc.abstractmethod
    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        pass

    @abc.abstractmethod
    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        pass


class _PrimitiveCodec(ICodec):
    def __init__(self, transcoder: Transcoder) -> None:
        self.trancoder = transcoder

    def can_handle(self, field_type: typing.Type) -> bool:
        return field_type in (str, int, float, bool)

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        return field_type(obj)

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        return field_type(data)


class _NoneCodec(ICodec):
    def can_handle(self, field_type: typing.Type) -> bool:
        return field_type is type(None)  # noqa: E721

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        return None

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        return None


class _SingleTypeInfiteSequenceCodec(ICodec):
    def __init__(self, transcoder: Transcoder) -> None:
        self.trancoder = transcoder

    def can_handle(self, field_type: typing.Type) -> bool:
        origin = typing.get_origin(field_type) or field_type
        origin_args = typing.get_args(field_type)

        return (
            origin in (list, tuple)
            and len(origin_args) == 2
            and origin_args[1] == Ellipsis
        )

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        origin_args = typing.get_args(field_type)

        return [self.trancoder.encode(o, origin_args[0]) for o in obj]

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        origin = typing.get_origin(field_type) or field_type
        origin_args = typing.get_args(field_type)

        return origin(self.trancoder.decode(o, origin_args[0]) for o in data)


class _OptionalCodec(ICodec):
    def __init__(self, transcoder: Transcoder) -> None:
        self.transcoder = transcoder

    def can_handle(self, field_type: typing.Type) -> bool:
        origin = typing.get_origin(field_type)
        origin_args = typing.get_args(field_type)

        return (  # typing.Optional[some_type]
            origin is typing.Union
            and len(origin_args) == 2
            and origin_args[1] is type(None)  # noqa: E721
        )

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        origin_args = typing.get_args(field_type)

        if obj is None:
            return None

        return self.transcoder.encode(obj, origin_args[1])

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        origin_args = typing.get_args(field_type)

        if data is None:
            return None

        return self.transcoder.decode(data, origin_args[1])


class _DictCodec(ICodec):
    def __init__(self, transcoder: Transcoder) -> None:
        self.trancoder = transcoder

    def can_handle(self, field_type: typing.Type) -> bool:
        origin = typing.get_origin(field_type) or field_type
        return origin is dict

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        origin_args = typing.get_args(field_type)

        return {
            k: self.trancoder.encode(v, origin_args[1]) for k, v in obj.items()
        }

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        origin = typing.get_origin(field_type) or field_type
        origin_args = typing.get_args(field_type)

        return origin(
            **{
                k: self.trancoder.decode(v, origin_args[1])
                for k, v in data.items()
            }
        )


class _SystemMessageCodec(ICodec):
    def __init__(self, transcoder: Transcoder) -> None:
        self.trancoder = transcoder

    def _encode(self, obj: typing.Any, field_type: typing.Type) -> dict:
        fields = get_fields(field_type)

        dct: dict[str, typing.Any] = {"payload": {}}
        for field in fields:
            field_value = getattr(obj, field.name, MISSING)
            if field_value == MISSING:
                raise MissingFieldValueError(f"missing field: {field.name}")

            encoded_value = self.trancoder.encode(field_value, field.type)
            if self._is_meta_field(field):
                dct[field.name] = encoded_value
            else:
                dct["payload"][field.name] = encoded_value

        return dct

    def _decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        fields = get_fields(field_type)

        dct = {}
        for field in fields:
            if self._is_meta_field(field):
                field_data = data.get(
                    self._get_record_field_name(field), MISSING
                )
            else:
                payload = data.get("payload", MISSING)
                if payload is MISSING:
                    raise MissingFieldValueError("missing field: payload")
                field_data = payload.get(field.name, MISSING)

            if field_data == MISSING:
                raise MissingFieldValueError(f"missing field: {field.name}")

            dct[field.name] = self.trancoder.decode(field_data, field.type)

        if 'trace_id' in data:
            dct['__trace_id__'] = data['trace_id']

        if 'context' in data:
            dct['__context__'] = data['context']

        return field_type(**dct)

    @classmethod
    def _is_meta_field(cls, field: Field) -> bool:
        return field.name.startswith("__") and field.name.endswith("__")

    @classmethod
    def _get_record_field_name(cls, field: Field) -> str:
        # Remove dunder
        # Ex. __stream_id__ to stream_id
        return field.name[2:-2]


class _ApplicationCommandCodec(_SystemMessageCodec):
    def can_handle(self, field_type: typing.Type) -> bool:
        if isgenerictype(field_type):
            return False
        return issubclass(field_type, ApplicationCommand)

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        dct = self._encode(obj, field_type)

        msg: ApplicationCommand = obj
        if msg.__trace_id__ is None:
            raise TypeError("__trace_id__ should not be None")

        record = CommandRecord(
            trace_id=msg.__trace_id__,
            topic=field_type.__name__,
            version=msg.__version__,
            timestamp=msg.__timestamp__,
            message=MessageType.APPLICATION_COMMAND.value,
            payload=dct["payload"],
        )
        return record

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        return self._decode(data, field_type)


class _IntegrationEventCodec(_SystemMessageCodec):
    def can_handle(self, field_type: typing.Type) -> bool:
        if isgenerictype(field_type):
            return False
        return issubclass(field_type, IntegrationEvent)

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        dct = self._encode(obj, field_type)

        msg: IntegrationEvent = obj
        if msg.__trace_id__ is None:
            raise TypeError("__trace_id__ should not be None")

        if msg.__context__ is None:
            raise TypeError("__context__ should not be None")

        return IntegrationRecord(
            trace_id=msg.__trace_id__,
            context=msg.__context__,
            topic=field_type.__name__,
            resolve=msg.__resolve__,
            error=msg.__error__,
            version=msg.__version__,
            timestamp=msg.__timestamp__,
            message=MessageType.INTEGRATION_EVENT.value,
            payload=dct["payload"],
        )

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        return self._decode(data, field_type)


class _DomainEventCodec(_SystemMessageCodec):
    def can_handle(self, field_type: typing.Type) -> bool:
        if isgenerictype(field_type):
            return False
        return issubclass(field_type, DomainEvent)

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        dct = self._encode(obj, field_type)

        msg: DomainEvent = obj
        if msg.__trace_id__ is None:
            raise TypeError("__trace_id__ should not be None")

        if msg.__context__ is None:
            raise TypeError("__context__ should not be None")

        return EventRecord(
            stream_id=msg.__stream_id__,
            number=msg.__number__,
            topic=field_type.__name__,
            version=msg.__version__,
            timestamp=msg.__timestamp__,
            trace_id=msg.__trace_id__,
            message=MessageType.DOMAIN_EVENT.value,
            context=msg.__context__,
            payload=dct["payload"],
        )

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        return self._decode(data, field_type)


class _ValueObjectCodec(ICodec):
    def __init__(self, transocder: Transcoder) -> None:
        self.transcoder = transocder

    def can_handle(self, field_type: typing.Type) -> bool:
        if isgenerictype(field_type):
            return False
        return issubclass(field_type, ValueObject)

    def encode(self, obj: typing.Any, field_type: typing.Type) -> typing.Any:
        fields = get_fields(field_type)

        dct = {}
        for field in fields:
            field_value = getattr(obj, field.name, MISSING)

            if field_value == MISSING:
                raise MissingFieldValueError(f"missing field: {field.name}")

            dct[field.name] = self.transcoder.encode(field_value, field.type)

        return dct

    def decode(self, data: dict, field_type: typing.Type) -> typing.Any:
        fields = get_fields(field_type)

        dct = {}
        for field in fields:
            field_data = data.get(field.name, MISSING)

            if field_data == MISSING:
                raise MissingFieldValueError(f"missing field: {field.name}")

            dct[field.name] = self.transcoder.decode(field_data, field.type)

        return field_type(**dct)
