import dataclasses
import typing

from domainpy.infrastructure.records import CommandRecord
from domainpy.infrastructure.tracer.recordmanager import (
    TraceRecordManager,
    ContextResolution,
    Resolution,
)
from domainpy.utils.bus import Bus


@dataclasses.dataclass(frozen=True)
class TraceResolution:
    trace_id: str
    resolution: str
    errors: typing.Optional[typing.Tuple[str, ...]] = None


class TraceStore:
    def __init__(
        self,
        record_manager: TraceRecordManager,
        resolver_bus: Bus[TraceResolution],
    ) -> None:
        self.record_manager = record_manager
        self.resolver_bus = resolver_bus

    def store_in_progress(
        self,
        trace_id: str,
        record: CommandRecord,
        contexts_resolutions: typing.Tuple[str, ...],
    ) -> None:
        self.record_manager.store_in_progress(
            trace_id,
            record,
            contexts_resolutions,
        )
        self.trace_resolution(trace_id)

    def store_context_success(self, trace_id: str, context: str) -> None:
        self.record_manager.store_context_resolve_success(trace_id, context)
        self.trace_resolution(trace_id)

    def store_context_failure(
        self, trace_id: str, context: str, error: str
    ) -> None:
        self.record_manager.store_context_resolve_failure(
            trace_id, context, error
        )
        self.trace_resolution(trace_id)

    def trace_resolution(self, trace_id: str) -> None:
        trace_contexts = tuple(
            self.record_manager.get_trace_contexts(trace_id)
        )

        if self.is_all_trace_context_resolved(trace_contexts):
            if self.is_all_trace_context_resolved_success(trace_contexts):

                self.record_manager.store_resolve_success(trace_id)
                self.resolver_bus.publish(
                    TraceResolution(trace_id, Resolution.success)
                )

            else:

                self.record_manager.store_resolve_failure(trace_id)
                self.resolver_bus.publish(
                    TraceResolution(
                        trace_id,
                        Resolution.failure,
                        errors=tuple(self.get_trace_errors(trace_contexts)),
                    )
                )

    @classmethod
    def is_all_trace_context_resolved(
        cls, trace_contexts: typing.Tuple[ContextResolution, ...]
    ) -> bool:
        return all(
            tc.resolution != Resolution.pending for tc in trace_contexts
        )

    @classmethod
    def is_all_trace_context_resolved_success(
        cls, trace_contexts: typing.Tuple[ContextResolution, ...]
    ) -> bool:
        return all(
            tc.resolution == Resolution.success for tc in trace_contexts
        )

    @classmethod
    def get_trace_errors(
        cls, trace_contexts: typing.Tuple[ContextResolution, ...]
    ) -> typing.Generator[str, None, None]:
        return (
            tc.error
            for tc in trace_contexts
            if tc.resolution == Resolution.failure and tc.error is not None
        )
