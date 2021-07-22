import abc
import json
import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.records import (
    CommandRecord,
    EventRecord,
    IntegrationRecord,
)
from domainpy.typing.infrastructure import (  # type: ignore
    JsonStr,
    CommandRecordDict,
    IntegrationRecordDict,
    EventRecordDict,
)


TMessage = typing.TypeVar("TMessage")
TRecord = typing.TypeVar("TRecord")
TRecordDict = typing.TypeVar("TRecordDict")


class ITranscoder(typing.Generic[TMessage, TRecord, TRecordDict], abc.ABC):
    @abc.abstractmethod
    def is_deserializable(
        self,
        deserializable: typing.Union[TRecord, TRecordDict, JsonStr],
        message_type: typing.Union[
            typing.Type[TMessage], typing.Dict[str, typing.Type[TMessage]]
        ],
    ) -> bool:
        pass

    @abc.abstractmethod
    def serialize(self, message: TMessage) -> TRecord:
        pass

    @abc.abstractmethod
    def deserialize(
        self,
        deserializable: typing.Union[TRecord, TRecordDict, JsonStr],
        message_type: typing.Union[
            typing.Type[TMessage], typing.Dict[str, typing.Type[TMessage]]
        ],
    ) -> TMessage:
        pass


class TranscoderContexted(ITranscoder[TMessage, TRecord, TRecordDict]):
    def __init__(self, context: str) -> None:
        self.context = context


class CommandTranscoder(
    ITranscoder[ApplicationCommand, CommandRecord, CommandRecordDict]
):
    message = "command"

    def is_deserializable(
        self,
        deserializable: typing.Union[
            CommandRecord, CommandRecordDict, JsonStr
        ],
        message_type: typing.Union[
            typing.Type[ApplicationCommand],
            typing.Dict[str, typing.Type[ApplicationCommand]],
        ],
    ) -> bool:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        return (
            deserializable.message == self.message
            and deserializable.topic == message_type.__name__
        )

    def get_as_record(
        self,
        deserializable: typing.Union[
            CommandRecord, CommandRecordDict, JsonStr
        ],
    ) -> CommandRecord:
        if isinstance(deserializable, JsonStr):
            deserializable = json.loads(deserializable)
        if isinstance(deserializable, dict):
            deserializable = CommandRecord(**deserializable)
        return deserializable


class BuiltinCommandTranscoder(CommandTranscoder):
    def serialize(self, message: ApplicationCommand) -> CommandRecord:
        if message.__trace_id__ is None:
            raise TypeError("message.__trace_id__ should not be None")

        record = CommandRecord(
            trace_id=message.__trace_id__,
            topic=message.__class__.__name__,
            version=message.__version__,
            timestamp=message.__timestamp__,
            message=self.message,
            payload=message.__to_dict__(),
        )
        return record

    def deserialize(
        self,
        deserializable: typing.Union[
            CommandRecord, CommandRecordDict, JsonStr
        ],
        message_type: typing.Union[
            typing.Type[ApplicationCommand],
            typing.Dict[str, typing.Type[ApplicationCommand]],
        ],
    ) -> ApplicationCommand:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        if deserializable.message != self.message:
            raise TypeError(
                f"message is not {self.message}: "
                f"found {deserializable.message}"
            )

        if deserializable.topic != message_type.__name__:
            raise TypeError(
                "topic and message_type mismatch: "
                f"{deserializable.topic}, {message_type.__name__}"
            )

        dct = {
            "__trace_id__": deserializable.trace_id,
            "__version__": deserializable.version,
            "__timestamp__": deserializable.timestamp,
            "__message__": deserializable.message,
        }
        dct.update(deserializable.payload)

        return message_type.__from_dict__(dct)


class IntegrationTranscoder(
    TranscoderContexted[
        IntegrationEvent, IntegrationRecord, IntegrationRecordDict
    ]
):
    message = "integration_event"

    def is_deserializable(
        self,
        deserializable: typing.Union[
            IntegrationRecord, IntegrationRecordDict, JsonStr
        ],
        message_type: typing.Union[
            typing.Type[IntegrationEvent],
            typing.Dict[str, typing.Type[IntegrationEvent]],
        ],
    ) -> bool:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        return (
            deserializable.message == self.message
            and deserializable.context == self.context
            and deserializable.topic == message_type.__name__
        )

    def get_as_record(
        self,
        deserializable: typing.Union[
            IntegrationRecord, IntegrationRecordDict, JsonStr
        ],
    ) -> IntegrationRecord:
        if isinstance(deserializable, JsonStr):
            deserializable = json.loads(deserializable)
        if isinstance(deserializable, dict):
            deserializable = IntegrationRecord(**deserializable)
        return deserializable


