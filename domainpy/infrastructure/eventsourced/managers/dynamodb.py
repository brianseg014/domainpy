import boto3
from boto3.dynamodb.conditions import Key, Attr

from domainpy.infrastructure.eventsourced.recordmanager import (
    EventRecordManager,
    Session
)
from domainpy.infrastructure.exception import (
    ConcurrencyException
)
from domainpy.utils.mappers.eventmapper import EventRecord
from domainpy.utils.dynamodb import serialize, deserialize

dynamodb = boto3.resource('dynamodb')

class DynamoEventRecordManager(EventRecordManager):

    def __init__(self, table_name):
        self.table = dynamodb.Table(table_name)

    def session(self):
        return DynamoSession(self)

    def find(self, stream_id: str):
        query = self.table.query(
            KeyConditionExpression=Key('stream_id').eq(stream_id)
        )
        return tuple([
            EventRecord(
                stream_id=deserialize(i['stream_id']),
                number=deserialize(i['number']),
                topic=deserialize(i['topic']),
                version=deserialize(i['version']),
                timestamp=deserialize(i['timestamp']),
                trace_id=deserialize(i['trace_id']),
                message=deserialize(i['message']),
                payload=deserialize(i['payload'])
            )
            for i in query['Items']
        ])


class DynamoSession(Session):

    def __init__(self, record_manager):
        self.writer = record_manager.table

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        #self.writer.__exit__(*args, **kwargs)
        pass

    def append(self, event_record: EventRecord):
        if event_record is None:
            raise TypeError('event_record cannot be None')
        
        try:
            self.writer.put_item(
                Item={
                    'stream_id': serialize(event_record.stream_id),
                    'number': serialize(event_record.number),
                    'topic': serialize(event_record.topic),
                    'version': serialize(event_record.version),
                    'timestamp': serialize(event_record.timestamp),
                    'trace_id': serialize(event_record.trace_id),
                    'message': serialize(event_record.message),
                    'payload': serialize(event_record.payload)
                },
                ConditionExpression=(
                    Attr('stream_id').not_exists()
                    & Attr('number').not_exists()
                )
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            stream_id = event_record.stream_id
            number = event_record.number
            raise ConcurrencyException(f'Other thread already write stream {stream_id} with number {number}')

    def commit(self):
        pass

    def rollback(self):
        pass
    