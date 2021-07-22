from __future__ import annotations

import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.application import SystemMessage  # type: ignore
    from domainpy.application.service import ApplicationService
    from domainpy.application.projection import Projection
    from domainpy.domain.model.event import DomainEvent
    from domainpy.infrastructure.publishers.base import IPublisher
    from domainpy.utils.bus import Bus

from domainpy.utils.bus import ISubscriber


class BasicSubscriber(ISubscriber, list):
    def __route__(self, message):
        self.append(message)


class BusSubscriber(ISubscriber):
    def __init__(self, bus: Bus):
        self.bus = bus

    def __route__(self, message: SystemMessage):
        self.bus.publish(message)


class ApplicationServiceSubscriber(ISubscriber):
    def __init__(self, application_service: ApplicationService):
        self.application_service = application_service

    def __route__(self, message: SystemMessage):
        self.application_service.handle(message)


class ProjectionSubscriber(ISubscriber):
    def __init__(self, projection: Projection):
        self.projection = projection

    def __route__(self, message: DomainEvent):
        self.projection.project(message)


class PublisherSubciber(ISubscriber):
    def __init__(self, publisher: IPublisher):
        self.publisher = publisher

    def __route__(self, message: SystemMessage):
        self.publisher.publish(message)
