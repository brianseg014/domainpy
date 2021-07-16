
from unittest import mock

from domainpy.typing import SystemMessage
from domainpy.environments.eventsourced import EventSourcedEnvironment
from domainpy.utils.bus import ISubscriber


class StorySubscriber(ISubscriber[SystemMessage]):

    def __init__(self, name: str, story: list[str]):
        self.name = name
        self.story = story

    def __route__(self, message: SystemMessage):
        self.story.append(self.name)
        

def test_bus_sequence():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    event = mock.MagicMock()
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper
    )

    story = []
    env.handler_bus.attach(StorySubscriber('handler', story))
    env.projection_bus.attach(StorySubscriber('projection', story))
    env.integration_publisher_bus.attach(StorySubscriber('integration', story))
    env.resolver_bus.attach(StorySubscriber('resolver', story))
    env.domain_publisher_bus.attach(StorySubscriber('domain', story))
    
    env.event_store.store_events([event])

    assert story == ['domain', 'integration', 'projection', 'resolver', 'handler']

def test_bus_handle():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    command = mock.MagicMock()
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    story = []
    env.resolver_bus.attach(StorySubscriber('resolver', story))
    env.handler_bus.attach(StorySubscriber('handler', story))

    env.handle(command)

    assert story == ['resolver', 'handler']
