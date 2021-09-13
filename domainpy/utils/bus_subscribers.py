from __future__ import annotations

import typing

from domainpy.domain.model.event import DomainEvent
from domainpy.utils.bus import ISubscriber

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.infrastructure import (
        InfrastructureMessage,
    )  # type: ignore
    from domainpy.application.service import ApplicationService
    from domainpy.application.projection import Projection
    from domainpy.infrastructure.publishers.base import IPublisher
    from domainpy.utils.bus import IBus


class BasicSubscriber(ISubscriber, list):
    def __route__(self, message):
        self.append(message)


class BusSubscriber(ISubscriber):
    def __init__(self, bus: IBus):
        self.bus = bus

    def __route__(self, message: InfrastructureMessage):
        self.bus.publish(message)


class ApplicationServiceSubscriber(ISubscriber):
    def __init__(self, application_service: ApplicationService):
        self.application_service = application_service

    def __route__(self, message: InfrastructureMessage):
        self.application_service.handle(message)


class ProjectionSubscriber(ISubscriber):
    def __init__(self, projection: Projection):
        self.projection = projection

    def __route__(self, message: InfrastructureMessage) -> None:
        if isinstance(message, DomainEvent):
            self.projection.project(message)


class PublisherSubscriber(ISubscriber):
    def __init__(self, publisher: IPublisher):
        self.publisher = publisher

    def __route__(self, message: InfrastructureMessage):
        self.publisher.publish(message)
