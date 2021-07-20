from domainpy.utils.data import SystemData
from domainpy.utils.traceable import Traceable
from domainpy.typing.infrastructure import CommandRecordDict  # type: ignore


class ApplicationCommand(SystemData[CommandRecordDict], Traceable):
    __timestamp__: float
    __version__: int = 1
    __message__: str = "command"

    class Struct(SystemData):
        pass
