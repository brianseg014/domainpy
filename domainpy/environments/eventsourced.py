from __future__ import annotations

import typing

from domainpy.application import IntegrationEvent
from domainpy.domain import DomainError
from domainpy.domain.model import DomainEvent
from domainpy.infrastructure import (
    EventRecordManager,
    EventStore,
    Mapper,
    MapperSet,
    MemoryEventRecordManager,
)
from domainpy.typing import SystemMessage
from domainpy.utils import (
    ApplicationBusAdapter,
    Bus,
    ProjectionBusAdapter,
    PublisherBusAdapter,
    Registry,
)
from domainpy.utils.traceable import Traceable


class EventSourcedEnvironment:
    def __init__(
        self,
        command_mapper: Mapper,
        integration_mapper: Mapper,
        event_mapper: Mapper,
        *,
        setupargs: dict = {}
    ) -> None:

        self.command_mapper = command_mapper
        self.integration_mapper = integration_mapper
        self.event_mapper = event_mapper

        self.setupargs = setupargs

        self.mapper_set = MapperSet(
            [self.command_mapper, self.integration_mapper, self.event_mapper]
        )

        self.event_record_manager = self.setup_event_record_manager(setupargs)
        if self.event_record_manager is None:
            self.event_record_manager = MemoryEventRecordManager()

        self.event_store_bus = Bus[DomainEvent]()
        self.event_store = EventStore(
            event_mapper=event_mapper,
            record_manager=self.event_record_manager,
            bus=self.event_store_bus,
        )

        self.registry = Registry()

        self.domain_publisher_bus = Bus[DomainEvent]()
        self.integration_publisher_bus = Bus[IntegrationEvent]()
        self.projection_bus = Bus[DomainEvent]()
        self.resolver_bus = Bus[SystemMessage]()
        self.handler_bus = Bus[SystemMessage](publish_exceptions=DomainError)

        self.event_store_bus.attach(self.domain_publisher_bus)
        self.event_store_bus.attach(self.integration_publisher_bus)
        self.event_store_bus.attach(self.projection_bus)
        self.event_store_bus.attach(self.resolver_bus)
        self.event_store_bus.attach(self.handler_bus)

        self.setup_registry(self.registry, self.event_store, self.setupargs)
        self.setup_domain_publisher_bus(
            PublisherBusAdapter(self.domain_publisher_bus),
            self.event_mapper,
            self.setupargs,
        )
        self.setup_integration_publisher_bus(
            PublisherBusAdapter(self.integration_publisher_bus),
            self.integration_mapper,
            self.setupargs,
        )
        self.setup_projection_bus(
            ProjectionBusAdapter(self.projection_bus), self.setupargs
        )
        self.setup_resolver_bus(
            ApplicationBusAdapter(self.resolver_bus),
            self.integration_publisher_bus,
            self.setupargs,
        )
        self.setup_handler_bus(
            ApplicationBusAdapter(self.handler_bus),
            self.registry,
            self.setupargs,
        )

    def handle(self, message: typing.Union[SystemMessage, dict]):
        if isinstance(message, dict):
            message = self.mapper_set.deserialize(message)

        if message.__trace_id__ is None:
            raise TypeError("__trace_id__ cannot be None")

        Traceable.__trace_id__ = message.__trace_id__

        self.resolver_bus.publish(message)
        self.handler_bus.publish(message)

    def setup_event_record_manager(
        self, setupargs: dict
    ) -> EventRecordManager:
        pass

    def setup_registry(
        self, registry: Registry, event_store: EventStore, setupargs: dict
    ) -> None:
        pass

    def setup_domain_publisher_bus(
        self,
        domain_publisher_bus: PublisherBusAdapter[DomainEvent],
        event_mapper: Mapper,
        setupargs: dict,
    ) -> None:
        pass

    def setup_integration_publisher_bus(
        self,
        integration_publisher_bus: PublisherBusAdapter[IntegrationEvent],
        integration_mapper: Mapper,
        setupargs: dict,
    ) -> None:
        pass

    def setup_projection_bus(
        self, projection_bus: ProjectionBusAdapter, setupargs: dict
    ) -> None:
        pass

    def setup_resolver_bus(
        self,
        resolver_bus: ApplicationBusAdapter,
        publisher_integration_bus: Bus[DomainEvent],
        setupargs: dict,
    ) -> None:
        pass

    def setup_handler_bus(
        self,
        handler_bus: ApplicationBusAdapter,
        registry: Registry,
        setupargs: dict,
    ) -> None:
        pass
