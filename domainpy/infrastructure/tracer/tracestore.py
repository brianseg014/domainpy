import abc
import time
import typing
import dataclasses

from domainpy.exceptions import Timeout
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.records import IntegrationRecord
from domainpy.utils import Bus


@dataclasses.dataclass
class TraceResolution:
    class Resolutions(IntegrationEvent.Resolution):
        pending = "pending"

    resolution: str
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
        pass

    @abc.abstractmethod
    def get_integrations(
        self, trace_id: str
    ) -> typing.Generator[IntegrationEvent, None, None]:
        pass

    @abc.abstractmethod
    def start_trace(self, command: ApplicationCommand) -> None:
        pass

    @abc.abstractmethod
    def resolve_context(
        self, integration: typing.Union[IntegrationEvent, IntegrationRecord]
    ) -> None:
        pass
