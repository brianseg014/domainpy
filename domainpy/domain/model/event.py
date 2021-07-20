
from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable
from domainpy.typing.infrastructure import EventRecordDict


class DomainEvent(SystemData[EventRecordDict], Traceable):
    __stream_id__: str
    __number__: int
    __timestamp__: float
    __version__: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DomainEvent):
            return False

        if other is None:
            return False

        if self.__class__ != other.__class__:
            return False

        return (
            self.__stream_id__ == other.__stream_id__
            and self.__number__ == other.__number__
        )
