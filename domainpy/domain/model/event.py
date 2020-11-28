import json
import time
from datetime import datetime, date

from domainpy.domain.model.value_object import ValueObject
from domainpy.domain.model.exceptions import EventParameterIsNotValueObjectError
from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.utils.dictable import Dictable
from domainpy.infrastructure.eventmapper import EventMapper, EventRecord


class DomainEvent(Constructable, Immutable, Dictable):
    
    def __init__(self, *args, **kwargs):
        self.__dict__.update({
            '__aggregate_id__': kwargs.pop('__aggregate_id__', None),
            '__number__': kwargs.pop('__number__', None),
            '__version__': kwargs.pop('__version__', None),
            '__timestamp__': kwargs.pop('__timestamp__', None)
        })
        
        super(DomainEvent, self).__init__(*args, **kwargs)
    
    @classmethod
    def from_event_record(cls, event_record):
        event = cls.__from_dict__(event_record.payload)
        
        event.__dict__.update({
            '__aggregate_id__': event_record.aggregate_id,
            '__number__': event_record.number,
            '__version__': event_record.version,
            '__timestamp__': event_record.timestamp
        })
        
        return event
    
    def __to_event_record__(self):
        if hasattr(self.__class__, '__annotations__'):
            attrs = self.__class__.__dict__['__annotations__']
            
            payload = {}
            for k in attrs:
                payload[k] = self.__dict__[k].__to_dict__()
            
            return EventRecord(
                aggregate_id=self.__aggregate_id__, # pylint: disable=maybe-no-member
                number=self.__number__, # pylint: disable=maybe-no-member
                topic=self.__class__.__name__,
                version=self.__version__, # pylint: disable=maybe-no-member
                timestamp=self.__timestamp__, # pylint: disable=maybe-no-member
                payload=self.__to_dict__()
            )
