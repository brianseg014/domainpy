import pytest
import boto3
import json
import moto
from unittest import mock

from domainpy.application.command import ApplicationCommand
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
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
    command = ApplicationCommand(
        __timestamp__=0.0,
        __trace_id__='tid',
        __version__=1
    )

    mapper = Mapper(transcoder=Transcoder())
    mapper.register(ApplicationCommand)

    pub = AwsSimpleQueueServicePublisher(queue_name, mapper, region_name=region_name)
    pub.publish(command)
    
    sqs_messages = sqs.receive_message(QueueUrl=queue_url)
    assert len(sqs_messages['Messages']) == 1
