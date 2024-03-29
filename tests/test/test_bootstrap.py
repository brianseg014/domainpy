from domainpy.infrastructure.tracer.managers.memory import MemoryTraceSegmentStore
import uuid
import typing
import pytest
from unittest import mock

from domainpy.bootstrap import ContextEnvironment, IContextFactory
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent, ScheduleIntegartionEvent
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
from domainpy.infrastructure.tracer.tracestore import TraceSegmentRecorder
from domainpy.utils.bus import Bus
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
def publisher_bus():
    return Bus()

@pytest.fixture
def environment(mapper, publisher_bus):
    return ContextEnvironment('ctx', DefaultFactory(mapper), publisher_bus)

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
        __trace_id__ = trace_id,
        __version__ = 1, 
        some_property='x'
    )

@pytest.fixture
def integration(trace_id):
    return IntegrationEvent(
        __trace_id__=trace_id,
        __resolve__ = 'success',
        __error__ = None,
        __timestamp__ = 0.0,
        __version__ = 1,
        some_property = 'x'
    )

@pytest.fixture
def command(trace_id):
    return ApplicationCommand(
        __timestamp__ = 0.0,
        __trace_id__ = trace_id,
        __version__ = 1
    )

def test_get_events(environment, event_store, event, trace_id, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )

    publisher_bus.publish(event)
    events = adap.then.domain_events.get_events(event.__class__, trace_id=trace_id)
    assert len(list(events)) == 1

def test_get_events_raises(environment, event_store, event, aggregate_id, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )

    with pytest.raises(AttributeError):
        adap.then.domain_events.get_events(event.__class__, aggregate_id=aggregate_id)
    with pytest.raises(AttributeError):
        adap.then.domain_events.get_events(event.__class__, aggregate_type=Aggregate)

def test_domain_events_given_has_event(environment, event_store, event, aggregate_id, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )

    publisher_bus.publish(event)
    adap.then.domain_events.assert_has_event(event.__class__, aggregate_type=Aggregate, aggregate_id=aggregate_id)
    adap.then.domain_events.assert_has_event_once(event.__class__)
    adap.then.domain_events.assert_has_event_n_times(event.__class__, times=1)
    adap.then.domain_events.assert_has_event_with(event.__class__, some_property='x')

def test_domain_events_has_event_fails(environment, event_store, event, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )

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

    publisher_bus.publish(event)
    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_not_event(DomainEvent)

    with pytest.raises(AssertionError):
        adap.then.domain_events.assert_has_not_event_with(DomainEvent, some_property='x')

def test_domain_events_has_not_event(environment, event_store, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )
    adap.then.domain_events.assert_has_not_event(DomainEvent)

def test_get_integrations(environment: ContextEnvironment, event_store, integration, trace_id, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )
    
    publisher_bus.publish(integration)
    integrations = adap.then.integration_events.get_integrations(IntegrationEvent, trace_id=trace_id)
    assert len(list(integrations)) == 1

def test_integration_events_has_integration(environment: ContextEnvironment, event_store, integration, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )
    
    publisher_bus.publish(integration)
    adap.then.integration_events.assert_has_integration(IntegrationEvent)
    adap.then.integration_events.assert_has_integration_n(IntegrationEvent, times=1)
    adap.then.integration_events.assert_has_integration_with(IntegrationEvent, some_property='x')
    adap.then.integration_events.assert_has_integration_with_error(IntegrationEvent, error=None)

def test_integration_events_has_integration_fails(environment: ContextEnvironment, event_store, integration, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration(IntegrationEvent)

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration_n(IntegrationEvent, times=1)

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration_with(IntegrationEvent, some_property='x')

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_n_integrations(count=1)

    publisher_bus.publish(integration)
    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_not_integration(IntegrationEvent)

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_not_integration_with(IntegrationEvent, some_property='x')

    with pytest.raises(AssertionError):
        adap.then.integration_events.assert_has_integration_with_error(IntegrationEvent, error='some')

def test_integration_events_has_not_integration(environment: ContextEnvironment, event_store, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )

    adap.then.integration_events.assert_has_not_integration(IntegrationEvent)
    adap.then.integration_events.assert_has_not_integration_with(IntegrationEvent, some_property='x')

def test_when(environment, event_store, command, publisher_bus):
    adap = TestContextEnvironment(
        environment, 
        EventSourcedProcessor(event_store),
        publisher_bus
    )

    environment.handle = mock.Mock()
    adap.when(command)

    environment.handle.assert_called_once_with(command)
