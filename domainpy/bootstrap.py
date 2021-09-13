import abc
import typing

from domainpy.exceptions import ConcurrencyError
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


class IContextFactory(abc.ABC):
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

        # First, publish outside
        repository.attach(BusSubscriber(self.event_publisher_bus))

        # Then, if close loop, handle
        if self.close_loop:
            # Handle in this environment new domain events
            repository.attach(ApplicationServiceSubscriber(self))

    def handle(self, message: ApplicationMessage) -> None:
        traceable_messages = (
            ApplicationCommand,
            IntegrationEvent,
            DomainEvent,
        )
        if isinstance(message, traceable_messages):
            if message.__trace_id__ is None:
                raise ValueError("message.__trace_id__ should not be NoneType")

            Traceable.set_default_trace_id(message.__trace_id__)

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


class IContextMapFactory(abc.ABC):
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

        self.projection_bus = Bus[DomainEvent]()
        self.resolver_bus = Bus[typing.Union[IntegrationEvent, DomainEvent]]()

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

    def handle(self, message: ApplicationMessage) -> None:
        if isinstance(message, DomainEvent):
            self.projection_bus.publish(message)

        if isinstance(message, (IntegrationEvent, DomainEvent)):
            self.resolver_bus.publish(message)


class IProjectorFactory(abc.ABC):
    @abc.abstractmethod
    def create_projection(self, key: typing.Type[Projection]) -> Projection:
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

        self.projection_bus = Bus[DomainEvent]()
        self.handler_bus = Bus[ApplicationQuery]()
        self.resolver_bus = Bus[ApplicationQuery]()

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

    def handle(self, message: ApplicationMessage) -> None:
        if isinstance(message, DomainEvent):
            self.projection_bus.publish(message)

        if isinstance(message, ApplicationQuery):
            self.resolver_bus.publish(message)
            self.handler_bus.publish(message)


class IGatewayFactory:
    @abc.abstractmethod
    def create_command_publisher(self) -> IPublisher:
        pass  # pragma: no cover

    @abc.abstractmethod
    def create_response_publisher(self) -> IPublisher:
        pass  # pragma: no cover


class GatewayEnvironment(ApplicationService):
    def __init__(self, context: str, factory: IGatewayFactory) -> None:
        self.context = context
        self.factory = factory

        Contextualized.set_default_context(context)

        self.handler_bus = Bus[ApplicationCommand]()
        self.resolver_bus = Bus[
            typing.Union[ApplicationCommand, IntegrationEvent]
        ]()

        self.command_publisher_bus = Bus[ApplicationCommand]()
        command_publisher = self.factory.create_response_publisher()
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
