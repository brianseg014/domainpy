from inspect import trace
import pytest
import uuid
from unittest import mock

from domainpy.exceptions import DefinitionError, VersionError
from domainpy.domain.model.aggregate import AggregateRoot, mutator, Selector



def test_aggregate_add_to_changes_and_mutate_when_apply():
    id = mock.MagicMock()
    event = mock.MagicMock()
    event.__number__ = 1

    agg = AggregateRoot(id=id)
    agg.mutate = mock.Mock()
    agg.__apply__(event)

    assert len(agg.__changes__) == 1
    agg.mutate.assert_called_once_with(event)

def test_aggregate_call_mutate_when_route():
    id = mock.MagicMock()
    event = mock.MagicMock()
    event.__number__ = 1

    agg = AggregateRoot(id=id)
    agg.mutate = mock.Mock()
    agg.__route__(event)

    agg.mutate.assert_called_once_with(event)

def test_aggregate_route_mismatch_version():
    id = mock.MagicMock()
    event = mock.MagicMock()
    event.__number__ = 2

    agg = AggregateRoot(id=id)
    agg.mutate = mock.Mock()

    with pytest.raises(VersionError):
        agg.__route__(event)

def test_selector_filter_trace():
    trace_id = str(uuid.uuid4())

    event = mock.MagicMock()
    event.__trace_id__ = trace_id

    selector = Selector(e for e in [event])
    events = selector.filter_trace(trace_id)

    assert len([e for e in events]) == 1

def test_selector_get_trace_for_compensation():
    trace_id = str(uuid.uuid4())

    StandarEvent = type('StandarEvent', (mock.MagicMock,), {})
    standard_event = StandarEvent()
    standard_event.__trace_id__ = trace_id

    CompensationEvent = type('CompensationEvent', (mock.MagicMock,), {})
    compensation_event = CompensationEvent()
    compensation_event.__trace_id__ = trace_id

    selector = Selector(e for e in [standard_event])
    events = selector.get_events_for_compensation(
        trace_id, empty_if_has_event=CompensationEvent, return_event=StandarEvent
    )
    # Should return event to compensate
    assert len(events) == 1
    assert events[0] == standard_event

    selector = Selector(e for e in [standard_event, compensation_event])
    events = selector.get_events_for_compensation(
        trace_id, empty_if_has_event=CompensationEvent, return_event=StandarEvent
    )
    # Should return empty as is already compensated
    assert len(events) == 0


def test_mutator():
    story = []

    something = mock.MagicMock()
    aggregate = mock.MagicMock()

    @mutator
    def mutate():
        pass

    def handle_something(*args):
        story.append(args)

    mutate.event(something.__class__)(handle_something)

    mutate(aggregate, something)

    assert story[0][0] == aggregate
    assert story[0][1] == something

def test_mutator_must_be_unique():
    something = mock.MagicMock()

    @mutator
    def mutate():
        pass

    def handle_something(*args):
        pass

    mutate.event(something.__class__)(handle_something)
    with pytest.raises(DefinitionError):
        mutate.event(something.__class__)(handle_something)
