
from collections import namedtuple


EventRecord = namedtuple(
    'EventRecord', 
    ('aggregate_id', 'number', 'topic', 'version', 'timestamp', 'payload')
)


class EventMapper:
    
    def __init__(self):
        self.map = dict()
        
    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls
    
    def serialize(self, event):
        return event.__to_event_record__()
    
    def deserialize(self, event_record):
        event_class = self.map[event_record.topic]
        
        return event_class.from_event_record(event_record)
