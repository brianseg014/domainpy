import abc
import typing

from domainpy.exceptions import ConcurrencyError
from domainpy.application.service import ApplicationService
from domainpy.application.projection import Projection
from domainpy.application.integration import IntegrationEvent
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
    PublisherSubciber,
)
from domainpy.utils.registry import Registry
from domainpy.utils.contextualized import Contextualized
from domainpy.typing.application import SystemMessage


class HandlerBus(IBus[typing.Union[SystemMessage, DomainError]]):
    def __init__(self) -> None:
        self.bus = Bus[typing.Union[SystemMessage, DomainError]]()
        self.handler_bus = Bus[typing.Union[SystemMessage, DomainError]]()
        self.resolver_bus = Bus[typing.Union[SystemMessage, DomainError]]()

    def attach(
        self, subscriber: ISubscriber[typing.Union[SystemMessage, DomainError]]
    ) -> None:
        self.bus.attach(subscriber)

    def publish(
        self, message: typing.Union[SystemMessage, DomainError]
    ) -> None:
        self.handle(message)

    def handle(
        self,
        message: typing.Union[SystemMessage, DomainError],
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
                    raise ConcurrencyError("exahusted retries") from error

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
        self.publisher_bus.attach(PublisherSubciber(publisher))


class ServiceBus(IBus[typing.Union[SystemMessage, DomainError]]):
    def __init__(self) -> None:
        self.handler_bus = HandlerBus()
        self.event_bus = EventBus()

    def attach(
        self, subscriber: ISubscriber[typing.Union[SystemMessage, DomainError]]
    ) -> None:
        self.handler_bus.attach(subscriber)

    def publish(
        self, message: typing.Union[SystemMessage, DomainError]
    ) -> None:
        self.handle(message)

    def handle(
        self,
        message: typing.Union[SystemMessage, DomainError],
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


TRepository = typing.TypeVar("TRepository", bound=IRepository)
TDomainService = typing.TypeVar("TDomainService", bound=IDomainService)


class Environment:
    def __init__(self, context: str, factory: IFactory) -> None:
        self.factory = factory

        Contextualized.__context__ = context

        self.service_bus = ServiceBus()
        self.integration_bus = Bus[IntegrationEvent]()
        self.registry = Registry()

        domain_publisher = factory.create_event_publisher()
        if domain_publisher is not None:
            self.service_bus.add_event_publisher(domain_publisher)

        integration_publisher = factory.create_integration_publisher()
        self.integration_bus.attach(PublisherSubciber(integration_publisher))

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
        message: typing.Union[SystemMessage, DomainError],
        retries: int = 3,
    ) -> None:
        self.service_bus.handle(message, retries)
