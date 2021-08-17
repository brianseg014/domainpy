import typing
import pytest
import moto
import boto3
import uuid
import datetime

from domainpy.infrastructure.records import CommandRecord
from domainpy.infrastructure.tracer.recordmanager import ContextResolution, Resolution
from domainpy.infrastructure.tracer.managers.dynamodb import DynamoDBTraceRecordManager


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

@pytest.fixture
def trace_id():
    return str(uuid.uuid4())

@pytest.fixture
def command_record(trace_id):
    return CommandRecord(
        trace_id=trace_id,
        topic='some-command-topic',
        version=1,
        timestamp=datetime.datetime.timestamp(datetime.datetime.now()),
        message='command',
        payload={ 'some_property': 'x' }
    )

@pytest.fixture
def contexts_resolutions():
    return tuple([
        ContextResolution(
            context='some_context',
            resolution=Resolution.pending
        )
    ])

@pytest.fixture(autouse=True)
def _(dynamodb, table_name):
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'trace_id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'trace_id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    dynamodb.get_waiter('table_exists').wait(TableName=table_name)

def test_get_trace_contexts(table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutinos = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    expected_contexts_resolutions = contexts_resolutions

    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutinos)
    contexts_resolutions = manager.get_trace_contexts(trace_id)
    
    for cr1,cr2 in zip(contexts_resolutions, expected_contexts_resolutions):
        assert cr1 == cr2

def test_store_in_progress(dynamodb, table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutinos = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    
    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutinos)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert len(items) == 1
    assert items[0]['resolution']['S'] == Resolution.pending
    for resolution in contexts_resolutions:
        assert items[0]['contexts_resolutions']['M'][resolution.context]['M']['resolution']['S'] == Resolution.pending

def test_store_resolve_success(dynamodb, table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])

    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_resolve_success(trace_id)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['resolution']['S'] == Resolution.success

def test_store_resolve_failure(dynamodb, table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])

    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_resolve_failure(trace_id)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['resolution']['S'] == Resolution.failure

def test_store_context_resolve_success(dynamodb, table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    context_resolution = contexts_resolutions[0]

    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_context_resolve_success(trace_id, context_resolution.context)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['contexts_resolutions']['M'][context_resolution.context]['M']['resolution']['S'] == Resolution.success

def test_store_resolve_success_unexpected(dynamodb, table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])

    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_context_resolve_success(trace_id, 'unexpected_context')

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['contexts_resolutions_unexpected']['M']['unexpected_context']['M']['resolution']['S'] == Resolution.success

def test_store_context_resolve_failure(dynamodb, table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])
    context_resolution = contexts_resolutions[0]

    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_context_resolve_failure(trace_id, context_resolution.context, 'some error')

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['contexts_resolutions']['M'][context_resolution.context]['M']['resolution']['S'] == Resolution.failure

def test_store_resolve_failure_unexpected(dynamodb, table_name: str, region_name: str, trace_id: str, command_record: CommandRecord, contexts_resolutions: typing.Tuple[ContextResolution, ...]):
    resolutions = tuple([
        resolution.context for resolution in contexts_resolutions
    ])

    manager = DynamoDBTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command_record, resolutions)
    manager.store_context_resolve_failure(trace_id, 'unexpected_context', 'some error')

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['contexts_resolutions_unexpected']['M']['unexpected_context']['M']['resolution']['S'] == Resolution.failure