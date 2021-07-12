
from domainpy.typing import SystemMessage
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.utils.bus import Bus
from domainpy.utils.registry import Registry


class IEnvironment:

    def setup(
        self, 
        registry: Registry, 
        projection_bus: Bus[DomainEvent], 
        resolver_bus: Bus[SystemMessage], 
        handler_bus: Bus[SystemMessage],
        integration_bus: Bus[IntegrationEvent]
    ) -> None:
        pass

    def handle(self, message: SystemMessage):
        pass
