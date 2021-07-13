
import typing

from domainpy.exceptions import IdempotencyItemError
from domainpy.infrastructure.idempotent.recordmanager import IdempotencyRecordManager


class MemoryIdempotencyRecordManager(IdempotencyRecordManager):

    def __init__(self, *args, **kwargs):
        self.heap = []

    def store_in_progress(self, record: dict):
        if not self.exists_in_progress_or_success(record['trace_id'], record['topic']):
            self.heap.append({
                'trace_id': record['trace_id'],
                'topic': record['topic'],
                'payload': record,
                'status': 'progress',
                'error': None
            })
        else:
            raise IdempotencyItemError()

    def store_success(self, record: dict):
        record = self.get_record(record['trace_id'], record['topic'])
        record['status'] = 'success'

    def store_failure(self, record: dict, exc: typing.Type[Exception]):
        record = self.get_record(record['trace_id'], record['topic'])
        record['status'] = 'failure'

    def get_record(self, trace_id: str, topic: str) -> dict:
        return next(
            r for r in self.heap 
            if r['trace_id'] == trace_id
            and r['topic'] == topic
        )

    def exists_in_progress_or_success(self, trace_id: dict, topic: str) -> bool:
        return any(
            True for r in self.heap 
            if r['trace_id'] == trace_id
            and r['topic'] == topic
            and r['status'] in ['progress', 'success']
        )

    