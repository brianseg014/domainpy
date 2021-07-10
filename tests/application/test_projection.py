import uuid

from domainpy.application.projection import Projection, projector
from domainpy.domain.model.event import DomainEvent


def test_projector_project():
    class BasicProjection(Projection):

        @projector
        def project(self, e: DomainEvent):
            pass

        @project.event(DomainEvent)
        def _(self, e: DomainEvent):
            self.e = e

    e  = DomainEvent(
        __stream_id__=uuid.uuid4(),
        __number__=0
    )

    p = BasicProjection()
    p.__route__(e)

    assert p.e == e
