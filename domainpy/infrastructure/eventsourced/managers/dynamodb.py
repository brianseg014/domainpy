import boto3
import datetime

from domainpy.exceptions import ConcurrencyError
from domainpy.infrastructure.eventsourced.recordmanager import EventRecordManager, Session
from domainpy.infrastructure.mappers import EventRecord
from domainpy.utils.dynamodb import client_serialize as serialize, client_deserialize as deserialize


class DynamoDBEventRecordManager(EventRecordManager):

    def __init__(self, table_name, region_name=None):
        self.table_name = table_name

        self.client = boto3.client('dynamodb', region_name=region_name)

    def session(self):
        return DynamoSession(self)

    def get_records(self, 
            stream_id: str, 
            topic: str=None,
            from_timestamp: datetime.datetime=None, to_timestamp: datetime.datetime=None, 
            from_number: int=None, to_number: int=None) -> tuple[EventRecord]:

        key_conditions_expressions = []
        filter_expressions = []
        expression_attribute_values = {}

        key_conditions_expressions.append(f'stream_id = :stream_id')
        expression_attribute_values.update({ ':stream_id': { 'S': stream_id } })

        if topic is not None:
            filter_expressions.append(f'topic = :topic')
            expression_attribute_values.update({ ':topic': { 'S': topic } })
        
        if from_number is not None:
            filter_expressions.append(f'number >= :from_numer')
            expression_attribute_values.update({ ':from_numer': { 'N': str(from_number) } })

        if to_number is not None:
            filter_expressions.append(f'number <= :to_number')
            expression_attribute_values.update({ ':to_number': { 'N': str(to_number) } })

        if from_timestamp is not None:
            filter_expressions.append(f'timestamp >= :from_timestamp')
            expression_attribute_values.update({ ':from_timestamp': { 'N': str(from_timestamp) } })

        if to_timestamp is not None:
            filter_expressions.append(f'timestamp <= :to_timestamp')
            expression_attribute_values.update({ ':to_timestamp': { 'N': str(to_timestamp) } })
        
        query_params = {
            'TableName': self.table_name,
            'KeyConditionExpression': ' and '.join(key_conditions_expressions),
            'ExpressionAttributeValues': expression_attribute_values
        }

        if len(filter_expressions) > 0:
            query_params.update({
                'FilterExpression': ' and '.join(filter_expressions)
            })

        query_result = self.client.query(**query_params)

        return tuple([
            self.deserialize(i)
            for i in query_result['Items']
        ])

    @classmethod
    def serialize(cls, event_record: EventRecord) -> dict:
        serialized = {
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
        return serialized

    @classmethod
    def deserialize(cls, dct: dict) -> EventRecord:
        event_record = EventRecord(
            stream_id=deserialize(dct['stream_id']),
            number=deserialize(dct['number']),
            topic=deserialize(dct['topic']),
            version=deserialize(dct['version']),
            timestamp=deserialize(dct['timestamp']),
            trace_id=deserialize(dct['trace_id']),
            message=deserialize(dct['message']),
            context=deserialize(dct['context']),
            payload=deserialize(dct['payload'])
        )
        return event_record
        

class DynamoSession(Session):

    def __init__(self, record_manager):
        self.record_manager = record_manager

        self.heap = []

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.rollback()

    def append(self, event_record: EventRecord):
        if event_record is None:
            raise TypeError('event_record cannot be None')
        
        self.heap.append(event_record)

    def commit(self):
        self.batch_writer(self.heap)
        self.heap = []

    def rollback(self):
        self.heap = []

    def batch_writer(self, heap):
        items = []
        for event_record in heap:
            items.append(
                {
                    'TableName': self.record_manager.table_name,
                    'Item': self.record_manager.serialize(event_record),
                    'ConditionExpression': 'attribute_not_exists(stream_id) and attribute_not_exists(number)'
                }
            )
            
        try:
            self.record_manager.client.transact_write_items(
                TransactItems=[
                    { 'Put': i } for i in items
                ]
            )
        except self.record_manager.client.exceptions.TransactionCanceledException as e:
            if e.response['Error']['Message'] == 'Transaction cancelled, please refer cancellation reasons for specific reasons [ConditionalCheckFailed]':
                raise ConcurrencyError() from e
            else:
                raise e