import uuid
import typing
import datetime
import functools

from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable
from domainpy.utils.contextualized import Contextualized


class IntegrationEvent(SystemData, Traceable, Contextualized):
    __resolve__: str
    __timestamp__: float
    __error__: typing.Optional[str]
    __version__: int = 1

    class Resolution:
        success = "success"
        failure = "failure"

    @classmethod
    def stamp(
        cls, *, trace_id: str = None, context: str = None
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
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
            __trace_id__=_trace_id,
            __context__=_context,
        )


class SuccessIntegrationEvent(IntegrationEvent):
    __resolve__: str = IntegrationEvent.Resolution.success
    __error__: typing.Optional[str] = None


class FailureIntegrationEvent(IntegrationEvent):
    __resolve__: str = IntegrationEvent.Resolution.failure
