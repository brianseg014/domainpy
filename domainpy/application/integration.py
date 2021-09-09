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
        compensate = "compensate"

    @classmethod
    def stamp(
        cls, *, trace_id: str = None, context: str = None
    ) -> functools.partial:
        _trace_id = trace_id
        if _trace_id is None:
            _trace_id = Traceable.__trace_id__

        _context = context
        if _context is None:
            _context = Contextualized.__context__

        return functools.partial(
            cls,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
            __trace_id__=_trace_id,
            __context__=_context,
        )

    def __str__(self) -> str:
        return (
            super().__str__()
            + " with "
            + str({"trace_id": self.__trace_id__, "context": self.__context__})
        )

    def __repr__(self) -> str:
        return (
            super().__repr__()
            + " with "
            + repr(
                {"trace_id": self.__trace_id__, "context": self.__context__}
            )
        )


class SuccessIntegrationEvent(IntegrationEvent):
    __resolve__: str = IntegrationEvent.Resolution.success
    __error__: typing.Optional[str] = None


class FailureIntegrationEvent(IntegrationEvent):
    __resolve__: str = IntegrationEvent.Resolution.failure


class CompensateIntegrationEvent(IntegrationEvent):
    __resolve__: str = IntegrationEvent.Resolution.compensate
    __error__: typing.Optional[str] = None


class ScheduleIntegartionEvent(SuccessIntegrationEvent):
    __publish_at_field__: str
