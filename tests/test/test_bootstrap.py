
import uuid
import pytest
import typing
from unittest import mock

from domainpy.bootstrap import Environment, IFactory
from domainpy.application.projection import Projection
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity
from domainpy.domain.repository import IRepository
from domainpy.domain.service import IDomainService
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.managers.memory import MemoryEventRecordManager
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.publishers.base import IPublisher
from domainpy.infrastructure.publishers.memory import MemoryPublisher
from domainpy.utils.bus import Bus
from domainpy.utils.contextualized import Contextualized
from domainpy.test.bootstrap import EventSourcedProcessor, TestEnvironment


class DefaultFactory(IFactory):
    def create_projection(self, key: typing.Type[Projection]) -> Projection:
        pass

    def create_repository(self, key: typing.Type[IRepository]) -> IRepository:
        pass

    def create_domain_service(self, key: typing.Type[IDomainService]) -> IDomainService:
        pass

    def create_event_publisher(self) -> IPublisher:
        return MemoryPublisher()

    def create_integration_publisher(self) -> IPublisher:
        return MemoryPublisher()

class Aggregate(AggregateRoot):
    def mutate(self, event: DomainEvent) -> None:
        pass


@pytest.fixture
def event_mapper():
    return Mapper(transcoder=Transcoder())

@pytest.fixture
def record_manager():
    return MemoryEventRecordManager()

@pytest.fixture
def event_store(event_mapper, record_manager):
    return EventStore(event_mapper, record_manager)

@pytest.fixture
def environment():
    return Environment('ctx', DefaultFactory())

@pytest.fixture
def integration_bus():
    return Bus()

@pytest.fixture
def aggregate_id():
    return str(uuid.uuid4())

@pytest.fixture
def aggregate(aggregate_id):
    return Aggregate(Identity.from_text(aggregate_id))

@pytest.fixture
def event(aggregate):
    return aggregate.__stamp__(DomainEvent)(
        __trace_id__ = 'tid', some_property='x'
    )

@pytest.fixture
def integration():
    return IntegrationEvent(
        __resolve__ = 'success',
        __error__ = None,
        __timestamp__ = 0.0,
        some_property = 'x'
    )

@pytest.fixture
def command():
    return ApplicationCommand(
        __timestamp__ = 0.0,
        __trace_id__ = 'tid'
    )

@pytest.fixture(autouse=True)
def _():
    Contextualized.__context__ = 'ctx'

def test_event_store_given_has_event(environment, event_store, event, aggregate_id):
    adap = TestEnvironment(environment, EventSourcedProcessor(event_store))

    adap.given(event)
    adap.then.domain_events.assert_has_event(event.__class__, aggregate_type=Aggregate, aggregate_id=aggregate_id)
    adap.then.domain_events.assert_has_event_once(event.__class__)
    adap.then.domain_events.assert_has_event_n_times(event.__class__, times=1)
    adap.then.domain_events.assert_has_event_with(event.__class__, some_property='x')

def test_event_store_has_event_fails(environment, event_store):
    adap = TestEnvironment(environment, EventSourcedProcessor(event_store))

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event(DomainEvent)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event_once(DomainEvent)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event_n_times(DomainEvent, times=1)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event_with(DomainEvent, some_property='x')

def test_event_store_has_not_event(environment, event_store):
    adap = TestEnvironment(environment, EventSourcedProcessor(event_store))
    adap.then.domain_events.assert_has_not_event(DomainEvent)

def test_integrations_has_integration(environment, event_store, integration):
    adap = TestEnvironment(environment, EventSourcedProcessor(event_store))
    
    environment.integration_bus.publish(integration)
    adap.then.integration_events.assert_has_integration(IntegrationEvent)
    adap.then.integration_events.assert_has_integration_with(IntegrationEvent, some_property='x')

def test_integrations_has_not_integration(environment, event_store):
    adap = TestEnvironment(environment, EventSourcedProcessor(event_store))

    adap.then.integration_events.assert_has_not_integration(IntegrationEvent)

def test_when(environment, event_store, command):
    adap = TestEnvironment(environment, EventSourcedProcessor(event_store))

    environment.service_bus.handle = mock.Mock()
    adap.when(command)

    environment.service_bus.handle.assert_called_once_with(command, mock.ANY)