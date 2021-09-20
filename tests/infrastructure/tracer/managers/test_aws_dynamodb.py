from domainpy.infrastructure.tracer.tracestore import TraceResolution
import uuid
import boto3
import pytest
import moto

from domainpy.exceptions import IdempotencyItemError, Timeout
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import SuccessIntegrationEvent, FailureIntegrationEvent
from domainpy.infrastructure.tracer.managers.aws_dynamodb import DynamoDBTraceSegmentStore, DynamoDBTraceStore
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.utils.bus import Bus
from domainpy.utils.bus_subscribers import BasicSubscriber


@pytest.fixture
def trace_table_name():
    return 'trace'

@pytest.fixture
def trace_segment_table_name():
    return 'trace_segment'

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
def mapper():
    m = Mapper(
        transcoder=Transcoder()
    )
    m.register(ApplicationCommand)
    m.register(SuccessIntegrationEvent)
    m.register(FailureIntegrationEvent)
    return m

@pytest.fixture
def command(trace_id):
    return ApplicationCommand(
        __resolvers__=['some_context'],
        __trace_id__=trace_id,
        __version__=1,
        __timestamp__=0.0
    )

@pytest.fixture
def integration_success(trace_id):
    return SuccessIntegrationEvent(
        __trace_id__=trace_id,
        __version__=1,
        __timestamp__=0.0,
        __context__='some_context'
    )

@pytest.fixture
def integration_failure(trace_id):
    return FailureIntegrationEvent(
        __trace_id__=trace_id,
        __version__=1,
        __timestamp__=0.0,
        __context__='some_context',
        __error__='Some'
    )

@pytest.fixture(autouse=True)
def _(dynamodb, trace_table_name, trace_segment_table_name):
    dynamodb.create_table(
        TableName=trace_table_name,
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
    dynamodb.create_table(
        TableName=trace_segment_table_name,
        KeySchema=[
            {
                'AttributeName': 'trace_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'subject',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'trace_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'subject',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    dynamodb.get_waiter('table_exists').wait(TableName=trace_table_name)
    dynamodb.get_waiter('table_exists').wait(TableName=trace_segment_table_name)

def test_trace_idempotency(dynamodb, mapper, trace_table_name, region_name, trace_id, command):
    store = DynamoDBTraceStore(trace_table_name, mapper, region_name=region_name)
    store.start_trace(command)

    with pytest.raises(IdempotencyItemError):
        store.start_trace(command)

def test_watch_resolution_success(dynamodb, mapper, trace_table_name, region_name, trace_id, command, integration_success):
    store = DynamoDBTraceStore(trace_table_name, mapper, region_name=region_name)
    store.start_trace(command)

    with pytest.raises(Timeout):
        print(store.watch_trace_resolution(trace_id, timeout_ms=1))

    store.resolve_context(integration_success)
    trace_resolution = store.watch_trace_resolution(trace_id)
    assert trace_resolution.resolution == trace_resolution.Resolutions.success

def test_watch_resolution_failure(dynamodb, mapper, trace_table_name, region_name, trace_id, command, integration_failure):
    store = DynamoDBTraceStore(trace_table_name, mapper, region_name=region_name)
    store.start_trace(command)

    with pytest.raises(Timeout):
        print(store.watch_trace_resolution(trace_id, timeout_ms=1))

    store.resolve_context(integration_failure)
    trace_resolution = store.watch_trace_resolution(trace_id)
    assert trace_resolution.resolution == trace_resolution.Resolutions.failure

def test_watch_resolution_bus(dynamodb, mapper, trace_table_name, region_name, trace_id, command, integration_success):
    integration_subscriber = BasicSubscriber()

    integration_bus = Bus()
    integration_bus.attach(integration_subscriber)

    store = DynamoDBTraceStore(trace_table_name, mapper, region_name=region_name)
    store.start_trace(command)
    store.resolve_context(integration_success)
    store.watch_trace_resolution(trace_id, integration_bus=integration_bus)

    assert len(integration_subscriber) == 1

def test_resolve_when_no_resolvers(dynamodb, mapper, trace_table_name, region_name, trace_id, command):
    command.__dict__['__resolvers__'] = []

    store = DynamoDBTraceStore(trace_table_name, mapper, region_name=region_name)
    store.start_trace(command)
    trace_resolution = store.get_resolution(trace_id)

    assert trace_resolution.resolution == trace_resolution.Resolutions.success

def test_trace_segment_idempotency(dynamodb, mapper, trace_segment_table_name, region_name, trace_id, command):
    store = DynamoDBTraceSegmentStore(trace_segment_table_name, mapper, region_name=region_name)
    with store.start_trace_segment(command):
        pass # Everything ok

    with pytest.raises(IdempotencyItemError):
        with store.start_trace_segment(command):
            pass # Everything ok

def test_trace_segment_success(dynamodb, mapper, trace_segment_table_name, region_name, trace_id, command):
    store = DynamoDBTraceSegmentStore(trace_segment_table_name, mapper, region_name=region_name)
    with store.start_trace_segment(command):
        pass # Everything ok

    resolution = store.get_resolution(trace_id, 'ApplicationCommand')
    assert resolution == TraceResolution.Resolutions.success

def test_trace_segment_failure(dynamodb, mapper, trace_segment_table_name, region_name, trace_id, command):
    store = DynamoDBTraceSegmentStore(trace_segment_table_name, mapper, region_name=region_name)
    with pytest.raises(Exception):
        with store.start_trace_segment(command):
            raise Exception()

    resolution = store.get_resolution(trace_id, 'ApplicationCommand')
    assert resolution == TraceResolution.Resolutions.failure
