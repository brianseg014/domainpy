import json
import typing
import dataclasses

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.records import CommandRecord, IntegrationRecord, EventRecord


Message = typing.TypeVar('Message', bound=typing.Union[ApplicationCommand, IntegrationEvent, DomainEvent])
Record = typing.TypeVar('Record', bound=typing.Union[CommandRecord, IntegrationRecord, EventRecord])

JsonStr = str
CommandRecordDict = typing.TypedDict('CommandRecordDict', trace_id=str, topic=str, version=int, timestamp=float, message=float, payload=dict)
IntegrationRecordDict = typing.TypedDict('IntegrationRecordDict', trace_id=str, context=str, topic=str, resolve=str, error=str, version=int, timestamp=float, message=str, payload=dict)
EventRecordDict = typing.TypedDict('EventRecordDict', stream_id=str, number=int, topic=str, version=int, timestamp=float, trace_id=str, message=str, context=str, payload=dict)
RecordDict = typing.TypeVar('RecordDict', CommandRecordDict, IntegrationRecordDict, EventRecordDict)


class ITranscoder(typing.Protocol[Message, Record, RecordDict]):

    def is_deserializable(self, 
        deserializable: typing.Union[Record, RecordDict, JsonStr],
        message_type: typing.Union[type[Message], dict[str, type[Message]]]
    ) -> bool:
        pass

    def serialize(self, message: Message) -> Record:
        pass

    def deserialize(
        self, 
        deserializable: typing.Union[Record, RecordDict, JsonStr], 
        message_type: typing.Union[type[Message], dict[str, type[Message]]]
    ) -> Message:
        pass


class CommandTranscoder(ITranscoder[ApplicationCommand, CommandRecord, CommandRecordDict]):
    message = 'command'

    def is_deserializable(
        self, 
        deserializable: typing.Union[CommandRecord, CommandRecordDict, JsonStr],
        message_type: typing.Union[type[ApplicationCommand], dict[str, type[ApplicationCommand]]]
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
        deserializable: typing.Union[CommandRecord, CommandRecordDict, JsonStr]
    ) -> CommandRecord:
        if isinstance(deserializable, JsonStr):
            deserializable = json.loads(deserializable)
        if isinstance(deserializable, dict):
            deserializable = CommandRecord(**deserializable)
        return deserializable

    
class BuiltinCommandTranscoder(CommandTranscoder):

    def serialize(self, message: ApplicationCommand) -> CommandRecord:
        record = CommandRecord(
            trace_id=message.__trace_id__,
            topic=message.__class__.__name__,
            version=message.__version__,
            timestamp=message.__timestamp__,
            message=self.message,
            payload=message.__to_dict__()
        )
        return record

    def deserialize(
        self, 
        deserializable: typing.Union[CommandRecord, CommandRecordDict, JsonStr], 
        message_type: typing.Union[type[ApplicationCommand], dict[str, type[ApplicationCommand]]]
    ) -> ApplicationCommand:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        if deserializable.message != self.message:
            raise TypeError(
                f'message is not {self.message}: found {deserializable.message}'
            )

        if deserializable.topic != message_type.__name__:
            raise TypeError(
                f'topic and message_type mismatch: {deserializable.topic}, {message_type.__name__}'
            )

        dct = {
            '__trace_id__': deserializable.trace_id,
            '__version__': deserializable.version,
            '__timestamp__': deserializable.timestamp,
            '__message__': deserializable.message
        }
        dct.update(deserializable.payload)

        return message_type.__from_dict__(dct)


class IntegrationTranscoder(ITranscoder[IntegrationEvent, IntegrationRecord, IntegrationRecordDict]):
    message = 'integration_event'

    def __init__(self, context: str):
        self.context = context

    def is_deserializable(
        self, 
        deserializable: typing.Union[IntegrationRecord, IntegrationRecordDict, JsonStr],
        message_type: typing.Union[type[IntegrationEvent], dict[str, type[IntegrationEvent]]]
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
        deserializable: typing.Union[IntegrationRecord, IntegrationRecordDict, JsonStr]
    ) -> IntegrationRecord:
        if isinstance(deserializable, JsonStr):
            deserializable = json.loads(deserializable)
        if isinstance(deserializable, dict):
            deserializable = IntegrationRecord(**deserializable)
        return deserializable
    

