import typing

from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable
from domainpy.typing.infrastructure import (  # type: ignore
    IntegrationRecordDict,
)


class IntegrationEvent(SystemData[IntegrationRecordDict], Traceable):
    __resolve__: str
    __timestamp__: float
    __error__: typing.Optional[str]
    __version__: int

    class Resolution:
        success = "success"
        failure = "failure"
