import typing

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent

SystemMessage = typing.Union[ApplicationCommand, IntegrationEvent, DomainEvent]