class BuiltinIntegrationTranscoder(IntegrationTranscoder):
    
    def serialize(self, message: IntegrationEvent) -> IntegrationRecord:
        record = IntegrationRecord(
            trace_id=message.__trace_id__,
            context=self.context,
            topic=message.__class__.__name__,
            resolve=message.__resolve__,
            version=message.__version__,
            timestamp=message.__timestamp__,
            message=self.message,
            error=message.__error__,
            payload=message.__to_dict__()
        )
        return record

    def deserialize(
        self, 
        deserializable: typing.Union[IntegrationRecord, IntegrationRecordDict, JsonStr], 
        message_type: typing.Union[type[IntegrationEvent], dict[str, type[IntegrationEvent]]]
    ) -> IntegrationEvent:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        if deserializable.message != self.message:
            raise TypeError(
                f'message is not {self.message}: found {deserializable.message}'
            )

        if deserializable.topic != message_type.__name__:
            raise TypeError(
                f'topic and message_type mismatch: {deserializable.topic}, {message_type.__name__}'
            )

        if deserializable.context != self.context:
            raise TypeError(
                f'context mismatch: {deserializable.context}, {self.context}'
            )

        dct = {
            '__trace_id__': deserializable.trace_id,
            '__resolve__': deserializable.resolve,
            '__error__': deserializable.error,
            '__version__': deserializable.version,
            '__timestamp__': deserializable.timestamp,
            '__message__': deserializable.message
        }
        dct.update(deserializable.payload)

        return message_type.__from_dict__(dct)


class EventTranscoder(ITranscoder[DomainEvent, EventRecord, EventRecordDict]):
    message = 'domain_event'

    def __init__(self, context: str):
        self.context = context

    def is_deserializable(
        self, 
        deserializable: typing.Union[EventRecord, EventRecordDict, JsonStr],
        message_type: typing.Union[type[DomainEvent], dict[str, type[DomainEvent]]]
    ) -> bool:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        return (
            deserializable.message == self.message
            and deserializable.context == self.context
            and deserializable.topic  == message_type.__name__
        )

    def get_as_record(
        self, 
        deserializable: typing.Union[EventRecord, EventRecordDict, JsonStr]
    ) -> EventRecord:
        if isinstance(deserializable, JsonStr):
            deserializable = json.loads(deserializable)
        if isinstance(deserializable, dict):
            deserializable = EventRecord(**deserializable)
        return deserializable


class BuiltinEventTranscoder(EventTranscoder):
    
    def serialize(self, message: DomainEvent) -> EventRecord:
        record = EventRecord(
            stream_id=message.__stream_id__,
            number=message.__number__,
            topic=message.__class__.__name__,
            version=message.__version__,
            timestamp=message.__timestamp__,
            trace_id=message.__trace_id__,
            message=self.message,
            context=self.context,
            payload=message.__to_dict__()
        )
        return record

    def deserialize(
        self, 
        deserializable: typing.Union[EventRecord, EventRecordDict, JsonStr], 
        message_type: typing.Union[type[DomainEvent], dict[str, type[DomainEvent]]]
    ) -> DomainEvent:
        deserializable = self.get_as_record(deserializable)

        if isinstance(message_type, dict):
            message_type = message_type[deserializable.topic]

        if deserializable.message != self.message:
            raise TypeError(
                f'message is not {self.message}: found {deserializable.message}'
            )

        if deserializable.topic != message_type.__name__:
            raise TypeError(
                f'topic and message_type misatch: {deserializable.topic}, {message_type.__name__}'
            )

        if deserializable.context != self.context:
            raise TypeError(
                f'context mismatch: {deserializable.context}, {self.context}'
            )

        dct = {
            '__stream_id__': deserializable.stream_id,
            '__number__': deserializable.number,
            '__version__': deserializable.version,
            '__timestamp__': deserializable.timestamp,
            '__trace_id__':  deserializable.trace_id,
        }
        dct.update(deserializable.payload)

        return message_type.__from_dict__(dct)
