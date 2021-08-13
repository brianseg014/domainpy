import typing
from unittest import mock

from domainpy.application.service import ApplicationService
from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.publishers.base import IPublisher
from domainpy.utils import bus_subscribers as subs
from domainpy.typing.application import SystemMessage


def test_application_service_subscriber():
    class Service(ApplicationService):
        def handle(self, message: SystemMessage) -> None:
            self.proof_of_work(message)

        def proof_of_work(self, *args, **kwargs):
            pass

    service = Service()
    service.proof_of_work = mock.Mock()

    command = ApplicationCommand(__timestamp__=0.0)

    x = subs.ApplicationServiceSubscriber(service)
    x.__route__(command)

    service.proof_of_work.assert_called_with(command)

def test_publisher_subscriber():
    class Publisher(IPublisher):
        def publish(self, messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]]):
            self.proof_of_work(messages)

        def proof_of_work(self, *args, **kwargs):
            pass

    publisher = Publisher()
    publisher.proof_of_work = mock.Mock()

    command = ApplicationCommand(__timestamp__=0.0)

    x = subs.PublisherSubscriber(publisher)
    x.__route__(command)

    publisher.proof_of_work.assert_called_with(command)