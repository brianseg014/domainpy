import typing

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


class SuccessIntegrationEvent(IntegrationEvent):
    __resolve__: str = IntegrationEvent.Resolution.success
    __error__: typing.Optional[str] = None


class FailureIntegrationEvent(IntegrationEvent):
    __resolve__: str = IntegrationEvent.Resolution.failure
