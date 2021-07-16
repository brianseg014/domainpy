
from unittest import mock

from domainpy.application.projection import projector


def test_projector():
    story = []

    something = mock.MagicMock()
    projection = mock.MagicMock()

    @projector
    def project():
        pass

    def project_something(*args):
        story.append(args)

    project.event(something.__class__)(project_something)

    project(projection, something)

    assert story[0][0] == projection
    assert story[0][1] == something