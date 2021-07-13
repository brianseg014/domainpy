
from domainpy.typing import SystemMessage
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.utils.bus import Bus
from domainpy.utils.registry import Registry


class IEnvironment:

    def setup_registry(self, registry: Registry) -> None:
        pass

    def setup_publisher_domain_bus(self, publisher_domain_bus: Bus[DomainEvent]) -> None:
        pass

    def setup_publisher_integration_bus(self, publisher_integration_bus: Bus[IntegrationEvent]) -> None:
        pass

    def setup_projection_bus(self, projection_bus: Bus[DomainEvent]) -> None:
        pass

    def setup_resolver_bus(self, resolver_bus: Bus[SystemMessage], publisher_integration_bus: Bus[IntegrationEvent]) -> None:
        pass

    def setup_handler_bus(self, handler_bus: Bus[SystemMessage], registry: Registry) -> None:
        pass
    
    def handle(self, message: SystemMessage):
        pass
