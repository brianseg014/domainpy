import dataclasses
import enum
import typing


@dataclasses.dataclass(frozen=True)
class CommandRecord:
    trace_id: str
    topic: str
    version: int
    timestamp: float
    message: float
    payload: dict


@dataclasses.dataclass(frozen=True)
class IntegrationRecord:
    trace_id: str
    context: str
    topic: str
    resolve: str
    error: str
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
    class StatusCode(enum.IntEnum):
        CODE_200 = 200

    class Resolution(enum.Enum):
        pending = "pending"
        success = "success"
        failure = "failure"

    @dataclasses.dataclass
    class ContextResolution:
        context: str
        resolution: "TraceRecord.Resolution"
        timestamp_resolution: typing.Optional[float] = None
        error: typing.Optional[str] = None

    trace_id: str
    command: CommandRecord
    status_code: "TraceRecord.StatusCode"
    number: int
    resolution: "TraceRecord.Resolution"
    version: int
    timestamp: float
    contexts_resolutions: tuple[ContextResolution]
    timestamp_resolution: typing.Optional[float] = None
