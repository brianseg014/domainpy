import json

from typing import Generic, TypeVar, Union, Type, Callable, get_args, get_origin

from domainpy.exceptions import MapperNotFoundError
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.records import CommandRecord, IntegrationRecord, EventRecord


MessageType = TypeVar('MessageType', bound=Union[ApplicationCommand, IntegrationEvent, DomainEvent])
RecordType = TypeVar('RecordType', bound=Union[CommandRecord, IntegrationRecord, EventRecord])

class Mapper(Generic[MessageType, RecordType]):
    __message__ = None

    def __init__(self):
        self.map = {}
        self.transformers = {}

    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls

    def add_transformer(self, message_type: Type[MessageType], transformer: Callable[[Union[RecordType, dict, str]], None]):
        self.transformers[message_type] = transformer

    def is_registered(self, topic: str) -> bool:
        return topic in self.map

    def is_deserializable(self, deserializable: Union[RecordType, dict, str]) -> bool:
        deserializable = self.make_record(deserializable)

        return (
            deserializable.message == self.__message__
            and self.is_registered(deserializable.topic)
        )
    
    def make_record(self, deserializable: Union[RecordType, dict, str]) -> RecordType:
        _, record_type = self.__get_generic_types__()
        if isinstance(deserializable, str):
            deserializable = json.loads(deserializable)
        if isinstance(deserializable, dict):
            deserializable = record_type(**deserializable)
        return deserializable

    def serialize(self, message: MessageType) -> RecordType:
        raise NotImplementedError(f'{self.__class__.__name__} should implement serialize')

    def deserialize(self, deserializable: Union[RecordType, dict, str]) -> MessageType:
        raise NotImplementedError(f'{self.__class__.__name__} should implement deserialize')

    def asdict(self, record: RecordType) -> dict:
        return record.__dict__

    def serialize_asdict(self, message: MessageType) -> dict:
        return self.asdict(self.serialize(message))

    def __class_getitem__(cls, item):
        return super().__class_getitem__(item)

    def __get_generic_types__(self):
        bases = self.__class__.__dict__.get('__orig_bases__')
        mapper_base = next(b for b in bases if get_origin(b) == Mapper)
        message_type, record_type = get_args(mapper_base)

        return message_type, record_type


class CommandMapper(Mapper[ApplicationCommand, CommandRecord]):
    __message__ = 'command'

    def serialize(self, command: ApplicationCommand) -> CommandRecord:
        record = CommandRecord(
            trace_id=command.__trace_id__,
            topic=command.__class__.__name__,
            version=command.__version__,
            timestamp=command.__timestamp__,
            message=command.__message__,
            payload=command.__to_dict__()
        )
        return record
    
    def deserialize(self, deserializable: Union[CommandRecord, dict, str]) -> ApplicationCommand:
        deserializable = self.make_record(deserializable)

        if deserializable.topic in self.transformers:
            transformer = self.transformers[deserializable.topic]
            deserializable = transformer(deserializable)
        
        command_class = self.map[deserializable.topic]
        command = command_class.__from_dict__(deserializable.payload)

        command.__dict__.update({
            '__trace_id__': deserializable.trace_id,
            '__version__': deserializable.version,
            '__timestamp__': deserializable.timestamp,
            '__message__': deserializable.message
        })

        return command
    

class IntegrationMapper(Mapper[IntegrationEvent, IntegrationRecord]):
    __message__ = 'integration_event'

    def __init__(self, context: str):
        super().__init__()

        self.context = context

    def serialize(self, integration: IntegrationEvent) -> IntegrationRecord:
        record = IntegrationRecord(
            trace_id=integration.__trace_id__,
            context=self.context,
            topic=integration.__class__.__name__,
            resolve=integration.__resolve__,
            version=integration.__version__,
            timestamp=integration.__timestamp__,
            message=integration.__message__,
            error=integration.__error__,
            payload=integration.__to_dict__()
        )
        return record
    
    def deserialize(self, deserializable: Union[IntegrationRecord, dict, str]) -> IntegrationEvent:
        deserializable = self.make_record(deserializable)

        if deserializable.topic in self.transformers:
            transformer = self.transformers[deserializable.topic]
            deserializable = transformer(deserializable)
        
        integration_class = self.map[deserializable.topic]
        integration = integration_class.__from_dict__(deserializable.payload)

        integration.__dict__.update({
            '__trace_id__': deserializable.trace_id,
            '__context__': deserializable.context,
            '__resolve__': deserializable.resolve,
            '__version__': deserializable.version,
            '__timestamp__': deserializable.timestamp,
            '__message__': deserializable.message,
            '__error__': deserializable.error
        })

        return integration


class EventMapper(Mapper[DomainEvent, EventRecord]):
    __message__ = 'domain_event'

    def __init__(self, context: str):
        super().__init__()

        self.context = context

    def serialize(self, event: DomainEvent) -> EventRecord:
        record = EventRecord(
            stream_id=event.__stream_id__,
            number=event.__number__,
            topic=event.__class__.__name__,
            version=event.__version__,
            timestamp=event.__timestamp__,
            trace_id=event.__trace_id__,
            message=event.__message__,
            context=self.context,
            payload=event.__to_dict__()
        )
        return record
    
    def deserialize(self, deserializable: Union[EventRecord, dict, str]) -> DomainEvent:
        deserializable = self.make_record(deserializable)

        if deserializable.topic in self.transformers:
            transformer = self.transformers[deserializable.topic]
            deserializable = transformer(deserializable)
        
        event_class = self.map[deserializable.topic]
        event = event_class.__from_dict__(deserializable.payload)

        event.__dict__.update({
            '__stream_id__': deserializable.stream_id,
            '__number__': deserializable.number,
            '__version__': deserializable.version,
            '__timestamp__': deserializable.timestamp,
            '__trace_id__':  deserializable.trace_id,
            '__message__': deserializable.message,
            '__context__': deserializable.context
        })

        return event


class MapperSet:

    def __init__(self, mappers: tuple[Mapper]):
        self.mappers = mappers

    def is_deserializable(self, deserializable: Union[RecordType, dict, str]) -> bool:
        return any(m.is_deserializable(deserializable) for m in self.mappers)

    def deserialize(self, deserializable: Union[RecordType, dict, str]) -> MessageType:
        for m in self.mappers:
            if m.is_deserializable(deserializable):
                return m.deserialize(deserializable)
        raise MapperNotFoundError(f'Unable to locate a mapper for {deserializable}')
    