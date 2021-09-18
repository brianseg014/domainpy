from __future__ import annotations

import abc
import time
import typing
import dataclasses

from domainpy.typing.infrastructure import InfrastructureMessage
from domainpy.exceptions import Timeout
from domainpy.application.command import ApplicationCommand
from domainpy.application.query import ApplicationQuery
from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.records import IntegrationRecord
from domainpy.utils import Bus


@dataclasses.dataclass
class TraceResolution:
    class Resolutions(IntegrationEvent.Resolution):
        pending = "pending"

    resolution: str
    expected: int
    completed: int
    errors: typing.Tuple[str, ...]


class TraceStore:
    def watch_trace_resolution(
        self,
        trace_id: str,
        *,
        integration_bus: Bus = None,
        timeout_ms: int = 3000,
        backoff_ms: int = 100
    ) -> TraceResolution:
        start_time = time.time()

        while True:
            if (time.time() - start_time) * 1000 > timeout_ms:
                raise Timeout()

            trace_resolution = self.get_resolution(trace_id)
            if (
                trace_resolution.resolution
                != TraceResolution.Resolutions.pending
            ):
                if integration_bus is not None:
                    integrations = list(self.get_integrations(trace_id))
                    for i in integrations:
                        integration_bus.publish(i)

                return trace_resolution

            time.sleep(backoff_ms / 1000)

    @abc.abstractmethod
    def get_resolution(self, trace_id: str) -> TraceResolution:
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_integrations(
        self, trace_id: str
    ) -> typing.Generator[IntegrationEvent, None, None]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def start_trace(
        self,
        request: typing.Union[
            ApplicationCommand, ApplicationQuery, IntegrationEvent
        ],
    ) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def resolve_context(
        self, integration: typing.Union[IntegrationEvent, IntegrationRecord]
    ) -> None:
        pass  # pragma: no cover


class TraceSegmentStore(abc.ABC):
    @abc.abstractmethod
    def get_resolution(
        self, trace_id: str, topic: str
    ) -> typing.Optional[str]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def start_trace_segment(
        self, request: InfrastructureMessage
    ) -> TraceSegmentRecorder:
        pass  # pragma: no cover

    @abc.abstractmethod
    def resolve_trace_segment_success(
        self, request: InfrastructureMessage
    ) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def resolve_trace_segment_failure(
        self,
        request: InfrastructureMessage,
        exc: typing.Type[Exception],
    ) -> None:
        pass  # pragma: no cover


class TraceSegmentRecorder:
    def __init__(
        self,
        request: InfrastructureMessage,
        trace_segment_store: TraceSegmentStore,
    ) -> None:
        self.request = request
        self.trace_segment_store = trace_segment_store

    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            self.trace_segment_store.resolve_trace_segment_success(
                self.request
            )
        else:
            self.trace_segment_store.resolve_trace_segment_failure(
                self.request, exc_value
            )
