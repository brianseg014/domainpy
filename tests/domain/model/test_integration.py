
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent


def test_integration_from_command():
    class BasicCommand(ApplicationCommand):
        some_property: str

    class BasicIntegration(IntegrationEvent):
        some_property: str

    c = BasicCommand(some_property='x')
    i = BasicIntegration.__from_command__(c)

    assert i.some_property == 'x'