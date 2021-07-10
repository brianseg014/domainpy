
from domainpy.utils.constructable import Constructable
from domainpy.utils.dictable import Dictable
from domainpy.utils.immutable import Immutable
from domainpy.utils.traceable import Traceable


class DomainEvent(Constructable, Dictable, Immutable, Traceable):
    __version__ = 1
    __message__ = 'domain_event'

    def __eq__(self, other):
        if other is None:
            return False

        if self.__class__ != other.__class__:
            return False

        return (
            self.__stream_id__ == other.__stream_id__
            and self.__number__ == other.__number__
        )
