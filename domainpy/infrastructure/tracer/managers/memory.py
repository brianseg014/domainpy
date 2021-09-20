import typing
import datetime
import dataclasses

from domainpy.typing.infrastructure import (
    InfrastructureMessage,
    InfrastructureRecord,
)
from domainpy.exceptions import (
    IdempotencyItemError,
    TraceNotFound,
    DefinitionError,
)
from domainpy.application.command import ApplicationCommand
from domainpy.application.query import ApplicationQuery
from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.tracer.tracestore import (
    TraceResolution,
    TraceSegmentRecorder,
    TraceSegmentStore,
    TraceStore,
)
from domainpy.infrastructure.records import (
    CommandRecord,
    EventRecord,
    IntegrationRecord,
    QueryRecord,
)
from domainpy.infrastructure.mappers import Mapper


@dataclasses.dataclass
class ContextResolution:
    context: str
    resolution: str
    error: typing.Optional[str]
    timestamp: typing.Optional[float]


@dataclasses.dataclass
class Trace:
    trace_id: str
    topic: str
    message: str
    request: typing.Union[CommandRecord, QueryRecord]
    resolution: str
    version: int
    timestamp: float
    timestamp_resolution: typing.Optional[float]
    contexts_resolutions: typing.Dict[str, ContextResolution]
    contexts_resolutions_unexpected: typing.Dict[str, ContextResolution]
    integrations: typing.List[IntegrationRecord]


class MemoryTraceStore(TraceStore):
    def __init__(self, mapper: Mapper) -> None:
        self.mapper = mapper

        self.traces: typing.Dict[str, Trace] = {}

    def get_resolution(self, trace_id: str) -> TraceResolution:
        if trace_id not in self.traces:
            raise TraceNotFound()

        trace = self.traces[trace_id]
        return TraceResolution(
            resolution=trace.resolution,
            expected=len(trace.contexts_resolutions),
            completed=sum(
                1
                for rc in trace.contexts_resolutions.values()
                if rc.resolution != TraceResolution.Resolutions.pending
            ),
            errors=tuple(
                [
                    rc.error
                    for rc in trace.contexts_resolutions.values()
                    if rc.error is not None
                ]
            ),
        )

    def get_integrations(
        self, trace_id: str
    ) -> typing.Generator[IntegrationEvent, None, None]:
        if trace_id not in self.traces:
            raise TraceNotFound()

        trace = self.traces[trace_id]
        return (
            typing.cast(IntegrationEvent, self.mapper.deserialize(i))
            for i in trace.integrations
        )

    def start_trace(
        self,
        request: typing.Union[
            ApplicationCommand, ApplicationQuery, IntegrationEvent
        ],
    ) -> None:
        try:
            resolvers = getattr(request, "__resolvers__")
        except AttributeError as error:
            raise DefinitionError(
                "request should have __resolvers__: "
                f"{request.__class__.__name__}"
            ) from error

        record = typing.cast(
            typing.Union[CommandRecord, QueryRecord],
            self.mapper.serialize(request),
        )

        if record.trace_id in self.traces:
            raise IdempotencyItemError()

        epoch = datetime.datetime.utcnow().timestamp()

        epoch_resolution = None
        resolution = TraceResolution.Resolutions.pending
        if len(resolvers) == 0:
            epoch_resolution = epoch
            resolution = TraceResolution.Resolutions.success

        self.traces[record.trace_id] = Trace(
            trace_id=record.trace_id,
            topic=record.topic,
            message=record.message,
            request=record,
            resolution=resolution,
            version=1,
            timestamp=epoch,
            timestamp_resolution=epoch_resolution,
            contexts_resolutions={
                context: ContextResolution(
                    context=context,
                    resolution=TraceResolution.Resolutions.pending,
                    timestamp=None,
                    error=None,
                )
                for context in resolvers
            },
            contexts_resolutions_unexpected={},
            integrations=[],
        )

    def resolve_context(
        self, integration: typing.Union[IntegrationEvent, IntegrationRecord]
    ) -> None:
        if isinstance(integration, IntegrationEvent):
            record = typing.cast(
                IntegrationRecord, self.mapper.serialize(integration)
            )
        elif isinstance(integration, IntegrationRecord):
            record = integration

        if record.trace_id not in self.traces:
            raise TraceNotFound()

        trace = self.traces[record.trace_id]
        if record.context in trace.contexts_resolutions:
            trace.contexts_resolutions[
                record.context
            ].resolution = record.resolve
        else:
            trace.contexts_resolutions_unexpected[
                record.context
            ] = ContextResolution(
                context=record.context,
                resolution=record.resolve,
                error=record.error,
                timestamp=None,
            )
        trace.integrations.append(record)

        self._safe_try_to_resolve_trace(record.trace_id)

    def _safe_try_to_resolve_trace(self, trace_id):
        trace = self.traces[trace_id]

        # All not pending but not necessarily all same resolution
        # if no resolutions expected, True
        at_least_partial_resolved = all(
            cr.resolution != TraceResolution.Resolutions.pending
            for cr in trace.contexts_resolutions.values()
        )
        if at_least_partial_resolved:
            resolutions = set(
                cr.resolution for cr in trace.contexts_resolutions.values()
            )

            # If no resolutions expected, success
            if len(trace.contexts_resolutions) == 0:
                resolutions = set([TraceResolution.Resolutions.success])

            # Unified resolution: All success or failure
            if len(resolutions) == 1:
                trace.resolution = list(resolutions)[0]


