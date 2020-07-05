import inspect

from domainpy.domain.events import DomainEvent

def _getcreatedtype(cls):
    return cls.__createdtype__
        
   
class DomainEntity:
    
    @classmethod
    def __create__(cls, *args, **kwargs):
        created_event_type = _getcreatedtype(cls)
        event = created_event_type(*args, **kwargs)
        
        self = event.__mutate__(None)
        self.__publish__(event)
        
        return self
    
    def __apply__(self, event: DomainEvent):
        event.__mutate__(self)
        
        self.__publish__(event)
 
    def __publish__(self, event):
        pass
