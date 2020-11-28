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
    