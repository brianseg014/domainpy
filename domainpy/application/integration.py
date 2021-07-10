
from domainpy.application.command import ApplicationCommand
from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.utils.dictable import Dictable
from domainpy.utils.traceable import Traceable



class IntegrationEvent(Constructable, Dictable, Immutable, Traceable):
    __version__ = 1
    __message__ = 'integration_event'
    __error__ = None

    class Resolution:
        success = 'success'
        failure = 'failure'
    
    @classmethod
    def __from_command__(cls, command: ApplicationCommand, **kwargs):
        payload = {
            k:v 
            for k,v in command.__dict__.items() 
            if not k.startswith('__')
        }
        return cls(**payload, **kwargs)
    