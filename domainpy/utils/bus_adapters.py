from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from domainpy.typing import SystemMessage
    from domainpy.application.service import ApplicationService
    from domainpy.application.projection import Projection
    from domainpy.application.integration import IntegrationEvent
    from domainpy.domain.model.event import DomainEvent
    from domainpy.infrastructure.publishers.base import IPublisher

from domainpy.utils.bus import Bus
from domainpy.utils.bus_subscribers import ApplicationServiceSubscriber, ProjectionSubscriber


class ApplicationBusAdapter:

    def __init__(self, bus: Bus[SystemMessage]) -> None:
        self.bus = bus

    def attach(self, application_service: ApplicationService) -> None:
        self.bus.attach(ApplicationServiceSubscriber(application_service))


class ProjectionBusAdapter:

    def __init__(self, bus: Bus[DomainEvent]) -> None:
        self.bus = bus

    def attach(self, projection: Projection) -> None:
        self.bus.attach(ProjectionSubscriber(projection))


PublishableMessage = typing.TypeVar('PublishableMessage', bound=typing.Union['DomainEvent', 'IntegrationEvent'])
class PublisherBusAdapter(typing.Generic[PublishableMessage]):

    def __init__(self, bus: Bus[PublishableMessage]) -> None:
        self.bus = bus

    def attach(self, publisher: IPublisher) -> None:
        self.bus.attach(publisher)