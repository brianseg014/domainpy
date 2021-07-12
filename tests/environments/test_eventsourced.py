from unittest import mock

from domainpy.typing import SystemMessage
from domainpy.domain.model.event import DomainEvent
from domainpy.environments.eventsourced import EventSourcedEnvironment
from domainpy.utils.bus import Subscriber


class StorySubscriber(Subscriber[SystemMessage]):

    def __init__(self, name: str, story: list[str]):
        self.name = name
        self.story = story

    def __route__(self, message: SystemMessage):
        self.story.append(self.name)
        

def test_bus_sequence():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    event_store_record_manager = mock.MagicMock()
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
        event_store_record_manager=event_store_record_manager
    )

    story = []
    env.projection_bus.attach(StorySubscriber('projection', story))
    env.resolver_bus.attach(StorySubscriber('resolver', story))
    env.handler_bus.attach(StorySubscriber('handler', story))
    env.integration_bus.attach(StorySubscriber('integration', story))
    
    env.event_store.store_events([DomainEvent()])

    assert story == ['projection', 'resolver', 'handler', 'integration']

def test_process():
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    event_store_record_manager = mock.MagicMock()
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
        event_store_record_manager=event_store_record_manager
    )

    story = []
    env.handler_bus.attach(StorySubscriber('handler', story))

    success_messages, failure_messagess = env.process({})

    assert story == ['handler']
    assert len(success_messages) == 1
    assert len(failure_messagess) == 0