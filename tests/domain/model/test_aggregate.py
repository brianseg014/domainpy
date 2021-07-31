
import pytest
import uuid
from unittest import mock

from domainpy.exceptions import DefinitionError, VersionError
from domainpy.domain.model.aggregate import AggregateRoot, mutator, Selector
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity


@pytest.fixture
def trace_id():
    return str(uuid.uuid4())

@pytest.fixture
def identity():
    return Identity.create()

@pytest.fixture
def event():
    return DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
    )

@pytest.fixture
def event2():
    return DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 2,
        __timestamp__ = 0.0
    )

def test_aggregate_add_to_changes_when_apply(identity, event):
    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    agg = Aggregate(identity=identity)
    agg.__apply__(event)

    assert len(agg.__changes__) == 1

def test_aggregate_call_mutate_when_apply(identity, event):
    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    agg = Aggregate(identity=identity)
    agg.mutate = mock.Mock()
    agg.__apply__(event)

    agg.mutate.assert_called_with(event)

def test_aggregate_call_mutate_when_route(identity, event):
    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    agg = Aggregate(identity=identity)
    agg.mutate = mock.Mock()
    agg.__route__(event)

    agg.mutate.assert_called_once_with(event)

def test_aggregate_route_mismatch_version(identity, event2):
    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    agg = Aggregate(identity=identity)
    agg.mutate = mock.Mock()

    with pytest.raises(VersionError):
        agg.__route__(event2)

def test_aggregate_selector(identity):
    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    agg = Aggregate(identity=identity)
    assert isinstance(agg.__selector__, Selector)

def test_selector_filter_trace(event, trace_id):
    event = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
        __trace_id__ = trace_id
    )

    selector = Selector(e for e in [event])
    events = selector.filter_trace(trace_id)

    assert len([e for e in events]) == 1

def test_selector_get_trace_for_compensation(trace_id):
    class StandardEvent(DomainEvent):
        pass

    class CompensationEvent(DomainEvent):
        pass

    standard_event = StandardEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
        __trace_id__ = trace_id
    )

    compensation_event = CompensationEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
        __trace_id__ = trace_id
    )

    selector = Selector(e for e in [standard_event])
    events = selector.get_events_for_compensation(
        trace_id, empty_if_has_event=CompensationEvent, return_event=StandardEvent
    )
    # Should return event to compensate
    assert len(events) == 1
    assert events[0] == standard_event

    selector = Selector(e for e in [standard_event, compensation_event])
    events = selector.get_events_for_compensation(
        trace_id, empty_if_has_event=CompensationEvent, return_event=StandardEvent
    )
    # Should return empty as is already compensated
    assert len(events) == 0


def test_mutator(identity, event):
    class Aggregate(AggregateRoot):
        @mutator
        def mutate(self, event: DomainEvent) -> None:
            pass

        @mutate.event(DomainEvent)
        def _(self, e: DomainEvent):
            self.proof_of_work(event)

        def proof_of_work(self, event):
            pass

    agg = Aggregate(identity=identity)
    agg.__dict__['proof_of_work'] = mock.Mock()
    agg.mutate(event)

    agg.proof_of_work.assert_called_with(event)

def test_mutator_must_be_unique():
    @mutator
    def mutate():
        pass

    mutate.event(DomainEvent)(lambda: ... )
    with pytest.raises(DefinitionError):
        mutate.event(DomainEvent)(lambda: ... )

def test_mutator_do_nothing_if_not_handle(event):
    @mutator
    def mutate():
        pass

    mutate(None, event)