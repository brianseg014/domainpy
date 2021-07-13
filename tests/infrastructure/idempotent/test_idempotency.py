import pytest
from unittest import mock

from domainpy.exceptions import IdempotencyItemError
from domainpy.infrastructure.idempotent.idempotency import Idempotency


def test_idempotency_sucess():
    record_manager = mock.MagicMock()
    record = { 'trace_id': '', 'topic': '' }

    with Idempotency(record, record_manager) as record:
        pass

    record_manager.store_in_progress.assert_called
    record_manager.store_success.assert_called

def test_idempotency_failure():
    record_manager = mock.MagicMock()
    record = { 'trace_id': '', 'topic': '' }

    with pytest.raises(Exception):
        with Idempotency(record, record_manager) as record:
            raise Exception()

    record_manager.store_in_progress.assert_called
    record_manager.store_failure.assert_called

def test_idempotency_already_exists():
    record_manager = mock.MagicMock()
    record_manager.store_in_progress = mock.Mock(side_effect=IdempotencyItemError())
    record = { 'trace_id': '', 'topic': '' }
    
    with Idempotency(record, record_manager) as record:
        assert record is None
