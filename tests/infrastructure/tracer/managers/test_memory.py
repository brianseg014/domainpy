import typing
import pytest
import uuid
import datetime

from domainpy.infrastructure.records import CommandRecord
from domainpy.infrastructure.tracer.recordmanager import ContextResolution, Resolution, StatusCode
from domainpy.infrastructure.tracer.managers.memory import MemoryTraceRecordManager


@pytest.fixture
def trace_id():
    return str(uuid.uuid4())

@pytest.fixture
def command_record(trace_id):
    return CommandRecord(
        trace_id=trace_id,
        topic='some-command-topic',
        version=1,
        timestamp=datetime.datetime.timestamp(datetime.datetime.now()),
        message='command',
        payload={ 'some_property': 'x' }
    )

@pytest.fixture
def contexts_resolutions():
    return tuple([
        ContextResolution(
            context='some_context',
            resolution=Resolution.pending
        )
    ])

def test_get_trace_contexts(trace_id: str, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutinos = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    expected_contexts_resolutions = contexts_resolutions

    manager = MemoryTraceRecordManager()
    manager.store_in_progress(trace_id, command_record, resolutinos)
    contexts_resolutions = manager.get_trace_contexts(trace_id)

    for cr1,cr2 in zip(contexts_resolutions, expected_contexts_resolutions):
        assert cr1 == cr2

def test_store_in_progress(trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutinos = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    
    manager = MemoryTraceRecordManager()
    manager.store_in_progress(trace_id, command_record, resolutinos)

    items = tuple(manager.heap.values())
    assert len(items) == 1
    assert items[0].resolution == Resolution.pending
    for resolution in contexts_resolutions:
        assert items[0].contexts_resolutions[resolution.context].resolution == Resolution.pending

def test_store_resolve_success(trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])

    manager = MemoryTraceRecordManager()
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_resolve_success(trace_id)

    items = tuple(manager.heap.values())
    assert items[0].resolution == Resolution.success

def test_store_resolve_failure(trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])

    manager = MemoryTraceRecordManager()
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_resolve_failure(trace_id)

    items = tuple(manager.heap.values())
    assert items[0].resolution == Resolution.failure

def test_store_context_resolve_success(trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    context_resolution = contexts_resolutions[0]

    manager = MemoryTraceRecordManager()
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_context_resolve_success(trace_id, context_resolution.context)

    items = tuple(manager.heap.values())
    assert items[0].contexts_resolutions[context_resolution.context].resolution == Resolution.success

def test_store_context_resolve_failure(trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    context_resolution = contexts_resolutions[0]

    manager = MemoryTraceRecordManager()
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_context_resolve_failure(trace_id, context_resolution.context, 'some error')

    items = tuple(manager.heap.values())
    assert items[0].contexts_resolutions[context_resolution.context].resolution == Resolution.failure
