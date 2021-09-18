from domainpy.infrastructure.tracer.managers.memory import MemoryTraceSegmentStore
import uuid
import typing
import pytest
from unittest import mock

from domainpy.bootstrap import ContextEnvironment, IContextFactory
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.application.projection import Projection
from domainpy.domain.service import IDomainService
from domainpy.domain.repository import IRepository
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.managers.memory import MemoryEventRecordManager
from domainpy.infrastructure.publishers.base import IPublisher
from domainpy.infrastructure.publishers.memory import MemoryPublisher
from domainpy.infrastructure.tracer.tracestore import TraceSegmentRecorder
from domainpy.test.bootstrap import TestContextEnvironment, EventSourcedProcessor


class DefaultFactory(IContextFactory):
    def __init__(self, mapper: Mapper) -> None:
        self.mapper = mapper

    def create_trace_segment_store(self) -> TraceSegmentRecorder:
        return MemoryTraceSegmentStore(self.mapper)

    def create_projection(self, key: typing.Type[Projection]) -> Projection:
        pass

    def create_domain_service(self, key: typing.Type[IDomainService]) -> IDomainService:
        pass

    def create_repository(self, key: typing.Type[IRepository]) -> IRepository:
        pass

    def create_event_publisher(self) -> IPublisher:
        return MemoryPublisher()

    def create_integration_publisher(self) -> IPublisher:
        return MemoryPublisher()

    def create_schedule_publisher(self) -> IPublisher:
        return MemoryPublisher()



class Aggregate(AggregateRoot):
    def mutate(self, event: DomainEvent) -> None:
        pass

@pytest.fixture
def mapper():
    return Mapper(transcoder=Transcoder())

@pytest.fixture
def record_manager():
    return MemoryEventRecordManager()

@pytest.fixture
def event_store(mapper, record_manager):
    return EventStore(mapper, record_manager)

@pytest.fixture
def environment(mapper):
    return ContextEnvironment('ctx', DefaultFactory(mapper))

@pytest.fixture
def aggregate_id():
    return str(uuid.uuid4())

@pytest.fixture
def aggregate(aggregate_id):
    return Aggregate(Identity.from_text(aggregate_id))

@pytest.fixture
def trace_id():
    return 'tid'

@pytest.fixture
def event(trace_id, aggregate):
    return aggregate.__stamp__(DomainEvent)(
        __trace_id__ = trace_id, some_property='x'
    )

@pytest.fixture
def integration(trace_id):
    return IntegrationEvent(
        __trace_id__=trace_id,
        __resolve__ = 'success',
        __error__ = None,
        __timestamp__ = 0.0,
        some_property = 'x'
    )

@pytest.fixture
def command(trace_id):
    return ApplicationCommand(
        __timestamp__ = 0.0,
        __trace_id__ = trace_id
    )

def test_get_events(environment, event_store, event, trace_id):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))

    adap.environment.event_publisher_bus.publish(event)
    events = adap.then.domain_events.get_events(event.__class__, trace_id=trace_id)
    assert len(list(events)) == 1

def test_get_events_raises(environment, event_store, event, aggregate_id):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))

    with pytest.raises(AttributeError):
        adap.then.domain_events.get_events(event.__class__, aggregate_id=aggregate_id)
    with pytest.raises(AttributeError):
        adap.then.domain_events.get_events(event.__class__, aggregate_type=Aggregate)

def test_domain_events_given_has_event(environment, event_store, event, aggregate_id):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))

    adap.environment.event_publisher_bus.publish(event)
    adap.then.domain_events.assert_has_event(event.__class__, aggregate_type=Aggregate, aggregate_id=aggregate_id)
    adap.then.domain_events.assert_has_event_once(event.__class__)
    adap.then.domain_events.assert_has_event_n_times(event.__class__, times=1)
    adap.then.domain_events.assert_has_event_with(event.__class__, some_property='x')

def test_domain_events_has_event_fails(environment, event_store, event):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event(DomainEvent)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event_once(DomainEvent)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event_n_times(DomainEvent, times=1)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_event_with(DomainEvent, some_property='x')

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_n_events(count=1)

    adap.environment.event_publisher_bus.publish(event)
    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_not_event(DomainEvent)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_not_event_with(DomainEvent, some_property='x')

def test_domain_events_has_not_event(environment, event_store):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))
    adap.then.domain_events.assert_has_not_event(DomainEvent)

def test_get_integrations(environment: ContextEnvironment, event_store, integration, trace_id):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))
    
    environment.integration_publisher_bus.publish(integration)
    integrations = adap.then.integration_events.get_integrations(IntegrationEvent, trace_id=trace_id)
    assert len(list(integrations)) == 1

def test_integration_events_has_integration(environment: ContextEnvironment, event_store, integration):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))
    
    environment.integration_publisher_bus.publish(integration)
    adap.then.integration_events.assert_has_integration(IntegrationEvent)
    adap.then.integration_events.assert_has_integration_n(IntegrationEvent, times=1)
    adap.then.integration_events.assert_has_integration_with(IntegrationEvent, some_property='x')
    adap.then.integration_events.assert_has_integration_with_error(IntegrationEvent, error=None)

def test_integration_events_has_integration_fails(environment: ContextEnvironment, event_store, integration):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration(IntegrationEvent)

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration_n(IntegrationEvent, times=1)

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration_with(IntegrationEvent, some_property='x')

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_n_integrations(count=1)

    environment.integration_publisher_bus.publish(integration)
    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_not_integration(IntegrationEvent)

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_not_integration_with(IntegrationEvent, some_property='x')

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration_with_error(IntegrationEvent, error='some')

def test_integration_events_has_not_integration(environment: ContextEnvironment, event_store):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))

    adap.then.integration_events.assert_has_not_integration(IntegrationEvent)
    adap.then.integration_events.assert_has_not_integration_with(IntegrationEvent, some_property='x')

def test_when(environment, event_store, command):
    adap = TestContextEnvironment(environment, EventSourcedProcessor(event_store))

    environment.handle = mock.Mock()
    adap.when(command)

    environment.handle.assert_called_once_with(command)