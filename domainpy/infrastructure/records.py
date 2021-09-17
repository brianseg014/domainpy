import typing
import dataclasses


@dataclasses.dataclass(frozen=True)
class CommandRecord:
    trace_id: str
    topic: str
    version: int
    timestamp: float
    message: str
    payload: dict


@dataclasses.dataclass(frozen=True)
class QueryRecord:
    trace_id: str
    topic: str
    version: int
    timestamp: float
    message: str
    payload: dict


@dataclasses.dataclass(frozen=True)
class IntegrationRecord:  # pylint: disable=too-many-instance-attributes
    trace_id: str
    context: str
    topic: str
    resolve: str
    error: typing.Optional[str]
    version: int
    timestamp: float
    message: str
    payload: dict


@dataclasses.dataclass(frozen=True)
class EventRecord:  # pylint: disable=too-many-instance-attributes
    stream_id: str
    number: int
    topic: str
    version: int
    timestamp: float
    trace_id: str
    message: str
    context: str
    payload: dict
