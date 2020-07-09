import inspect

from domainpy.domain.events import DomainEvent, mutatorfor

"""
def apply_event_created_class(event: DomainEvent):
    def inner_class(cls):
        if not issubclass(cls, DomainEntity):
            raise TypeError("{} must be a subclass of {}".format(
                    cls, DomainEntity
                ))
        
        original_method = cls.__create__
        
        def __create__(**kwargs):
            return original_method(event, **kwargs)
            
        cls.__create__ = __create__
        mutatorfor(event)(cls.__create__)
        
        return cls
    return inner_class
"""   
    
class DomainEntity:
    
    __identifiedby__ = None
    __orderedby__ = None
    
    @classmethod
    def __create__(cls, created: DomainEvent):
        self = cls(**created.__dict__)
        self.__publish__(created)
        
        return self
    
    def __apply__(self, event: DomainEvent):
        event.__mutate__(self)
        self.__publish__(event)
 
    def __publish__(self, event):
        pass
    
    def __hash__(self):
        return hash(self.__dict__[self.__class__.__identifiedby__])
        
    def __eq__(self, other):
        if other is None:
            return False
            
        return (
            (
                isinstance(other, self.__class__)
                or isinstance(other, self.__dict__[self.__class__.__identifiedby__].__class__)
            )
            and self.__hash__() == other.__hash__()
        )
        
    def __ne__(self, other):
        return not self == other
        
    def __gt__(self, other):
        orderby = self.__class__.__orderedby__
        
        if other is None:
            return True
        
        if other.__dict__[orderby] is None:
            return True
            
        if self.__dict__[orderby] is None:
            return False
            
        return self.__dict__[orderby] > other.__dict__[orderby]
            
    def __ge__(self, other):
        orderby = self.__class__.__orderedby__
        
        if other is None:
            return True
        
        if other.__dict__[orderby] is None:
            return True
            
        if self.__dict__[orderby] is None:
            return False
            
        return self.__dict__[orderby] >= other.__dict__[orderby]
    
    def __lt__(self, other):
        orderby = self.__class__.__orderedby__
        
        if other is None:
            return True
        
        if other.__dict__[orderby] is None:
            return True
            
        if self.__dict__[orderby] is None:
            return False
            
        return self.__dict__[orderby] < other.__dict__[orderby]
    
    def __le__(self, other):
        orderby = self.__class__.__orderedby__
        
        if other is None:
            return True
        
        if other.__dict__[orderby] is None:
            return True
            
        if self.__dict__[orderby] is None:
            return False
            
        return self.__dict__[orderby] <= other.__dict__[orderby]


def usecreated(event: DomainEvent):
    def inner_class(cls):
        if not issubclass(cls, DomainEntity):
            raise TypeError("{} must be a subclass of {}".format(
                    cls, DomainEntity
                ))
        
        mutatorfor(event)(cls.__create__)
        
        return cls
    
    return inner_class