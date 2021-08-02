import pytest
import boto3
import moto
from unittest import mock

from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
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
    command = ApplicationCommand(
        __timestamp__=0.0,
        __trace_id__='tid'
    )

    mapper = Mapper(transcoder=Transcoder())
    mapper.register(ApplicationCommand)

    pub = AwsSimpleNotificationServicePublisher(topic_arn, mapper, region_name=region_name)
    pub.publish(command)
