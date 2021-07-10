import pytest
import uuid

from domainpy import exceptions as excs
from domainpy.application.service import ApplicationService, handler
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.domain.model.event import DomainEvent


def test_handler_fail_if_not_trace_id():
    class BasicService(ApplicationService):

        @handler
        def handle(self, c: ApplicationCommand):
            pass

        @handle.command(ApplicationCommand)
        def _(self, c: ApplicationCommand):
            pass

    c = ApplicationCommand()
    
    s = BasicService()
    with pytest.raises(TypeError):
        s.handle(c)

def test_handler_command():
    class BasicService(ApplicationService):

        @handler
        def handle(self, c: ApplicationCommand):
            pass

        @handle.command(ApplicationCommand)
        def _(self, c: ApplicationCommand):
            self.c = c

    c = ApplicationCommand(__trace_id__=uuid.uuid4())

    s = BasicService()
    s.handle(c)

    assert s.c == c

def test_handler_integration():
    class BasicService(ApplicationService):

        @handler
        def handle(self, c: ApplicationCommand):
            pass

        @handle.integration(IntegrationEvent)
        def _(self, i: IntegrationEvent):
            self.i = i

    i = IntegrationEvent(__trace_id__=uuid.uuid4())

    s = BasicService()
    s.handle(i)

    assert s.i == i

def test_handler_event():
    class BasicService(ApplicationService):

        @handler
        def handle(self, c: ApplicationCommand):
            pass

        @handle.event(DomainEvent)
        def _(self, e: DomainEvent):
            self.e = e

    e = DomainEvent(
        __trace_id__=uuid.uuid4(),
        __stream_id__=uuid.uuid4(),
        __number__=0
    )

    s = BasicService()
    s.handle(e)

    assert s.e == e

def test_handler_trace():
    class BasicService(ApplicationService):

        @handler
        def handle(self, c: ApplicationCommand):
            pass

        @handle.trace(ApplicationCommand, DomainEvent)
        def _(self, c: ApplicationCommand, e: DomainEvent):
            self.c = c
            self.e = e

    trace_id=uuid.uuid4()
    c = ApplicationCommand(__trace_id__=trace_id)
    e = DomainEvent(
        __trace_id__=uuid.uuid4(),
        __stream_id__=uuid.uuid4(),
        __number__=0
    )

    s = BasicService()
    s.handle(c)
    s.handle(e)

    assert s.c == c
    assert s.e == e
