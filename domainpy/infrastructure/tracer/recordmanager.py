import abc
import typing

from domainpy.infrastructure.records import TraceRecord


class TraceRecordManager(abc.ABC):
    @abc.abstractmethod
    def get_trace_contexts(
        self, trace_id: str
    ) -> typing.Tuple[TraceRecord.ContextResolution]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def store_in_progress(
        self,
        command: dict,
        contexts_resolutions: typing.Tuple[TraceRecord.ContextResolution],
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
