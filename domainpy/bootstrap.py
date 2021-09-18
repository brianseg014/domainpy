import abc
import typing

from domainpy.exceptions import ConcurrencyError, DefinitionError
from domainpy.application.command import ApplicationCommand
from domainpy.application.query import ApplicationQuery
from domainpy.application.service import ApplicationService
from domainpy.application.projection import Projection
from domainpy.application.integration import (
    IntegrationEvent,
    ScheduleIntegartionEvent,
)
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.exceptions import DomainError
from domainpy.domain.repository import IRepository
from domainpy.domain.service import IDomainService
from domainpy.infrastructure.publishers.base import IPublisher
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.recordmanager import (
    EventRecordManager,
)
from domainpy.infrastructure.tracer.tracestore import (
    TraceSegmentStore,
    TraceStore,
)
from domainpy.infrastructure.mappers import Mapper
from domainpy.utils.bus import Bus
from domainpy.utils.bus_subscribers import (
    BusSubscriber,
    ApplicationServiceSubscriber,
    ProjectionSubscriber,
    PublisherSubscriber,
)
from domainpy.utils.registry import Registry
from domainpy.utils.contextualized import Contextualized
from domainpy.utils.traceable import Traceable
from domainpy.typing.application import ApplicationMessage
from domainpy.typing.infrastructure import InfrastructureMessage


class IContextFactory(abc.ABC):
    @abc.abstractmethod
    def create_trace_segment_store(self) -> TraceSegmentStore:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_projection(self, key: typing.Type[Projection]) -> Projection:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_domain_service(
        self, key: typing.Type[IDomainService]
    ) -> IDomainService:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_repository(self, key: typing.Type[IRepository]) -> IRepository:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_event_publisher(self) -> IPublisher:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_integration_publisher(self) -> IPublisher:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_schedule_publisher(self) -> IPublisher:
        pass  # pragma: no cover


class ContextEnvironment(ApplicationService):
    def __init__(
        self,
        context: str,
        factory: IContextFactory,
        close_loop: bool = True,
        retries: int = 3,
    ):
        if retries <= 0:
            raise ValueError("retries should be positive integer")

        self.context = context
        self.factory = factory
        self.close_loop = close_loop
        self.retries = retries

        Contextualized.set_default_context(context)

        self.registry = Registry()

        self.trace_segment_store = self.factory.create_trace_segment_store()

        self.projection_bus = Bus[DomainEvent]()
        self.resolver_bus = Bus[ApplicationMessage]()
        self.handler_bus = Bus[ApplicationMessage]()

        self.event_publisher_bus = Bus[DomainEvent]()
        event_publisher = self.factory.create_event_publisher()
        self.event_publisher_bus.attach(PublisherSubscriber(event_publisher))

        self.integration_publisher_bus = Bus[IntegrationEvent]()
        integration_publisher = self.factory.create_integration_publisher()
        self.integration_publisher_bus.attach(
            PublisherSubscriber(integration_publisher)
        )

        self.scheduler_publisher_bus = Bus[ScheduleIntegartionEvent]()
        schedule_publisher = self.factory.create_schedule_publisher()
        self.scheduler_publisher_bus.attach(
            PublisherSubscriber(schedule_publisher)
        )

        # Self publish outgoing domain events
        if close_loop:
            self.event_publisher_bus.attach(ApplicationServiceSubscriber(self))

    def add_projection(self, key: typing.Type[Projection]) -> None:
        projection = self.factory.create_projection(key)

        self.registry.put(key, projection)

        self.projection_bus.attach(ProjectionSubscriber(projection))

    def add_handler(self, handler: ApplicationService) -> None:
        self.handler_bus.attach(ApplicationServiceSubscriber(handler))

    def add_resolver(self, resolver: ApplicationService) -> None:
        self.resolver_bus.attach(ApplicationServiceSubscriber(resolver))

    def add_domain_service(
        self,
        key: typing.Type[IDomainService],
        service: typing.Optional[IDomainService] = None,
    ) -> None:
        _service = service
        if _service is None:
            _service = self.factory.create_domain_service(key)

        self.registry.put(key, _service)

    def add_repository(self, key: typing.Type[IRepository]) -> None:
        repository = self.factory.create_repository(key)

        self.registry.put(key, repository)

        repository.attach(BusSubscriber(self.event_publisher_bus))

    def trace(self, message: InfrastructureMessage) -> None:
        if message.__trace_id__ is None:
            raise DefinitionError("__trace_id__ should not be NoneType")

        with self.trace_segment_store.start_trace_segment(message):
            Traceable.set_default_trace_id(message.__trace_id__)
            self.handle(message)

    def handle(self, message: ApplicationMessage) -> None:
        if isinstance(message, DomainEvent):
            self.projection_bus.publish(message)

        self.resolver_bus.publish(message)

        _retries = self.retries
        while _retries > 0:
            try:
                return self.handler_bus.publish(message)
            except DomainError as error:
                return self.handle(error)
            except ConcurrencyError as error:
                _retries = _retries - 1
                if _retries == 0:
                    raise ConcurrencyError(
                        f"exahusted {self.retries} retries: {message}"
                    ) from error


