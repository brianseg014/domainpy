
import pytest
import typing
import functools
from unittest import mock

from domainpy.typing.application import SystemMessage

from domainpy.environments.eventsourced import EventSourcedEnvironment
from domainpy.exceptions import ConcurrencyError
from domainpy.domain.model.exceptions import DomainError
from domainpy.utils.bus import ISubscriber


class StorySubscriber(ISubscriber[SystemMessage]):

    def __init__(self, name: str, story: typing.List[str]):
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

    assert story == ['domain', 'projection', 'resolver', 'handler']

@mock.patch('domainpy.environments.eventsourced.MapperSet')
def test_bus_handle(MapperSet):
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    command = mock.MagicMock()
    command.__trace_id__ = 'tid'

    mapper_set_instance = MapperSet.return_value
    mapper_set_instance.deserialize = mock.Mock(return_value=command)
    
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

@mock.patch('domainpy.environments.eventsourced.MapperSet')
def test_publish_domain_error(MapperSet):
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    command = mock.MagicMock()
    command.__trace_id__ = 'tid'

    error = DomainError()
    def router(message):
        if message == command:
            raise error

    handler = mock.MagicMock()
    handler.__route__ = mock.Mock(side_effect=router)

    mapper_set_instance = MapperSet.return_value
    mapper_set_instance.deserialize = mock.Mock(return_value=command)
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    env.handler_bus.attach(handler)

    env.handle(command)

    handler.__route__.assert_called_with(error)

@mock.patch('domainpy.environments.eventsourced.MapperSet')
def test_publish_retry_on_concurrency_error(MapperSet):
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    command = mock.MagicMock()
    command.__trace_id__ = 'tid'

    story = []
    def router(story, message):
        if len(story) <= 1:
            story.append('raised')
            raise ConcurrencyError()

    handler = mock.MagicMock()
    handler.__route__ = mock.Mock(side_effect=functools.partial(router, story))

    mapper_set_instance = MapperSet.return_value
    mapper_set_instance.deserialize = mock.Mock(return_value=command)
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    env.handler_bus.attach(handler)

    env.handle(command)

    assert story == ['raised', 'raised']

@mock.patch('domainpy.environments.eventsourced.MapperSet')
def test_publish_raise_concurrency_error_if_exahusted(MapperSet):
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    command = mock.MagicMock()
    command.__trace_id__ = 'tid'

    story = []
    def router(story, message):
        if len(story) <= 5:
            story.append('raised')
            raise ConcurrencyError()

    handler = mock.MagicMock()
    handler.__route__ = mock.Mock(side_effect=functools.partial(router, story))

    mapper_set_instance = MapperSet.return_value
    mapper_set_instance.deserialize = mock.Mock(return_value=command)
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    env.handler_bus.attach(handler)

    with pytest.raises(ConcurrencyError):
        env.handle(command)

@mock.patch('domainpy.environments.eventsourced.MapperSet')
def test_bus_handle_fails_if_trace_id_is_None(MapperSet):
    command_mapper = mock.MagicMock()
    integration_mapper = mock.MagicMock()
    event_mapper = mock.MagicMock()
    command = mock.MagicMock()
    command.__trace_id__ = None

    mapper_set_instance = MapperSet.return_value
    mapper_set_instance.deserialize = mock.Mock(return_value=command)
    
    env = EventSourcedEnvironment(
        command_mapper=command_mapper,
        integration_mapper=integration_mapper,
        event_mapper=event_mapper,
    )

    with pytest.raises(TypeError):
        env.handle(command)