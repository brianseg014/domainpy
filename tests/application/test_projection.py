import pytest
from unittest import mock

from domainpy.exceptions import DefinitionError
from domainpy.application.projection import Projection, projector
from domainpy.domain.model.event import DomainEvent

@pytest.fixture
def event():
    event = DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0
    )
    return event

def test_projector(event):
    class TestProjection(Projection):
        @projector
        def project(self):
            pass

        @project.event(DomainEvent)
        def _(self, e: DomainEvent):
            self.proof_of_work(e)

        def proof_of_work(self, *args, **kwargs):
            pass

    
    projection = TestProjection()
    projection.proof_of_work = mock.Mock()
    projection.project(event)

    projection.proof_of_work.assert_called_with(event)

def test_projector_do_nothing_if_not_handled():
    @projector
    def project():
        pass

    project(None, None)

def test_projector_raises_if_more_than_once_definition():
    @projector
    def project():
        pass

    project.event(DomainEvent)(lambda: None)

    with pytest.raises(DefinitionError):
        project.event(DomainEvent)(lambda: None)
