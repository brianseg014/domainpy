import pytest
import boto3
import json
import moto
from unittest import mock
from collections import namedtuple

from domainpy import exceptions as excs
from domainpy.infrastructure.publishers.aws_sns import AwsSimpleNotificationServicePublisher


@pytest.fixture
def topic_name():
    return 'topic_name'

@pytest.fixture
def region_name():
    return 'us-east-1'

@pytest.fixture
def sns(region_name):
    with moto.mock_sns():
        yield boto3.client('sns', region_name=region_name)

@pytest.fixture(autouse=True)
def topic_arn(sns, topic_name):
    topic = sns.create_topic(Name=topic_name)
    return topic['TopicArn']

def test_sns_publish(topic_arn, region_name):
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    mapper = mock.MagicMock()
    mapper.serialize_asdict = mock.Mock(return_value={ 'some_property': 'x' })

    pub = AwsSimpleNotificationServicePublisher(topic_arn, mapper, region_name=region_name)
    pub.publish(some_message)
