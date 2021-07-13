
from unittest import mock

from domainpy.utils import bus_subscribers as subs


def test_application_service_subscriber():
    application_service = mock.MagicMock()

    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    x = subs.ApplicationServiceSubscriber(application_service)
    x.__route__(some_message)

    application_service.handle.assert_called_once_with(some_message)

def test_publisher_subscriber():
    publisher = mock.MagicMock()

    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    x = subs.PublisherSubciber(publisher)
    x.__route__(some_message)

    publisher.publish.assert_called_once_with(some_message)