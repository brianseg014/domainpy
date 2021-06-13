
from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.utils.dictable import Dictable
from domainpy.utils.traceable import Traceable


class DomainEvent(Constructable, Immutable, Dictable, Traceable):
    
    def __init__(self, *args, **kwargs):
        self.__dict__.update({
            '__aggregate_id__': kwargs.pop('__aggregate_id__', None),
            '__number__': kwargs.pop('__number__', None),
            '__version__': kwargs.pop('__version__', None),
            '__timestamp__': kwargs.pop('__timestamp__', None),
            '__trace_id__': kwargs.pop('__trace_id__', Traceable.__trace_id__),
            '__message__': 'event'
        })
        
        super(DomainEvent, self).__init__(*args, **kwargs)
    
    def __eq__(self, other):
        if other is None:
            return False

        if self.__class__ != other.__class__:
            return False

        return (
            self.__aggregate_id__ == other.__aggregate_id__
            and self.__number__ == other.__number__
        )
