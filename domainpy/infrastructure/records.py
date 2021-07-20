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
class IntegrationRecord:
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
class EventRecord:
    stream_id: str
    number: int
    topic: str
    version: int
    timestamp: float
    trace_id: str
    message: str
    context: str
    payload: dict


@dataclasses.dataclass
class TraceRecord:
    class StatusCode:
        CODE_200 = 200

    class Resolution:
        pending = "pending"
        success = "success"
        failure = "failure"

    @dataclasses.dataclass
    class ContextResolution:
        context: str
        resolution: str
        timestamp_resolution: typing.Optional[float] = None
        error: typing.Optional[str] = None

    trace_id: str
    command: CommandRecord
    status_code: int
    number: int
    resolution: str
    version: int
    timestamp: float
    contexts_resolutions: tuple[ContextResolution]
    timestamp_resolution: typing.Optional[float] = None
