import abc
import typing

from domainpy.exceptions import ConcurrencyError
from domainpy.application.command import ApplicationCommand
from domainpy.application.service import ApplicationService
from domainpy.application.projection import Projection
from domainpy.application.integration import IntegrationEvent, ScheduleIntegartionEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.exceptions import DomainError
from domainpy.domain.repository import IRepository
from domainpy.domain.service import IDomainService
from domainpy.infrastructure.publishers.base import IPublisher
from domainpy.utils.bus import Bus, IBus, ISubscriber
from domainpy.utils.bus_subscribers import (
    ApplicationServiceSubscriber,
    BusSubscriber,
    ProjectionSubscriber,
    PublisherSubscriber,
)
from domainpy.utils.registry import Registry
from domainpy.utils.contextualized import Contextualized
from domainpy.utils.traceable import Traceable
from domainpy.typing.application import ApplicationMessage


class HandlerBus(IBus[ApplicationMessage]):
    def __init__(self) -> None:
        self.bus = Bus[ApplicationMessage]()
        self.handler_bus = Bus[ApplicationMessage]()
        self.resolver_bus = Bus[ApplicationMessage]()

    def attach(self, subscriber: ISubscriber[ApplicationMessage]) -> None:
        self.bus.attach(subscriber)

    def publish(self, message: typing.Union[ApplicationMessage]) -> None:
        self.handle(message)

    def handle(
        self,
        message: typing.Union[ApplicationMessage],
        retries: int = 3,
    ) -> None:
        if retries <= 0:
            raise ValueError("retries should be positive integer")

        self.bus.publish(message)

        self.resolver_bus.publish(message)

        _retries = retries
        while _retries > 0:
            try:
                self.handler_bus.publish(message)
                return
            except DomainError as error:
                self.handle(error, retries)
                return
            except ConcurrencyError as error:
                _retries = _retries - 1
                if _retries == 0:
                    raise ConcurrencyError(f"exahusted {retries} retries: {message}") from error

    def add_handler(self, handler: ApplicationService) -> None:
        self.handler_bus.attach(ApplicationServiceSubscriber(handler))

    def add_resolver(self, resolver: ApplicationService) -> None:
        self.resolver_bus.attach(ApplicationServiceSubscriber(resolver))


class EventBus(IBus[DomainEvent]):
    def __init__(self) -> None:
        self.bus = Bus[DomainEvent]()
        self.publisher_bus = Bus[DomainEvent]()
        self.projection_bus = Bus[DomainEvent]()
        self.resolver_bus = Bus[DomainEvent]()
        self.handler_bus = Bus[DomainEvent]()

    def attach(self, subscriber: ISubscriber[DomainEvent]) -> None:
        self.bus.attach(subscriber)

    def publish(self, message: DomainEvent) -> None:
        self.bus.publish(message)

        self.publisher_bus.publish(message)
        self.projection_bus.publish(message)
        self.resolver_bus.publish(message)
        self.handler_bus.publish(message)

    def add_projection(self, projection: Projection) -> None:
        self.projection_bus.attach(ProjectionSubscriber(projection))

    def add_resolver(self, resolver: ApplicationService) -> None:
        self.resolver_bus.attach(ApplicationServiceSubscriber(resolver))

    def add_handler(self, handler: ApplicationService) -> None:
        self.handler_bus.attach(ApplicationServiceSubscriber(handler))

    def add_publisher(self, publisher: IPublisher) -> None:
        self.publisher_bus.attach(PublisherSubscriber(publisher))


class ServiceBus(IBus[ApplicationMessage]):
    def __init__(self) -> None:
        self.handler_bus = HandlerBus()
        self.event_bus = EventBus()

    def attach(self, subscriber: ISubscriber[ApplicationMessage]) -> None:
        self.handler_bus.attach(subscriber)

    def publish(self, message: ApplicationMessage) -> None:
        self.handle(message)

    def handle(
        self,
        message: ApplicationMessage,
        retries: int = 3,
    ) -> None:
        self.handler_bus.handle(message, retries)

    def add_projection(self, projection: Projection) -> None:
        self.event_bus.add_projection(projection)

    def add_handler(self, handler: ApplicationService) -> None:
        self.handler_bus.add_handler(handler)
        self.event_bus.add_handler(handler)

    def add_resolver(self, resolver: ApplicationService) -> None:
        self.handler_bus.add_resolver(resolver)
        self.event_bus.add_resolver(resolver)

    def add_event_publisher(self, publisher: IPublisher) -> None:
        self.event_bus.add_publisher(publisher)

    def add_event_subsciber(self, subscriber: ISubscriber) -> None:
        self.event_bus.attach(subscriber)


class IFactory(abc.ABC):
    @abc.abstractmethod
    def create_projection(self, key: typing.Type[Projection]) -> Projection:
        pass

    @abc.abstractmethod
    def create_repository(self, key: typing.Type[IRepository]) -> IRepository:
        pass

    @abc.abstractmethod
    def create_domain_service(
        self, key: typing.Type[IDomainService]
    ) -> IDomainService:
        pass

    @abc.abstractmethod
    def create_event_publisher(self) -> typing.Optional[IPublisher]:
        pass

    @abc.abstractmethod
    def create_integration_publisher(self) -> IPublisher:
        pass

    @abc.abstractmethod
    def create_scheduler_publisher(self) -> IPublisher:
        pass


TRepository = typing.TypeVar("TRepository", bound=IRepository)
TDomainService = typing.TypeVar("TDomainService", bound=IDomainService)


class Environment:
    def __init__(self, context: str, factory: IFactory) -> None:
        self.factory = factory

        Contextualized.__context__ = context

        self.service_bus = ServiceBus()
        self.integration_bus = Bus[IntegrationEvent]()
        self.schedule_bus = Bus[ScheduleIntegartionEvent]()
        self.registry = Registry()

        domain_publisher = factory.create_event_publisher()
        if domain_publisher is not None:
            self.service_bus.add_event_publisher(domain_publisher)

        integration_publisher = factory.create_integration_publisher()
        self.integration_bus.attach(PublisherSubscriber(integration_publisher))

        scheduler_publisher = factory.create_scheduler_publisher()
        if scheduler_publisher is not None:
            self.schedule_bus.attach(PublisherSubscriber(scheduler_publisher))

    def add_handler(self, handler: ApplicationService):
        self.service_bus.add_handler(handler)

    def add_resolver(self, resolver: ApplicationService):
        self.service_bus.add_resolver(resolver)

    def add_projection(self, projection: typing.Type[Projection]):
        _projection = self.factory.create_projection(projection)

        self.registry.put(projection, _projection)
        self.service_bus.add_projection(_projection)

    def add_repository(self, key: typing.Type[IRepository]):
        repository = self.factory.create_repository(key)
        repository.attach(BusSubscriber(self.service_bus.event_bus))
        self.registry.put(key, repository)

    def add_domain_service(
        self, key: typing.Type[IDomainService], value: IDomainService = None
    ):
        _value = value
        if _value is None:
            _value = self.factory.create_domain_service(key)
        self.registry.put(key, _value)

    def handle(
        self,
        message: ApplicationMessage,
        retries: int = 3,
    ) -> None:
        if isinstance(
            message, (ApplicationCommand, IntegrationEvent, DomainEvent)
        ):
            if message.__trace_id__ is None:
                raise TypeError("message.__trace_id__ should not be None")

            Traceable.set_default_trace_id(message.__trace_id__)

        self.service_bus.handle(message, retries)
