from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable
from domainpy.utils.contextualized import Contextualized


class DomainEvent(SystemData, Traceable, Contextualized):
    __stream_id__: str
    __number__: int
    __timestamp__: float
    __version__: int = 1
