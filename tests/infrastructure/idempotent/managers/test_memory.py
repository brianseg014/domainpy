
import pytest

from domainpy.exceptions import IdempotencyItemError
from domainpy.infrastructure.idempotent.managers.memory import MemoryIdempotencyRecordManager


def test_store_in_progress():
    record = {
        'trace_id': 'some-trace-id',
        'topic': 'some-topic'
    }

    record_manager = MemoryIdempotencyRecordManager()
    record_manager.store_in_progress(record)

    assert len(record_manager.heap) == 1

def test_store_in_progress_already_exists_in_progress():
    record = {
        'trace_id': 'some-trace-id',
        'topic': 'some-topic'
    }

    record_manager = MemoryIdempotencyRecordManager()
    record_manager.store_in_progress(record)

    with pytest.raises(IdempotencyItemError):
        record_manager.store_in_progress(record)

def test_store_in_progress_already_exists_in_success():
    record = {
        'trace_id': 'some-trace-id',
        'topic': 'some-topic'
    }

    record_manager = MemoryIdempotencyRecordManager()
    record_manager.store_in_progress(record)
    record_manager.store_success(record)

    with pytest.raises(IdempotencyItemError):
        record_manager.store_in_progress(record)

def test_store_in_progress_already_exists_in_failure():
    record = {
        'trace_id': 'some-trace-id',
        'topic': 'some-topic'
    }

    record_manager = MemoryIdempotencyRecordManager()
    record_manager.store_in_progress(record)
    record_manager.store_failure(record, Exception('some-error-description'))
    record_manager.store_in_progress(record)