class IEventSourcedContextFactory(IContextFactory):
    def inject_event_store(self, event_store: EventStore) -> None:
        self.event_store = event_store

    @abc.abstractmethod
    def create_event_record_manager(self) -> EventRecordManager:
        pass


class EventSourcedContextEnvironment(ContextEnvironment):
    def __init__(
        self,
        context: str,
        mapper: Mapper,
        factory: IEventSourcedContextFactory,
        close_loop: bool = True,
        retries: int = 3,
    ):
        super().__init__(
            context, factory, close_loop=close_loop, retries=retries
        )
        self.factory = factory

        event_record_manager = self.factory.create_event_record_manager()
        self.event_store = EventStore(
            event_mapper=mapper, record_manager=event_record_manager
        )
        self.factory.inject_event_store(self.event_store)


class IContextMapFactory(abc.ABC):
    @abc.abstractmethod
    def create_trace_segment_store(self) -> TraceSegmentStore:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_projection(self, key: typing.Type[Projection]) -> Projection:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_integration_publisher(self) -> IPublisher:
        pass  # pragma: no cover


class ContextMapEnvironment(ApplicationService):
    def __init__(self, context: str, factory: IContextMapFactory):
        self.context = context
        self.factory = factory

        Contextualized.set_default_context(context)

        self.registry = Registry()

        self.trace_segment_store = self.factory.create_trace_segment_store()

        self.projection_bus = Bus[DomainEvent]()
        self.resolver_bus = Bus[typing.Union[DomainEvent]]()

        self.integration_publisher_bus = Bus[IntegrationEvent]()
        integration_publisher = self.factory.create_integration_publisher()
        self.integration_publisher_bus.attach(
            PublisherSubscriber(integration_publisher)
        )

    def add_projection(self, key: typing.Type[Projection]) -> None:
        projection = self.factory.create_projection(key)

        self.registry.put(key, projection)

        self.projection_bus.attach(ProjectionSubscriber(projection))

    def add_resolver(self, resolver: ApplicationService) -> None:
        self.resolver_bus.attach(ApplicationServiceSubscriber(resolver))

    def trace(self, message: InfrastructureMessage) -> None:
        if message.__trace_id__ is None:
            raise DefinitionError("__trace_id__ should not be NoneType")

        with self.trace_segment_store.start_trace_segment(message):
            Traceable.set_default_trace_id(message.__trace_id__)
            self.handle(message)

    def handle(self, message: ApplicationMessage) -> None:
        if isinstance(message, DomainEvent):
            self.projection_bus.publish(message)
            self.resolver_bus.publish(message)


class IProjectorFactory(abc.ABC):
    @abc.abstractmethod
    def create_trace_segment_store(self) -> TraceSegmentStore:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_projection(self, key: typing.Type[Projection]) -> Projection:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_query_result_publisher(self) -> IPublisher:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_integration_publisher(self) -> IPublisher:
        pass  # pragma: no cover


