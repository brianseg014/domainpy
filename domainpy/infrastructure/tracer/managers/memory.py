import typing
import datetime
import dataclasses

from domainpy.infrastructure.tracer.recordmanager import (
    TraceRecordManager,
    ContextResolution,
    Resolution,
)
from domainpy.infrastructure.records import CommandRecord


@dataclasses.dataclass
class Trace:
    command_record: CommandRecord
    resolution: str
    contexts_resolutions: typing.Dict[str, ContextResolution]


class MemoryTraceRecordManager(TraceRecordManager):
    def __init__(self) -> None:
        self.heap: typing.Dict[str, Trace] = {}

    def get_trace_contexts(
        self, trace_id: str
    ) -> typing.Generator[ContextResolution, None, None]:
        return (cr for cr in self.heap[trace_id].contexts_resolutions.values())

    def store_in_progress(
        self,
        trace_id: str,
        command_record: CommandRecord,
        contexts_resolutions: typing.Tuple[str, ...],
    ) -> None:
        resolutions: typing.Dict[str, ContextResolution] = {
            context_name: ContextResolution(
                context=context_name,
                resolution=Resolution.pending,
            )
            for context_name in contexts_resolutions
        }

        trace = Trace(
            command_record=command_record,
            resolution=Resolution.pending,
            contexts_resolutions=resolutions,
        )

        self.heap[trace_id] = trace

    def store_resolve_success(self, trace_id: str) -> None:
        self.heap[trace_id].resolution = Resolution.success

    def store_resolve_failure(self, trace_id: str) -> None:
        self.heap[trace_id].resolution = Resolution.failure

    def store_context_resolve_success(
        self, trace_id: str, context: str
    ) -> None:
        trace = self.heap[trace_id]
        context_resolution = trace.contexts_resolutions[context]
        context_resolution.resolution = Resolution.success
        context_resolution.timestamp_resolution = datetime.datetime.timestamp(datetime.datetime.now())

    def store_context_resolve_failure(
        self, trace_id: str, context: str, error: str
    ) -> None:
        trace = self.heap[trace_id]
        context_resolution = trace.contexts_resolutions[context]
        context_resolution.resolution = Resolution.failure
        context_resolution.timestamp_resolution = datetime.datetime.timestamp(datetime.datetime.now())
        context_resolution.error = error
