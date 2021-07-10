
from inspect import trace
import uuid
from unittest import mock

from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.records import TraceRecord
from domainpy.infrastructure.tracer.tracestore import TraceStore


def test_store_in_progress():
    mapper = mock.MagicMock()
    manager = mock.MagicMock()
    bus = mock.MagicMock()

    command = ApplicationCommand()

    store = TraceStore(mapper, manager, bus)
    store.store_in_progress(command, ['some_context'])

    manager.store_in_progress.assert_called()

def test_store_context_success():
    trace_id = str(uuid.uuid4())

    mapper = mock.MagicMock()
    manager = mock.MagicMock()
    bus = mock.MagicMock()

    manager.get_trace_contexts = mock.Mock(return_value=[
        TraceRecord.ContextResolution(
            context='some_context',
            resolution=TraceRecord.Resolution.success.name
        )
    ])

    store = TraceStore(mapper, manager, bus)
    store.store_context_success(trace_id, 'some_context')

    manager.store_context_success.assert_called()
    bus.publish.assert_called()

def test_store_context_failure():
    trace_id = str(uuid.uuid4())

    mapper = mock.MagicMock()
    manager = mock.MagicMock()
    bus = mock.MagicMock()

    manager.get_trace_contexts = mock.Mock(return_value=[
        TraceRecord.ContextResolution(
            context='some_context',
            resolution=TraceRecord.Resolution.failure.name,
            error='some-error-description'
        )
    ])

    store = TraceStore(mapper, manager, bus)
    store.store_context_failure(trace_id, 'some_context', 'some-error')

    manager.store_context_failure.assert_called()
    bus.publish.assert_called()