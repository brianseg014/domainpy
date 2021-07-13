
from domainpy.domain.model.event import DomainEvent
from domainpy.infrastructure.processors.base import BasicProcessor, Processor
from domainpy.typing import DomainMessage, SystemMessage
from domainpy.environments.base import IEnvironment
from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.recordmanager import EventRecordManager
from domainpy.infrastructure.idempotent.idempotency import Idempotency
from domainpy.infrastructure.idempotent.recordmanager import IdempotencyRecordManager
from domainpy.infrastructure.mappers import CommandMapper, EventMapper, IntegrationMapper, MapperSet
from domainpy.utils.bus import Bus
from domainpy.utils.registry import Registry


class EventSourcedEnvironment(IEnvironment):

    def __init__(
            self,
            command_mapper: CommandMapper,
            integration_mapper: IntegrationMapper,
            event_mapper: EventMapper,
            event_store_record_manager: EventRecordManager,
            *,
            idempotency_record_manager: IdempotencyRecordManager = None,
            processor: Processor = BasicProcessor()
    ) -> None:
        
        self.command_mapper = command_mapper
        self.integration_mapper = integration_mapper
        self.event_mapper = event_mapper

        self.idempotency_record_manager = idempotency_record_manager
        self.processor = processor

        self.mapper_set = MapperSet([
            command_mapper, integration_mapper, event_mapper
        ])

        self.registry = Registry()

        self.publisher_domain_bus = Bus[DomainEvent]()
        self.publisher_integration_bus = Bus[IntegrationEvent]()

        self.projection_bus = Bus[SystemMessage]()
        self.resolver_bus = Bus[SystemMessage]()
        self.handler_bus = Bus[SystemMessage]()

        self.event_store_bus = Bus[DomainMessage]()
        self.event_store = EventStore(
            event_mapper=event_mapper,
            record_manager=event_store_record_manager,
            bus=self.event_store_bus
        )
        self.event_store_bus.attach(self.publisher_domain_bus)
        self.event_store_bus.attach(self.publisher_integration_bus)

        self.event_store_bus.attach(self.projection_bus)
        self.event_store_bus.attach(self.resolver_bus)
        self.event_store_bus.attach(self.handler_bus)

        self.setup_registry(self.registry)

        self.setup_publisher_domain_bus(self.publisher_domain_bus)
        self.setup_publisher_integration_bus(self.publisher_integration_bus)

        self.setup_projection_bus(self.projection_bus)
        self.setup_resolver_bus(self.resolver_bus, self.publisher_integration_bus)
        self.setup_handler_bus(self.handler_bus, self.registry)

    def process(self, raw: dict):
        with self.processor(raw, self.handle) as (success_messages, fail_messages):
            return success_messages, fail_messages

    def handle(self, record: dict):
        record = self.with_idempotent(record)
        if record is not None:
            self.handler_bus.publish(
                self.mapper_set.deserialize(record)
            )

    def with_idempotent(self, record):
        if self.idempotency_record_manager is not None:
            with Idempotency(record, self.idempotency_record_manager) as record:
                return record
        else:
            return record
    
