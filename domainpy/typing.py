import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.exceptions import DomainError
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.records import (
    CommandRecord,
    IntegrationRecord,
    EventRecord,
)

ApplicationMessage = typing.Union[ApplicationCommand, IntegrationEvent]
DomainMessage = typing.Union[DomainEvent, DomainError]
SystemMessage = typing.Union[ApplicationCommand, IntegrationEvent, DomainEvent]

Message = typing.TypeVar(
    "Message",
    bound=typing.Union[ApplicationCommand, IntegrationEvent, DomainEvent],
)
Record = typing.TypeVar(
    "Record", bound=typing.Union[CommandRecord, IntegrationRecord, EventRecord]
)

JsonStr = str
CommandRecordDict = typing.TypedDict(
    "CommandRecordDict",
    trace_id=str,
    topic=str,
    version=int,
    timestamp=float,
    message=float,
    payload=dict,
)
IntegrationRecordDict = typing.TypedDict(
    "IntegrationRecordDict",
    trace_id=str,
    context=str,
    topic=str,
    resolve=str,
    error=str,
    version=int,
    timestamp=float,
    message=str,
    payload=dict,
)
EventRecordDict = typing.TypedDict(
    "EventRecordDict",
    stream_id=str,
    number=int,
    topic=str,
    version=int,
    timestamp=float,
    trace_id=str,
    message=str,
    context=str,
    payload=dict,
)
RecordDict = typing.TypeVar(
    "RecordDict", CommandRecordDict, IntegrationRecordDict, EventRecordDict
)
