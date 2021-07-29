from __future__ import annotations

import typing

from domainpy.domain.model.exceptions import DomainError
from domainpy.utils.bus import Bus
from domainpy.utils.bus_subscribers import (
    ApplicationServiceSubscriber,
    ProjectionSubscriber,
    PublisherSubciber,
)

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.application import SystemMessage  # type: ignore
    from domainpy.application.service import ApplicationService
    from domainpy.application.projection import Projection
    from domainpy.application.integration import IntegrationEvent
    from domainpy.domain.model.event import DomainEvent
    from domainpy.infrastructure.publishers.base import IPublisher


class ApplicationBusAdapter:
    def __init__(
        self, bus: Bus[typing.Union[SystemMessage, DomainError]]
    ) -> None:
        self.bus = bus

    def attach(self, application_service: ApplicationService) -> None:
        self.bus.attach(ApplicationServiceSubscriber(application_service))


class ProjectionBusAdapter:
    def __init__(self, bus: Bus[DomainEvent]) -> None:
        self.bus = bus

    def attach(self, projection: Projection) -> None:
        self.bus.attach(ProjectionSubscriber(projection))


PublishableMessage = typing.TypeVar(
    "PublishableMessage", bound=typing.Union["DomainEvent", "IntegrationEvent"]
)


class PublisherBusAdapter(typing.Generic[PublishableMessage]):
    def __init__(self, bus: Bus[PublishableMessage]) -> None:
        self.bus = bus

    def attach(self, publisher: IPublisher) -> None:
        self.bus.attach(PublisherSubciber(publisher))
