import pytest
import uuid
from unittest import mock

from domainpy.exceptions import DefinitionError
from domainpy.application.service import handler


def test_handler_fail_if_not_trace_id():
    story = []

    something = mock.MagicMock()
    service = mock.MagicMock()

    @handler
    def handle():
        pass

    def handle_something(*args):
        story.append(args)

    handle.command(something.__class__)(handle_something)

    with pytest.raises(DefinitionError):
        handle(service, something)

def test_handler_command():
    story = []

    something = mock.MagicMock()
    something.__trace_id__ = 'some-trace-id'
    service = mock.MagicMock()

    @handler
    def handle():
        pass

    def handle_something(*args):
        story.append(args)

    handle.command(something.__class__)(handle_something)

    handle(service, something)

    assert story[0][0] == service
    assert story[0][1] == something

def test_handler_integration():
    story = []

    something = mock.MagicMock()
    something.__trace_id__ = 'some-trace-id'
    service = mock.MagicMock()

    @handler
    def handle():
        pass

    def handle_something(*args):
        story.append(args)

    handle.integration(something.__class__)(handle_something)

    handle(service, something)

    assert story[0][0] == service
    assert story[0][1] == something

def test_handler_event():
    story = []

    something = mock.MagicMock()
    something.__trace_id__ = 'some-trace-id'
    service = mock.MagicMock()

    @handler
    def handle():
        pass

    def handle_something(*args):
        story.append(args)

    handle.event(something.__class__)(handle_something)

    handle(service, something)

    assert story[0][0] == service
    assert story[0][1] == something

def test_handler_trace():
    story = []

    something = mock.MagicMock()
    something.__trace_id__ = 'some-trace-id'
    someotherthing = mock.MagicMock()
    someotherthing.__trace_id__ = 'some-trace-id'
    service = mock.MagicMock()

    @handler
    def handle():
        pass

    def handle_trace(*args):
        story.append(args)

    handle.trace(something.__class__, someotherthing.__class__)(handle_trace)

    handle(service, something)
    handle(service, someotherthing)

    assert story[0][0] == service
    assert story[0][1] == something
    assert story[0][2] == someotherthing