
from domainpy.infrastructure.eventmapper import EventRecord
from domainpy.infrastructure.eventsourced.recordmanager import (
    RecordManager,
    Session
)

class MemoryRecordManager(RecordManager):
    
    def __init__(self):
        self._heap = []
        
    def session(self):
         return MemorySession(self)
     
    def find(self, aggregate_id: str):
        return (
            er
            for er in self._heap
            if er.aggregate_id == aggregate_id
        )
        

class MemorySession(Session):
    
    def __init__(self, record_manager):
        self.record_manager = record_manager
        
        self._heap = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        self.rollback()
    
    def append(self, event_record: EventRecord):
        if event_record is None:
            raise TypeError('event_record cannot be none')
        
        self._heap.append(event_record)
    
    def commit(self):
        self.record_manager._heap.extend(self._heap)
    
    def rollback(self):
        pass
