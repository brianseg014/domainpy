import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.exceptions import DomainError

ApplicationMessage = typing.Union[
    ApplicationCommand, IntegrationEvent, DomainEvent, DomainError
]
SingleOrSequenceOfApplicationMessage = typing.Union[
    ApplicationMessage, typing.Sequence[ApplicationMessage]
]
