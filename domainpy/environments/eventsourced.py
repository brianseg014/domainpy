from __future__ import annotations

import abc
import typing

from domainpy.application import IntegrationEvent
from domainpy.domain.model import DomainEvent, DomainError
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.recordmanager import (
    EventRecordManager,
)
from domainpy.infrastructure.eventsourced.managers.memory import (
    MemoryEventRecordManager,
)
from domainpy.infrastructure.mappers import Mapper
from domainpy.utils.bus import Bus
from domainpy.utils.bus_adapters import (
    ApplicationBusAdapter,
    ProjectionBusAdapter,
    PublisherBusAdapter,
)
from domainpy.utils.bus_subscribers import BusSubscriber
from domainpy.utils.registry import Registry
from domainpy.utils.traceable import Traceable
from domainpy.utils.contextualized import Contextualized
from domainpy.exceptions import ConcurrencyError
from domainpy.typing.application import SystemMessage  # type: ignore


class EventSourcedEnvironment(abc.ABC):
    def __init__(
        self,
        context: str,
        command_mapper: Mapper,
        integration_mapper: Mapper,
        event_mapper: Mapper,
        *,
        setupargs: dict = None
    ) -> None:
        if setupargs is None:
            setupargs = {}

        self.context = context
        Contextualized.__context__ = self.context

        self.command_mapper = command_mapper
        self.integration_mapper = integration_mapper
        self.event_mapper = event_mapper

        self.setupargs = setupargs

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
        self.resolver_bus = Bus[typing.Union[SystemMessage, DomainError]]()
        self.handler_bus = Bus[typing.Union[SystemMessage, DomainError]]()

        self.handler_bus.attach(BusSubscriber(self.resolver_bus))

        self.event_store_bus.attach(BusSubscriber(self.domain_publisher_bus))
        self.event_store_bus.attach(BusSubscriber(self.projection_bus))
        self.event_store_bus.attach(BusSubscriber(self.handler_bus))

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
            ProjectionBusAdapter(self.projection_bus),
            self.registry,
            self.setupargs,
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

    def handle(
        self,
        message: SystemMessage,
        retries: int = 3,
    ):
        if retries <= 0:
            raise ValueError("retries should be positive integer")

        if message.__trace_id__ is None:
            raise TypeError("__trace_id__ cannot be None")

        Traceable.__trace_id__ = message.__trace_id__

        # Publish original message, but if a domain error raises publish the
        # domain error
        #
        # If concurrency error raises from the original or the domain error
        # publishing, retry until exahusted
        publishable: typing.Union[SystemMessage, DomainError] = message

        done = False
        while not done:
            try:
                try:
                    self.handler_bus.publish(publishable)
                    done = True
                except DomainError as error:
                    publishable = error
            except ConcurrencyError as error:
                retries = retries - 1
                if retries == 0:
                    raise ConcurrencyError("exahusted retries") from error

    @abc.abstractmethod
    def setup_event_record_manager(
        self, setupargs: dict
    ) -> EventRecordManager:
        pass

    @abc.abstractmethod
    def setup_registry(
        self, registry: Registry, event_store: EventStore, setupargs: dict
    ) -> None:
        pass

    @abc.abstractmethod
    def setup_domain_publisher_bus(
        self,
        domain_publisher_bus: PublisherBusAdapter[DomainEvent],
        event_mapper: Mapper,
        setupargs: dict,
    ) -> None:
        pass

    @abc.abstractmethod
    def setup_integration_publisher_bus(
        self,
        integration_publisher_bus: PublisherBusAdapter[IntegrationEvent],
        integration_mapper: Mapper,
        setupargs: dict,
    ) -> None:
        pass

    @abc.abstractmethod
    def setup_projection_bus(
        self,
        projection_bus: ProjectionBusAdapter,
        registry: Registry,
        setupargs: dict,
    ) -> None:
        pass

    @abc.abstractmethod
    def setup_resolver_bus(
        self,
        resolver_bus: ApplicationBusAdapter,
        publisher_integration_bus: Bus[IntegrationEvent],
        setupargs: dict,
    ) -> None:
        pass

    @abc.abstractmethod
    def setup_handler_bus(
        self,
        handler_bus: ApplicationBusAdapter,
        registry: Registry,
        setupargs: dict,
    ) -> None:
        pass