@dataclasses.dataclass
class TraceSegment:
    trace_id: str
    topic: str
    timestamp: float
    timestamp_resolution: typing.Optional[float]
    request: InfrastructureRecord
    resolution: str
    error: typing.Optional[str]


class MemoryTraceSegmentStore(TraceSegmentStore):
    def __init__(self, mapper: Mapper) -> None:
        self.mapper = mapper

        self.segments: typing.Dict[str, TraceSegment] = {}

    def get_resolution(
        self, trace_id: str, topic: str, context: typing.Optional[str] = None
    ) -> typing.Optional[str]:
        subject = topic
        if context is not None:
            subject = f"{context}:{topic}"

        trace_segment_id = self._get_trace_segment_id(trace_id, subject)

        if trace_segment_id not in self.segments:
            raise TraceNotFound()

        trace_segment = self.segments[trace_segment_id]
        return trace_segment.resolution

    def start_trace_segment(
        self, request: InfrastructureMessage
    ) -> TraceSegmentRecorder:
        record = self.mapper.serialize(request)

        subject = record.topic
        if isinstance(record, EventRecord):
            subject = f"{record.context}:{record.topic}"

        trace_segment_id = self._get_trace_segment_id(record.trace_id, subject)

        if trace_segment_id in self.segments:
            raise IdempotencyItemError()

        epoch = datetime.datetime.utcnow().timestamp()
        self.segments[trace_segment_id] = TraceSegment(
            trace_id=record.trace_id,
            topic=record.topic,
            timestamp=epoch,
            timestamp_resolution=None,
            request=record,
            resolution=TraceResolution.Resolutions.pending,
            error=None,
        )

        return TraceSegmentRecorder(request, self)

    def resolve_trace_segment_success(
        self, request: InfrastructureMessage
    ) -> None:
        record = self.mapper.serialize(request)
        record = self.mapper.serialize(request)

        subject = record.topic
        if isinstance(record, EventRecord):
            subject = f"{record.context}:{record.topic}"

        trace_segment_id = self._get_trace_segment_id(record.trace_id, subject)

        if trace_segment_id not in self.segments:
            raise TraceNotFound()

        epoch = datetime.datetime.utcnow().timestamp()

        trace_segment = self.segments[trace_segment_id]
        trace_segment.resolution = TraceResolution.Resolutions.success
        trace_segment.timestamp_resolution = epoch

    def resolve_trace_segment_failure(
        self, request: InfrastructureMessage, exc: typing.Type[Exception]
    ) -> None:
        record = self.mapper.serialize(request)

        subject = record.topic
        if isinstance(record, EventRecord):
            subject = f"{record.context}:{record.topic}"

        trace_segment_id = self._get_trace_segment_id(record.trace_id, subject)

        if trace_segment_id not in self.segments:
            raise TraceNotFound()

        epoch = datetime.datetime.utcnow().timestamp()

        trace_segment = self.segments[trace_segment_id]
        trace_segment.resolution = TraceResolution.Resolutions.failure
        trace_segment.error = str(exc)
        trace_segment.timestamp_resolution = epoch

    @classmethod
    def _get_trace_segment_id(cls, trace_id: str, subject: str) -> str:
        return f"{trace_id}:{subject}"
