from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable
from domainpy.utils.contextualized import Contextualized


class DomainEvent(SystemData, Traceable, Contextualized):
    __stream_id__: str
    __number__: int
    __timestamp__: float
    __version__: int = 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return (
            self.__stream_id__ == other.__stream_id__
            and self.__number__ == other.__number__
        )
