

from domainpy.exceptions import IdempotencyItemError 
from domainpy.infrastructure.idempotent.recordmanager import IdempotencyRecordManager


class Idempotency:

    def __init__(self, record: dict, record_manager: IdempotencyRecordManager):
        self.record = record
        self.record_manager = record_manager

    def __enter__(self):
        record = self.record
        try:
            self.record_manager.store_in_progress(record)
            return record
        except IdempotencyItemError:
            return None
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        record = self.record
        if exc_type is None:
            self.record_manager.store_success(record)
        else:
            self.record_manager.store_failure(record, exc_value)
        

def idempotent(record_manager: IdempotencyRecordManager):
    def inner_function(func):

        def wrapper(record):
            with Idempotency(record, record_manager) as record:
                if record is not None:
                    func(record)
            
        return wrapper
    return inner_function