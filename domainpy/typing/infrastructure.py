import typing

JsonStr = str
CommandRecordDict = typing.TypedDict(
    "CommandRecordDict",
    trace_id=str,
    topic=str,
    version=int,
    timestamp=float,
    message=float,
    payload=dict,
)
IntegrationRecordDict = typing.TypedDict(
    "IntegrationRecordDict",
    trace_id=str,
    context=str,
    topic=str,
    resolve=str,
    error=str,
    version=int,
    timestamp=float,
    message=str,
    payload=dict,
)
EventRecordDict = typing.TypedDict(
    "EventRecordDict",
    stream_id=str,
    number=int,
    topic=str,
    version=int,
    timestamp=float,
    trace_id=str,
    message=str,
    context=str,
    payload=dict,
)
RecordDict = typing.Union[
    CommandRecordDict, IntegrationRecordDict, EventRecordDict
]

TMessage = typing.TypeVar("TMessage")
TRecord = typing.TypeVar("TRecord")
TRecordDict = typing.TypeVar("TRecordDict")
