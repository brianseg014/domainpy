
from unittest import mock

from domainpy.application.projection import projector


def test_projector():
    event = mock.MagicMock()
    projection = mock.MagicMock()
    method = mock.Mock()

    @projector
    def project():
        pass

    project.event(event.__class__)(method)

    project(projection, event)

    method.assert_called_once_with(projection, event)