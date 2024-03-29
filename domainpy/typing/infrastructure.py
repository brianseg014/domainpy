import domainpy.compat_typing as typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.query import ApplicationQuery
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.records import (
    CommandRecord,
    QueryRecord,
    IntegrationRecord,
    EventRecord,
)

InfrastructureMessage = typing.Union[
    ApplicationCommand, ApplicationQuery, IntegrationEvent, DomainEvent
]
SequenceOfInfrastructureMessage = typing.Sequence[InfrastructureMessage]
SingleOrSequenceOfInfrastructureMessage = typing.Union[
    InfrastructureMessage, SequenceOfInfrastructureMessage
]

InfrastructureRecord = typing.Union[
    CommandRecord, QueryRecord, IntegrationRecord, EventRecord
]

JsonStr = str
CommandRecordDict = typing.TypedDict(
    "CommandRecordDict",
    {
        "trace_id": str,
        "topic": str,
        "version": int,
        "timestamp": float,
        "message": str,
        "payload": dict,
    },
)
QueryRecordDict = typing.TypedDict(
    "QueryRecordDict",
    {
        "trace_id": str,
        "topic": str,
        "version": int,
        "timestamp": float,
        "message": str,
        "payload": dict,
    },
)
IntegrationRecordDict = typing.TypedDict(
    "IntegrationRecordDict",
    {
        "trace_id": str,
        "context": str,
        "topic": str,
        "resolve": str,
        "error": str,
        "version": int,
        "timestamp": float,
        "message": str,
        "payload": dict,
    },
)
EventRecordDict = typing.TypedDict(
    "EventRecordDict",
    {
        "stream_id": str,
        "number": int,
        "topic": str,
        "version": int,
        "timestamp": float,
        "trace_id": str,
        "message": str,
        "context": str,
        "payload": dict,
    },
)
InfrastructureRecordDict = typing.Union[
    CommandRecordDict, QueryRecordDict, IntegrationRecordDict, EventRecordDict
]
