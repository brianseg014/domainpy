import pytest
import moto
import boto3
import uuid
import datetime
import dataclasses

from domainpy.infrastructure.records import CommandRecord, TraceRecord
from domainpy.infrastructure.tracer.managers.dynamodb import DynamodbTraceRecordManager
from domainpy.utils.dynamodb import client_serialize as serialize


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
def example_trace():
    trace_id = str(uuid.uuid4())
    trace_record = TraceRecord(
        trace_id=trace_id,
        command=CommandRecord(
            trace_id=trace_id,
            topic='some-command-topic',
            version=1,
            timestamp=datetime.datetime.timestamp(datetime.datetime.now()),
            message='command',
            payload={ 'some_property': 'x' }
        ),
        status_code=TraceRecord.StatusCode.CODE_200,
        number=0,
        resolution=TraceRecord.Resolution.pending,
        version=1,
        timestamp=datetime.datetime.timestamp(datetime.datetime.now()),
        contexts_resolutions=tuple([
            TraceRecord.ContextResolution(
                context='some_context',
                resolution=TraceRecord.Resolution.pending
            )
        ])
    )
    return trace_record

@pytest.fixture(autouse=True)
def _(dynamodb, table_name, example_trace):
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

@pytest.fixture
def init_example_trace(dynamodb, table_name, example_trace):
    example_trace = dataclasses.asdict(example_trace)
    example_trace['resolution'] = example_trace['resolution']
    example_trace['contexts_resolutions'][0]['resolution'] = example_trace['contexts_resolutions'][0]['resolution']

    dynamodb.put_item(
        TableName=table_name,
        Item={
            'trace_id': serialize(example_trace['trace_id']),
            'command': serialize(example_trace['command']),
            'status_code': serialize(example_trace['status_code']),
            'number': serialize(example_trace['number']),
            'resolution': serialize(example_trace['resolution']),
            'version': serialize(example_trace['version']),
            'timestamp': serialize(example_trace['timestamp']),
            'contexts_resolutions': serialize({
                cr['context']: cr for cr in example_trace['contexts_resolutions']
            })
        }
    )

def test_get_trace_contexts(init_example_trace, table_name: str, region_name: str, example_trace: TraceRecord):
    trace_id = example_trace.trace_id

    manager = DynamodbTraceRecordManager(table_name, region_name=region_name)
    contexts_resolutions = manager.get_trace_contexts(trace_id)
    
    for cr1,cr2 in zip(contexts_resolutions, example_trace.contexts_resolutions):
        assert cr1 == cr2

def test_store_in_progress(dynamodb, table_name: str, region_name: str, example_trace: TraceRecord):
    trace_id = str(uuid.uuid4())

    command = dataclasses.asdict(example_trace.command)

    contexts = [cr.context for cr in example_trace.contexts_resolutions]

    manager = DynamodbTraceRecordManager(table_name, region_name=region_name)
    manager.store_in_progress(trace_id, command, contexts)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert len(items) == 1
    assert items[0]['resolution']['S'] == TraceRecord.Resolution.pending
    for context in contexts:
        assert items[0]['contexts_resolutions']['M'][context]['M']['resolution']['S'] == TraceRecord.Resolution.pending

def test_store_resolve_success(init_example_trace, dynamodb, table_name: str, region_name: str, example_trace: TraceRecord):
    trace_id = example_trace.trace_id

    manager = DynamodbTraceRecordManager(table_name, region_name=region_name)
    manager.store_resolve_success(trace_id)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['resolution']['S'] == TraceRecord.Resolution.success

def test_store_resolve_failure(init_example_trace, dynamodb, table_name: str, region_name: str, example_trace: TraceRecord):
    trace_id = example_trace.trace_id

    manager = DynamodbTraceRecordManager(table_name, region_name=region_name)
    manager.store_resolve_failure(trace_id)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['resolution']['S'] == TraceRecord.Resolution.failure

def test_store_context_resolve_success(init_example_trace, dynamodb, table_name: str, region_name: str, example_trace: TraceRecord):
    trace_id = example_trace.trace_id
    context = example_trace.contexts_resolutions[0].context

    manager = DynamodbTraceRecordManager(table_name, region_name=region_name)
    manager.store_context_resolve_success(trace_id, context)

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['contexts_resolutions']['M'][context]['M']['resolution']['S'] == TraceRecord.Resolution.success

def test_store_context_resolve_failure(init_example_trace, dynamodb, table_name: str, region_name: str, example_trace: TraceRecord):
    trace_id = example_trace.trace_id
    context = example_trace.contexts_resolutions[0].context

    manager = DynamodbTraceRecordManager(table_name, region_name=region_name)
    manager.store_context_resolve_failure(trace_id, context, 'some error')

    items = dynamodb.scan(TableName=table_name)['Items']
    assert items[0]['contexts_resolutions']['M'][context]['M']['resolution']['S'] == TraceRecord.Resolution.failure