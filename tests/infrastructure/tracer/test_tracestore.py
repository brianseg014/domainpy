import uuid
import pytest

from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.tracer.tracestore import TraceStore, Resolution
from domainpy.infrastructure.tracer.managers.memory import MemoryTraceRecordManager
from domainpy.infrastructure.records import CommandRecord
from domainpy.infrastructure.transcoder import MessageType
from domainpy.utils.bus import Bus


@pytest.fixture
def trace_id():
    return str(uuid.uuid4())


@pytest.fixture
def record(trace_id):
    return CommandRecord(
        trace_id=trace_id,
        topic=ApplicationCommand.__name__,
        version=1,
        timestamp=0.0,
        message=MessageType.APPLICATION_COMMAND.value,
        payload={}
    )

def test_store_in_progress(trace_id, record):
    some_context = 'some_context'

    record_manager = MemoryTraceRecordManager()
    store = TraceStore(record_manager, Bus())
    store.store_in_progress(trace_id, record, [some_context])
    trace_contexts = record_manager.get_trace_contexts(trace_id)

    trace_contexts = list(trace_contexts)
    assert len(trace_contexts) == 1
    assert trace_contexts[0].context == some_context
    assert trace_contexts[0].resolution == Resolution.pending
    assert trace_contexts[0].timestamp_resolution == None
    assert trace_contexts[0].error == None

def test_store_context_success(trace_id, record):
    some_context = 'some_context'

    record_manager = MemoryTraceRecordManager()
    store = TraceStore(record_manager, Bus())
    store.store_in_progress(trace_id, record, [some_context])
    store.store_context_success(trace_id, some_context)
    trace_contexts = record_manager.get_trace_contexts(trace_id)
    
    trace_contexts = list(trace_contexts)
    assert len(trace_contexts) == 1
    assert trace_contexts[0].context == some_context
    assert trace_contexts[0].resolution == Resolution.success

def test_store_context_failure():
    some_context = 'some_context'
    error = 'error'

    record_manager = MemoryTraceRecordManager()
    store = TraceStore(record_manager, Bus())
    store.store_in_progress(trace_id, record, [some_context])
    store.store_context_failure(trace_id, some_context, error)
    trace_contexts = record_manager.get_trace_contexts(trace_id)
    
    trace_contexts = list(trace_contexts)
    assert len(trace_contexts) == 1
    assert trace_contexts[0].context == some_context
    assert trace_contexts[0].resolution == Resolution.failure
    assert trace_contexts[0].error == error
