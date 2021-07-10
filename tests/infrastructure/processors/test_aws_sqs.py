import pytest
import moto
import boto3
import json
import uuid

from domainpy.exceptions import PartialBatchError
from domainpy.infrastructure.processors.aws_sqs import SimpleQueueServiceBatchProcessor, sqs_batch_processor


@pytest.fixture
def queue_name():
    return 'queue_name'

@pytest.fixture
def region_name():
    return 'us-east-1'

@pytest.fixture
def account_id():
    return '123456789012'

@pytest.fixture
def messages():
    return [
        'Some-message',
        'Some-other-message'
    ]

@pytest.fixture
def sqs(region_name):
    with moto.mock_sqs():
        yield boto3.client('sqs', region_name=region_name)

@pytest.fixture
def queue_url(sqs, queue_name):
    response = sqs.create_queue(QueueName=queue_name)
    return response['QueueUrl']

@pytest.fixture(autouse=True)
def send_messages_to_queue(sqs, queue_url, messages):
    entries = [
        {
            'Id': str(uuid.uuid4()),
            'MessageBody': json.dumps(m)
        }
        for m in messages
    ]

    sqs.send_message_batch(
        QueueUrl=queue_url,
        Entries=entries
    )

@pytest.fixture
def queue_message(sqs, queue_url, queue_name, account_id, region_name):
    queue_message = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
    if 'Messages' in queue_message:
        queue_message['Records'] = queue_message['Messages']
        del queue_message['Messages']
    else:
        queue_message['Records'] = []

    for record in queue_message['Records']: # Fix moto structure
        record['messageId'] = record['MessageId']
        record['receiptHandle'] = record['ReceiptHandle']
        record['eventSourceARN'] = f'arn:aws:sqs:{region_name}:{account_id}:{queue_name}'

        del record['MessageId']
        del record['ReceiptHandle']

    return queue_message

def test_sqs_processor_all_success(queue_message, messages):

    def record_handler(record):
        pass

    processor = SimpleQueueServiceBatchProcessor(queue_message, record_handler)
    with processor as (success_messages, fail_messages):
        assert len(success_messages) == len(messages)
        assert len(fail_messages) == 0


def test_sqs_processor_all_fail(queue_message, messages):

    def record_handler(record):
        raise Exception()

    processor = SimpleQueueServiceBatchProcessor(queue_message, record_handler)

    with pytest.raises(PartialBatchError):
        with processor as (success_messages, fail_messages):
            assert len(fail_messages) == len(messages)

def tests_sqs_process_partial_fail(sqs, queue_url, queue_message, messages):
    messages_to_fail = [messages[0]]
    messages_to_success = messages[1:]

    def record_handler(record):
        body = json.loads(record['Body'])
        if body in messages_to_fail:
            raise Exception()

    processor = SimpleQueueServiceBatchProcessor(queue_message, record_handler)
    with pytest.raises(PartialBatchError):
        with processor as (success_messages, fail_messages):
            assert len(success_messages) == len(messages_to_success)
            assert len(fail_messages) == len(messages_to_fail)

def test_decorator(queue_message, messages):

    def record_handler(record):
        pass

    @sqs_batch_processor(record_handler=record_handler)
    def handler(queue_message, success_messages, fail_messages):
        assert len(success_messages) == len(messages)
        assert len(fail_messages) == 0

    handler(queue_message)