
from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.utils.dictable import Dictable
from domainpy.utils.traceable import Traceable


class ApplicationCommand(Constructable, Dictable, Immutable, Traceable):
    __version__ = 1
    __message__ = 'command'

    class Struct(Constructable, Dictable, Immutable):
        pass
    