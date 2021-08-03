import abc
import typing
import dataclasses

from domainpy.infrastructure.records import CommandRecord


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


class TraceRecordManager(abc.ABC):
    @abc.abstractmethod
    def get_trace_contexts(
        self, trace_id: str
    ) -> typing.Generator[ContextResolution, None, None]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def store_in_progress(
        self,
        trace_id: str,
        command_record: CommandRecord,
        contexts_resolutions: typing.Tuple[str, ...],
    ) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def store_resolve_success(self, trace_id: str) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def store_resolve_failure(self, trace_id: str) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def store_context_resolve_success(
        self, trace_id: str, context: str
    ) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def store_context_resolve_failure(
        self, trace_id: str, context: str, error: str
    ) -> None:
        pass  # pragma: no cover
