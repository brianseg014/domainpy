
from unittest import mock

from domainpy.utils import bus_subscribers as subs


def test_application_service_subscriber():
    application_service = mock.MagicMock()

    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    x = subs.ApplicationServiceSubscriber(application_service)
    x.__route__(some_message)

    application_service.handle.assert_called_once_with(some_message)

def test_aws_event_bridge_subscriber():
    event_bridge_subscriber = mock.MagicMock()

    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    x = subs.AwsEventBridgeSubscriber(event_bridge_subscriber)
    x.__route__(some_message)

    event_bridge_subscriber.publish.assert_called_once_with(some_message)

def test_aws_sqs_subscriber():
    sqs_subscriber = mock.MagicMock()

    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    x = subs.AwsSimpleQueueServiceSubscriber(sqs_subscriber)
    x.__route__(some_message)

    sqs_subscriber.publish.assert_called_once_with(some_message)