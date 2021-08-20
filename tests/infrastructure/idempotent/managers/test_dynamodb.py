

import pytest
import boto3
import moto

from domainpy.exceptions import IdempotencyItemError
from domainpy.infrastructure.records import CommandRecord
from domainpy.infrastructure.transcoder import MessageType, record_asdict
from domainpy.infrastructure.idempotent.managers.dynamodb import DynamoDBIdempotencyRecordManager


@pytest.fixture
def table_name():
    return 'idempotent'

@pytest.fixture
def region_name():
    return 'us-east-1'

@pytest.fixture
def dynamodb(region_name):
    with moto.mock_dynamodb2():
        yield boto3.client('dynamodb', region_name=region_name)

@pytest.fixture(autouse=True)
def _(dynamodb, table_name):
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'trace_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'topic',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'trace_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'topic',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    dynamodb.get_waiter('table_exists').wait(TableName=table_name)

@pytest.fixture
def record():
    return record_asdict(CommandRecord(
        trace_id='tid',
        topic='ApplicationCommand',
        version=1,
        timestamp=0.0,
        message=MessageType.APPLICATION_COMMAND.value,
        payload={ }
    ))

def test_store_in_progress(dynamodb, table_name, region_name, record):
    record_manager = DynamoDBIdempotencyRecordManager(table_name, region_name=region_name)
    record_manager.store_in_progress(record)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert len(items) == 1

def test_store_in_progress_already_exists_in_progress(table_name, region_name, record):
    record_manager = DynamoDBIdempotencyRecordManager(table_name, region_name=region_name)
    record_manager.store_in_progress(record)

    with pytest.raises(IdempotencyItemError):
        record_manager.store_in_progress(record)

def test_store_in_progress_already_exists_in_success(table_name, region_name, record):
    record_manager = DynamoDBIdempotencyRecordManager(table_name, region_name=region_name)
    record_manager.store_in_progress(record)
    record_manager.store_success(record)

    with pytest.raises(IdempotencyItemError):
        record_manager.store_in_progress(record)

def test_store_in_progress_already_exists_in_failure(table_name, region_name, record):
    record_manager = DynamoDBIdempotencyRecordManager(table_name, region_name=region_name)
    record_manager.store_in_progress(record)
    record_manager.store_failure(record, Exception('some-error-description'))
    record_manager.store_in_progress(record)
