import pytest
import boto3
import json
import moto
import dataclasses
from unittest import mock

from domainpy import exceptions as excs
from domainpy.infrastructure.publishers.aws_sqs import AwsSimpleQueueServicePublisher


@pytest.fixture
def queue_name():
    return 'queue_name'

@pytest.fixture
def region_name():
    return 'us-east-1'

@pytest.fixture
def sqs(region_name):
    with moto.mock_sqs():
        yield boto3.client('sqs', region_name=region_name)

@pytest.fixture(autouse=True)
def queue_url(sqs, queue_name):
    queue = sqs.create_queue(QueueName=queue_name)
    return queue['QueueUrl']

def test_sqs_publish(sqs, queue_url, queue_name, region_name):
    SomeMessageType = type('SomeMessageType', (), {})
    some_message = SomeMessageType()

    mapper = mock.MagicMock()
    mapper.serialize_asdict = mock.Mock(return_value={ 'some_property': 'x' })

    pub = AwsSimpleQueueServicePublisher(queue_name, mapper, region_name=region_name)
    pub.publish(some_message)
    
    sqs_messages = sqs.receive_message(QueueUrl=queue_url)
    assert len(sqs_messages['Messages']) == 1
    assert json.loads(sqs_messages['Messages'][0]['Body'])['some_property'] == 'x'
