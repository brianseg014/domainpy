import time
from uuid import uuid4

from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.utils.dictable import Dictable
from domainpy.utils.traceable import Traceable

from domainpy.application.command import ApplicationCommand


class IntegrationEvent(Constructable, Immutable, Dictable, Traceable):

    def __init__(self, *args, **kwargs):
        self.__dict__.update({
            '__trace_id__': kwargs.pop('__trace_id__', Traceable.__trace_id__),
            '__timestamp__': time.time(),
            '__message__': 'integration',
            '__error__': kwargs.pop('__error__', None)
        })
        
        super(IntegrationEvent, self).__init__(*args, **kwargs)

    @classmethod
    def from_command(cls, command: ApplicationCommand, **kwargs):
        payload = {
            k:v 
            for k,v in command.__dict__.items() 
            if not k.startswith('__')
        }
        return cls(**payload, **kwargs)

    class Resolution:
        success = 'success'
        failure = 'failure'