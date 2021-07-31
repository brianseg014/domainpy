import functools
from unittest import mock

from domainpy.application.service import ApplicationService, handler


def test_service_stamp():
    IntegrationEvent = type(
        'IntegrationEvent',
        (mock.MagicMock,),
        {}
    )
    
    partial_integration = ApplicationService.stamp_integration(IntegrationEvent)
    assert isinstance(partial_integration, functools.partial)

def test_handler_command():
    message = mock.MagicMock()
    service = mock.MagicMock()
    method = mock.Mock()

    @handler
    def handle():
        pass

    handle.command(message.__class__)(method)

    handle(service, message)

    method.assert_called_with(service, message)

def test_handler_integration():
    message = mock.MagicMock()
    service = mock.MagicMock()
    method = mock.Mock()

    @handler
    def handle():
        pass

    handle.integration(message.__class__)(method)

    handle(service, message)

    method.assert_called_with(service, message)

def test_handler_event():
    message = mock.MagicMock()
    service = mock.MagicMock()
    method = mock.Mock()

    @handler
    def handle():
        pass

    handle.event(message.__class__)(method)

    handle(service, message)

    method.assert_called_with(service, message)

def test_handler_trace():
    story = []

    Message1 = type('Message1', (mock.MagicMock,), {})
    Message2 = type('Message2', (mock.MagicMock,), {})

    message1 = Message1()
    message2 = Message2()
    service = mock.MagicMock()
    method = mock.Mock()

    @handler
    def handle():
        pass

    handle.trace(message1.__class__, message2.__class__)(method)

    handle(service, message1)
    handle(service, message2)

    method.assert_called_with(service, message1, message2)