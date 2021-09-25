from unittest import mock

from domainpy.application.command import ApplicationCommand
from domainpy.application.query import ApplicationQuery
from domainpy.utils.bus import Bus, FilterPolicy, ISubscriber, Message
from domainpy.utils.bus_subscribers import BasicSubscriber


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

def test_filter_policy_by_context():
    context = "ctx"

    command_match = ApplicationCommand.stamp()(
        __context__ = context,
        __version__ = 1
    )
    command_not_match = ApplicationCommand.stamp()(
        __context__ = None,
        __version__ = 1
    )

    subscriber = BasicSubscriber()

    bus = Bus()
    bus.attach(
        FilterPolicy(
            contexts=[context],
            targets=[subscriber]   
        )
    )
    
    bus.publish(command_match)
    bus.publish(command_not_match)


    assert len(subscriber) == 1
    assert subscriber[0] == command_match

def test_filter_policy_by_topic():
    class CommandMatch(ApplicationCommand):
        __version__: int = 1
    class CommandNotMatch(ApplicationCommand):
        __version__: int = 1

    command_match = CommandMatch.stamp()()
    command_not_match = CommandNotMatch.stamp()()

    subscriber = BasicSubscriber()

    bus = Bus()
    bus.attach(
        FilterPolicy(
            topics=[CommandMatch.__topic__],
            targets=[subscriber]   
        )
    )
    
    bus.publish(command_match)
    bus.publish(command_not_match)

    assert len(subscriber) == 1
    assert subscriber[0] == command_match

def test_filter_policy_by_concept():
    class CommandMatch(ApplicationCommand):
        __concept__: str = 'ConceptMatch'
        __version__: int = 1
    class CommandNotMatch(ApplicationCommand):
        __concept__: str = 'ConceptNotMatch'
        __version__: int = 1

    command_match = CommandMatch.stamp()()
    command_not_match = CommandNotMatch.stamp()()

    subscriber = BasicSubscriber()

    bus = Bus()
    bus.attach(
        FilterPolicy(
            concepts=[CommandMatch.__concept__],
            targets=[subscriber]   
        )
    )
    
    bus.publish(command_match)
    bus.publish(command_not_match)

    assert len(subscriber) == 1
    assert subscriber[0] == command_match

def test_filter_policy_by_message():
    message_match = ApplicationCommand.stamp()(__version__=1)
    message_not_match = ApplicationQuery.stamp()(__version__=1)

    subscriber = BasicSubscriber()

    bus = Bus()
    bus.attach(
        FilterPolicy(
            messages=[ApplicationCommand.__message__],
            targets=[subscriber]   
        )
    )
    
    bus.publish(message_match)
    bus.publish(message_not_match)

    assert len(subscriber) == 1
    assert subscriber[0] == message_match
