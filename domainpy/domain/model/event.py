import uuid
import datetime
import functools

from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable
from domainpy.utils.contextualized import Contextualized


class DomainEvent(SystemData, Traceable, Contextualized):
    __stream_id__: str
    __number__: int
    __timestamp__: float
    __version__: int = 1

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, self.__class__):
            return False

        return (
            self.__stream_id__ == o.__stream_id__
            and self.__number__ == o.__number__
        )

    @classmethod
    def stamp(
        cls,
        stream_id: str,
        number: int,
        *,
        trace_id: str = None,
        context: str = None
    ) -> functools.partial:
        _trace_id = trace_id
        if _trace_id is None:
            _trace_id = Traceable.__trace_id__

        if _trace_id is None:
            _trace_id = str(uuid.uuid4())

        _context = context
        if _context is None:
            _context = Contextualized.__context__

        return functools.partial(
            cls,
            __stream_id__=stream_id,
            __number__=number,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
            __trace_id__=_trace_id,
            __context__=_context,
        )
