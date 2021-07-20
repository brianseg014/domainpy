from collections import namedtuple
import pytest
import boto3
import moto
from unittest import mock

from domainpy import exceptions as excs
from domainpy.infrastructure.publishers.aws_eventbridge import AwsEventBridgePublisher

@pytest.fixture
def bus_name():
    return 'bus_name'

@pytest.fixture
def region_name():
    return 'us-east-1'

@pytest.fixture
def cloudwatch_events(region_name):
    with moto.mock_events():
        yield boto3.client('events', region_name=region_name)

@pytest.fixture(autouse=True)
def _(cloudwatch_events, bus_name):
    cloudwatch_events.create_event_bus(Name=bus_name)

def test_eventbridge_publish(bus_name):
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    mapper = mock.MagicMock()
    mapper.serialize_asdict = mock.Mock(return_value={ 'some_property': 'x' })

    pub = AwsEventBridgePublisher(bus_name, 'some_context', mapper)
    pub.publish(some_message)
