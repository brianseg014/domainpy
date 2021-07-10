import pytest
from uuid import uuid4
from unittest import mock

from domainpy import exceptions as excs
from domainpy.domain.model.aggregate import AggregateRoot, mutator
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity



def test_aggregate_apply():
    class BasicAggregate(AggregateRoot):
        pass

    id = Identity.create()
    e = DomainEvent()

    agg = BasicAggregate(id=id)
    agg.mutate = mock.Mock()
    agg.__apply__(e)

    agg.mutate.assert_called_once_with(e)

    assert e.__stream_id__ == f'{id.id}:{BasicAggregate.__name__}'
    assert e.__number__ == 1
    assert len(agg.__changes__) == 1
    assert agg.__changes__[0] == e

def test_aggregate_route():
    class BasicAggregate(AggregateRoot):
        pass

    id = Identity.create()
    e = DomainEvent(
        __stream_id__ = f'{id.id}:{BasicAggregate.__name__}',
        __number__ = 0
    )

    agg = BasicAggregate(id=id)
    agg.mutate = mock.Mock()
    agg.__route__(e)

    agg.mutate.assert_called_once_with(e)

def test_selector_get_trace():
    class BasicAggregate(AggregateRoot):
        pass

    trace_id = uuid4()
    id = Identity.create()
    e = DomainEvent(
        __stream_id__ = f'{id.id}:{BasicAggregate.__name__}',
        __number__ = 0,
        __trace_id__ = trace_id
    )

    agg = BasicAggregate(id=id)
    agg.__route__(e)

    events = agg.__selector__.get_trace(trace_id, DomainEvent)
    assert len(events) == 1
    assert events[0] == e

def test_selector_get_trace_if_not_compensated():
    class BasicAggregate(AggregateRoot):
        pass

    class StandartEvent(DomainEvent):
        pass

    class CompensationEvent(DomainEvent):
        pass

    trace_id = uuid4()
    id = Identity.create()
    std_event = StandartEvent(
        __stream_id__ = f'{id.id}:{BasicAggregate.__name__}',
        __number__ = 0,
        __trace_id__ = trace_id
    )
    comp_event = CompensationEvent(
        __stream_id__ = f'{id.id}:{BasicAggregate.__name__}',
        __number__ = 1,
        __trace_id__ = trace_id
    )

    agg = BasicAggregate(id=id)
    agg.__route__(std_event)

    events = agg.__selector__.get_trace_if_not_compensated(trace_id, compensate_type=CompensationEvent)
    # Should return event to compensate
    assert len(events) == 1
    assert events[0] == std_event

    agg.__route__(comp_event)
    events = agg.__selector__.get_trace_if_not_compensated(trace_id, compensate_type=CompensationEvent)
    # Should return empty as is already compensated
    assert len(events) == 0

def test_mutator():
    class BasicAggregate(AggregateRoot):

        @mutator
        def mutate(self, e: DomainEvent):
            pass

        @mutate.event(DomainEvent)
        def _(self, e: DomainEvent):
            self.e = e


    id = Identity.create()
    e = DomainEvent(
        __stream_id__ = f'{id.id}:{BasicAggregate.__name__}',
        __number__ = 1,
    )

    agg = BasicAggregate(id=id)
    agg.__route__(e)

    assert agg.e == e

def test_mutator_must_be_unique():
    with pytest.raises(excs.DefinitionError):
        class BasicAggregate(AggregateRoot):

            @mutator
            def mutate(self, e: DomainEvent):
                pass

            @mutate.event(DomainEvent)
            def _(self, e: DomainEvent):
                pass

            @mutate.event(DomainEvent)
            def _(self, e: DomainEvent):
                pass
