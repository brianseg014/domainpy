from uuid import uuid4
from datetime import datetime

from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.utils.dictable import Dictable

class IntegrationEvent(Constructable, Immutable, Dictable):

    def __init__(self, *args, **kwargs):
        self.__dict__.update({
            '__trace_id__': kwargs.pop('__trace_id__', str(uuid4())),
            '__timestamp__': str(datetime.now()),
            '__message__': 'integration'
        })
        
        super(IntegrationEvent, self).__init__(*args, **kwargs)