class BuiltinIntegrationTranscoder(IntegrationTranscoder):
    def serialize(self, message: IntegrationEvent) -> IntegrationRecord:
        if message.__trace_id__ is None:
            raise TypeError("message.__trace_id__ should not be None")

        record = IntegrationRecord(
            trace_id=message.__trace_id__,
            context=self.context,
            topic=message.__class__.__name__,
            resolve=message.__resolve__,
            version=message.__version__,
            timestamp=message.__timestamp__,
            message=self.message,
            error=message.__error__,
            payload=message.__to_dict__(),
        )
        return record

    def deserialize(
        self,
        deserializable: typing.Union[
            IntegrationRecord, IntegrationRecordDict, JsonStr
        ],
        message_type: typing.Union[
            typing.Type[IntegrationEvent],
            typing.Dict[str, typing.Type[IntegrationEvent]],
        ],
    ) -> IntegrationEvent:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        if deserializable.message != self.message:
            raise TypeError(
                f"message is not {self.message}: "
                f"found {deserializable.message}"
            )

        if deserializable.topic != message_type.__name__:
            raise TypeError(
                "topic and message_type mismatch: "
                f"{deserializable.topic}, {message_type.__name__}"
            )

        if deserializable.context != self.context:
            raise TypeError(
                f"context mismatch: {deserializable.context}, {self.context}"
            )

        dct = {
            "__trace_id__": deserializable.trace_id,
            "__resolve__": deserializable.resolve,
            "__error__": deserializable.error,
            "__version__": deserializable.version,
            "__timestamp__": deserializable.timestamp,
            "__message__": deserializable.message,
        }
        dct.update(deserializable.payload)

        return message_type.__from_dict__(dct)


class EventTranscoder(
    TranscoderContexted[DomainEvent, EventRecord, EventRecordDict]
):
    message = "domain_event"

    def is_deserializable(
        self,
        deserializable: typing.Union[EventRecord, EventRecordDict, JsonStr],
        message_type: typing.Union[
            typing.Type[DomainEvent],
            typing.Dict[str, typing.Type[DomainEvent]],
        ],
    ) -> bool:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        return (
            deserializable.message == self.message
            and deserializable.context == self.context
            and deserializable.topic == message_type.__name__
        )

    def get_as_record(
        self,
        deserializable: typing.Union[EventRecord, EventRecordDict, JsonStr],
    ) -> EventRecord:
        if isinstance(deserializable, JsonStr):
            deserializable = json.loads(deserializable)
        if isinstance(deserializable, dict):
            deserializable = EventRecord(**deserializable)
        return deserializable


class BuiltinEventTranscoder(EventTranscoder):
    def serialize(self, message: DomainEvent) -> EventRecord:
        if message.__trace_id__ is None:
            raise TypeError("message.__trace_id__ should not be None")

        record = EventRecord(
            stream_id=message.__stream_id__,
            number=message.__number__,
            topic=message.__class__.__name__,
            version=message.__version__,
            timestamp=message.__timestamp__,
            trace_id=message.__trace_id__,
            message=self.message,
            context=self.context,
            payload=message.__to_dict__(),
        )
        return record

    def deserialize(
        self,
        deserializable: typing.Union[EventRecord, EventRecordDict, JsonStr],
        message_type: typing.Union[
            typing.Type[DomainEvent],
            typing.Dict[str, typing.Type[DomainEvent]],
        ],
    ) -> DomainEvent:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        if deserializable.message != self.message:
            raise TypeError(
                f"message is not {self.message}: "
                f"found {deserializable.message}"
            )

        if deserializable.topic != message_type.__name__:
            raise TypeError(
                "topic and message_type misatch: "
                f"{deserializable.topic}, {message_type.__name__}"
            )

        if deserializable.context != self.context:
            raise TypeError(
                f"context mismatch: {deserializable.context}, {self.context}"
            )

        dct = {
            "__stream_id__": deserializable.stream_id,
            "__number__": deserializable.number,
            "__version__": deserializable.version,
            "__timestamp__": deserializable.timestamp,
            "__trace_id__": deserializable.trace_id,
        }
        dct.update(deserializable.payload)

        return message_type.__from_dict__(dct)
