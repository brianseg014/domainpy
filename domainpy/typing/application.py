import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.query import ApplicationQuery
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.exceptions import DomainError

ApplicationMessage = typing.Union[
    ApplicationCommand,
    ApplicationQuery,
    IntegrationEvent,
    DomainEvent,
    DomainError,
]
SingleOrSequenceOfApplicationMessage = typing.Union[
    ApplicationMessage, typing.Sequence[ApplicationMessage]
]
