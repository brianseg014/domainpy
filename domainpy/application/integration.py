import typing

from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable


class IntegrationEvent(SystemData, Traceable):
    __resolve__: str
    __timestamp__: float
    __error__: typing.Optional[str]
    __version__: int

    class Resolution:
        success = "success"
        failure = "failure"
