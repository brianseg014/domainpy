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


def fromdict(
    dct: dict,
) -> typing.Union[CommandRecord, IntegrationRecord, EventRecord]:
    message = dct["message"]
    if message == "command":
        return CommandRecord(**dct)

    if message == "integration_event":
        return IntegrationRecord(**dct)

    if message == "domain_event":
        return EventRecord(**dct)

    raise ValueError(
        "dct[message] should be one of command, "
        "integration_event or domain_event"
    )


def asdict(
    record: typing.Union[CommandRecord, IntegrationRecord, EventRecord]
) -> dict:
    return dataclasses.asdict(record)
