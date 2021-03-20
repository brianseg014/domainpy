
from collections import namedtuple


EventRecord = namedtuple(
    'EventRecord', 
    ('stream_id', 'number', 'topic', 'version', 'timestamp', 'message', 'payload')
)


class EventMapper:
    
    def __init__(self):
        self.map = dict()
        
    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls
    
    def serialize(self, event):
        if hasattr(event.__class__, '__annotations__'):
            attrs = event.__class__.__dict__['__annotations__']
            
            return EventRecord(
                stream_id=event.__aggregate_id__, # pylint: disable=maybe-no-member
                number=event.__number__, # pylint: disable=maybe-no-member
                topic=event.__class__.__name__,
                version=event.__version__, # pylint: disable=maybe-no-member
                timestamp=event.__timestamp__, # pylint: disable=maybe-no-member
                message=event.__message__,
                payload=event.__to_dict__()
            )
        else:
            raise NotImplementedError(
                f'{event.__class__.__name__} should have annotations'
            )
    
    def deserialize(self, event_record: EventRecord):
        event_class = self.map[event_record.topic]
        event = event_class.__from_dict__(event_record.payload)
        
        event.__dict__.update({
            '__aggregate_id__': event_record.stream_id,
            '__number__': event_record.number,
            '__version__': event_record.version,
            '__timestamp__': event_record.timestamp,
            '__message__': event_record.message
        })
        
        return event
    