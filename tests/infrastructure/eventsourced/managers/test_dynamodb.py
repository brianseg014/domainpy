import pytest
import uuid
import datetime
import boto3
import moto
import dataclasses

from domainpy import exceptions as excs
from domainpy.infrastructure.eventsourced.managers.dynamodb import DynamoDBEventRecordManager
from domainpy.infrastructure.records import EventRecord
from domainpy.utils.dynamodb import client_serialize as serialize, client_deserialize as deserialize


@pytest.fixture
def table_name():
    return 'event_store_table_name'

@pytest.fixture
def region_name():
    return 'us-east-1'

@pytest.fixture
def dynamodb(region_name):
    with moto.mock_dynamodb2():
        dynamodb = boto3.client('dynamodb', region_name=region_name)
        yield dynamodb

@pytest.fixture(autouse=True)
def _(dynamodb, table_name):
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'stream_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'number',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'stream_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'number',
                'AttributeType': 'N'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    dynamodb.get_waiter('table_exists').wait(TableName=table_name)

@pytest.fixture
def stream_id():
    return str(uuid.uuid4())

@pytest.fixture
def  event_record(stream_id):
    return EventRecord(
        stream_id=stream_id,
        number=0,
        topic='some-topic',
        version=1,
        timestamp=datetime.datetime.timestamp(datetime.datetime.now()),
        trace_id=str(uuid.uuid4()),
        message='event',
        context='some-context',
        payload={ 
            'some_property': {
                'some_other_property': 'x'
            } 
        }
    )

def put_event_record(dynamodb, table_name, event_record):
    dynamodb.put_item(
        TableName=table_name,
        Item={
            'stream_id': serialize(event_record.stream_id),
            'number': serialize(event_record.number),
            'topic': serialize(event_record.topic),
            'version': serialize(event_record.version),
            'timestamp': serialize(event_record.timestamp),
            'trace_id': serialize(event_record.trace_id),
            'message': serialize(event_record.message),
            'context': serialize(event_record.context),
            'payload': serialize(event_record.payload)
        }
    )

def test_append_commit(dynamodb, table_name, region_name, event_record):
    rm = DynamoDBEventRecordManager(table_name, region_name)

    with rm.session() as session:
        session.append(
            event_record
        )
        session.commit()
    
    items = dynamodb.scan(TableName=table_name)['Items']
    assert len(items) == 1

def test_append_fail_on_concurrency(dynamodb, table_name, region_name, event_record):
    put_event_record(dynamodb, table_name, event_record)

    rm = DynamoDBEventRecordManager(table_name, region_name)

    with pytest.raises(excs.ConcurrencyError):
        with rm.session() as session:
            session.append(
                event_record
            )
            session.commit()

def test_append_rollback(dynamodb, table_name, region_name, event_record):
    rm = DynamoDBEventRecordManager(table_name, region_name)

    with rm.session() as session:
        session.append(
            event_record
        )
    
    items = dynamodb.scan(TableName=table_name)['Items']
    assert len(items) == 0

def test_get_records(dynamodb, table_name, region_name, stream_id, event_record):
    put_event_record(dynamodb, table_name, event_record)

    rm = DynamoDBEventRecordManager(table_name, region_name)

    events = rm.get_records(stream_id)
    assert len(list(events)) == 1

def test_get_records_filtering_number(dynamodb, table_name, region_name, stream_id, event_record):
    event_record_2 = dataclasses.replace(event_record, number=1)
    put_event_record(dynamodb, table_name, event_record)
    put_event_record(dynamodb, table_name, event_record_2)

    rm = DynamoDBEventRecordManager(table_name, region_name)

    events = rm.get_records(stream_id, from_number=0, to_number=0)
    assert len(list(events)) == 1
