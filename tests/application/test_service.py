import typing
import pytest
import functools
from unittest import mock

from domainpy.application.command import ApplicationCommand
from domainpy.application.service import ApplicationService, handler
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.typing.application import ApplicationMessage


@pytest.fixture
def command():
    return ApplicationCommand(
        __timestamp__ = 0.0
    )

@pytest.fixture
def integration():
    return IntegrationEvent(
        __resolve__ = 'success',
        __error__ = None,
        __timestamp__ = 0.0
    )

@pytest.fixture
def event():
    return DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0
    )


def test_service_stamp():
    partial_integration = ApplicationService.stamp_integration(IntegrationEvent)
    assert isinstance(partial_integration, functools.partial)

def test_handler_command(command):
    class Service(ApplicationService):
        @handler
        def handle(self, message: ApplicationMessage) -> None:
            pass

        @handle.command(ApplicationCommand)
        def _(self, c: ApplicationCommand):
            self.proof_of_work(c)

        def proof_of_work(self, *args, **kwargs):
            pass

    service = Service()
    service.proof_of_work = mock.Mock()
    service.handle(command)

    service.proof_of_work.assert_called_with(command)


def test_handler_integration(integration):
    class Service(ApplicationService):
        @handler
        def handle(self, message: ApplicationMessage) -> None:
            pass

        @handle.integration(IntegrationEvent)
        def _(self, i: IntegrationEvent):
            self.proof_of_work(i)

        def proof_of_work(self, *args, **kwargs):
            pass

    service = Service()
    service.proof_of_work = mock.Mock()
    service.handle(integration)

    service.proof_of_work.assert_called_with(integration)

def test_handler_event(event):
    class Service(ApplicationService):
        @handler
        def handle(self, message: ApplicationMessage) -> None:
            pass

        @handle.event(DomainEvent)
        def _(self, e: DomainEvent):
            self.proof_of_work(e)

        def proof_of_work(self, *args, **kwargs):
            pass

    service = Service()
    service.proof_of_work = mock.Mock()
    service.handle(event)

    service.proof_of_work.assert_called_with(event)
    

def test_handler_trace(command, integration, event):
    class Service(ApplicationService):
        @handler
        def handle(self, message: ApplicationMessage) -> None:
            pass

        @handle.trace(ApplicationCommand, IntegrationEvent)
        def _(self, c: ApplicationCommand, i: IntegrationEvent):
            self.proof_of_work(c, i)

        @handle.trace(ApplicationCommand, DomainEvent)
        def _(self, c: ApplicationCommand, e: DomainEvent):
            self.proof_of_work(c, e)

        def proof_of_work(self, *args, **kwargs):
            pass

    service = Service()
    service.proof_of_work = mock.Mock()
    service.handle(command)
    service.handle(integration)
    service.handle(event)

    service.proof_of_work.assert_has_calls([
        mock.call(command, integration),
        mock.call(command, event)
    ])

def test_handler_trace_with_any(command, integration, event):
    class Service(ApplicationService):
        @handler
        def handle(self, message: ApplicationMessage) -> None:
            pass

        @handle.trace(ApplicationCommand, handler.any([IntegrationEvent, DomainEvent]))
        def _(self, c: ApplicationCommand, e: typing.Union[IntegrationEvent, DomainEvent]):
            self.proof_of_work(c, e)

        def proof_of_work(self, *args, **kwargs):
            pass

    service = Service()
    service.proof_of_work = mock.Mock()
    service.handle(command)
    service.handle(integration)
    service.proof_of_work.assert_has_calls([
        mock.call(command, integration)
    ])

    service = Service()
    service.proof_of_work = mock.Mock()
    service.handle(command)
    service.handle(event)
    service.proof_of_work.assert_has_calls([
        mock.call(command, event)
    ])

def test_handler_async_rebuilding(command, integration):
    class Service(ApplicationService):
        @handler
        def handle(self, message: ApplicationMessage) -> None:
            pass

        @handle.command(ApplicationCommand)
        def _(self, c: ApplicationCommand):
            self.should_not_be_called(c)

        @handle.trace(ApplicationCommand, IntegrationEvent)
        def _(self, c: ApplicationCommand, i: IntegrationEvent):
            self.proof_of_work(c, i)

        def should_not_be_called(self, *args, **kwargs):
            pass

        def proof_of_work(self, *args, **kwargs):
            pass

    service = Service()
    service.should_not_be_called = mock.Mock()
    service.proof_of_work = mock.Mock()

    command.__dict__['__handle__'] = 'rebuilding'
    service.handle(command)
    service.handle(integration)

    assert not service.should_not_be_called.mock_calls == [mock.call(command)]
    assert service.proof_of_work.mock_calls == [mock.call(command, integration)]