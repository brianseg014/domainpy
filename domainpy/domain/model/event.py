
from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable


class DomainEvent(SystemData, Traceable):
    __stream_id__: str
    __number__: int
    __timestamp__: float
    __version__: int = 1

    def __eq__(self, other: 'DomainEvent'):
        if other is None:
            return False

        if self.__class__ != other.__class__:
            return False

        return (
            self.__stream_id__ == other.__stream_id__
            and self.__number__ == other.__number__
        )
