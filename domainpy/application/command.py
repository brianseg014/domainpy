import datetime
import functools

from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable


class ApplicationCommand(SystemData, Traceable):
    __timestamp__: float
    __version__: int = 1
    __message__: str = "command"

    class Struct(SystemData):
        pass

    @classmethod
    def stamp(cls, *, trace_id: str = None) -> functools.partial:
        _trace_id = trace_id
        if _trace_id is None:
            _trace_id = Traceable.__trace_id__

        return functools.partial(
            cls,
            __timestamp__=datetime.datetime.utcnow().timestamp(),
            __trace_id__=_trace_id,
        )

    def __str__(self) -> str:
        return (
            super().__str__() + " with " + str({"trace_id": self.__trace_id__})
        )

    def __repr__(self) -> str:
        return (
            super().__repr__()
            + " with "
            + repr({"trace_id": self.__trace_id__})
        )