class ProjectorEnvironment(ApplicationService):
    def __init__(self, context: str, factory: IProjectorFactory):
        self.context = context
        self.factory = factory

        Contextualized.set_default_context(context)

        self.registry = Registry()

        self.trace_segment_store = factory.create_trace_segment_store()

        self.projection_bus = Bus[DomainEvent]()
        self.handler_bus = Bus[typing.Union[ApplicationQuery, DomainEvent]]()
        self.resolver_bus = Bus[typing.Union[ApplicationQuery, DomainEvent]]()

        self.query_result_publisher_bus = Bus[typing.Any]()
        query_result_publisher = self.factory.create_query_result_publisher()
        self.query_result_publisher_bus.attach(
            PublisherSubscriber(query_result_publisher)
        )

        self.integration_publisher_bus = Bus[IntegrationEvent]()
        integration_publisher = self.factory.create_integration_publisher()
        self.integration_publisher_bus.attach(
            PublisherSubscriber(integration_publisher)
        )

    def add_projection(self, key: typing.Type[Projection]) -> None:
        projection = self.factory.create_projection(key)

        self.registry.put(key, projection)

        self.projection_bus.attach(ProjectionSubscriber(projection))

    def add_handler(self, handler: ApplicationService) -> None:
        self.handler_bus.attach(ApplicationServiceSubscriber(handler))

    def add_resolver(self, resolver: ApplicationService) -> None:
        self.resolver_bus.attach(ApplicationServiceSubscriber(resolver))

    def trace(self, message: InfrastructureMessage) -> None:
        if message.__trace_id__ is None:
            raise DefinitionError("__trace_id__ should not be NoneType")

        with self.trace_segment_store.start_trace_segment(message):
            Traceable.set_default_trace_id(message.__trace_id__)
            self.handle(message)

    def handle(self, message: ApplicationMessage) -> None:
        if isinstance(message, DomainEvent):
            self.projection_bus.publish(message)

        if isinstance(message, (ApplicationQuery, DomainEvent)):
            self.resolver_bus.publish(message)
            self.handler_bus.publish(message)


class IGatewayFactory:
    @abc.abstractmethod
    def create_trace_store(self) -> TraceStore:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_command_publisher(self) -> IPublisher:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_response_publisher(self) -> IPublisher:
        pass  # pragma: no cover


class GatewayEnvironment(ApplicationService):
    def __init__(
        self,
        context: str,
        factory: IGatewayFactory,
        sync: bool = False,
        sync_timeout_ms: int = 3000,
        sync_backoff_ms: int = 100,
    ) -> None:
        self.context = context
        self.factory = factory
        self.sync = sync
        self.sync_timeout_ms = sync_timeout_ms
        self.sync_backoff_ms = sync_backoff_ms

        Contextualized.set_default_context(context)

        self.trace_store = factory.create_trace_store()

        self.handler_bus = Bus[
            typing.Union[
                ApplicationCommand, ApplicationQuery, IntegrationEvent
            ]
        ]()
        self.resolver_bus = Bus[
            typing.Union[
                ApplicationCommand, ApplicationQuery, IntegrationEvent
            ]
        ]()

        self.command_publisher_bus = Bus[ApplicationCommand]()
        command_publisher = self.factory.create_command_publisher()
        self.command_publisher_bus.attach(
            PublisherSubscriber(command_publisher)
        )

        self.response_publisher_bus = Bus[dict]()
        response_publisher = self.factory.create_response_publisher()
        self.response_publisher_bus.attach(
            PublisherSubscriber(response_publisher)
        )

    def add_handler(self, handler: ApplicationService) -> None:
        self.handler_bus.attach(ApplicationServiceSubscriber(handler))

    def add_resolver(self, resolver: ApplicationService) -> None:
        self.resolver_bus.attach(ApplicationServiceSubscriber(resolver))

    def trace(
        self,
        message: typing.Union[
            ApplicationCommand, ApplicationQuery, IntegrationEvent
        ],
    ) -> None:
        if message.__trace_id__ is None:
            raise DefinitionError("__trace_id__ should not be NoneType")

        Traceable.set_default_trace_id(message.__trace_id__)
        self.trace_store.start_trace(message)

        self.handle(message)

        if self.sync:
            # Publish in current thread async integration events
            # coming from other contexts
            integration_bus = Bus[ApplicationMessage]()
            integration_bus.attach(ApplicationServiceSubscriber(self))
            self.trace_store.watch_trace_resolution(
                message.__trace_id__,
                integration_bus=integration_bus,
                timeout_ms=self.sync_timeout_ms,
                backoff_ms=self.sync_backoff_ms,
            )

    def handle(self, message: ApplicationMessage) -> None:
        if isinstance(
            message, (ApplicationCommand, ApplicationQuery, IntegrationEvent)
        ):
            self.resolver_bus.publish(message)
            self.handler_bus.publish(message)
