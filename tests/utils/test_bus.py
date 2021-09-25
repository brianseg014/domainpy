from unittest import mock

from domainpy.application.command import ApplicationCommand
from domainpy.utils.bus import Bus, ISubscriber, Message


def test_bus():
    class Subscriber(ISubscriber):
        def __route__(self, message: Message):
            self.proof_of_work(message)

        def proof_of_work(self, *args, **kwargs):
            pass

    subscriber = Subscriber()
    subscriber.proof_of_work = mock.Mock()

    command = ApplicationCommand(__timestamp__ = 0.0, __version__ = 1)

    bus = Bus()
    bus.attach(subscriber)
    bus.publish(command)

    subscriber.proof_of_work.assert_called_with(command)
