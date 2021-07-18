from typing import Union

from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.exceptions import DomainError
from domainpy.domain.model.event import DomainEvent

ApplicationMessage = Union[ApplicationCommand, IntegrationEvent]
DomainMessage = Union[DomainEvent, DomainError]
SystemMessage = Union[ApplicationMessage, DomainMessage]
