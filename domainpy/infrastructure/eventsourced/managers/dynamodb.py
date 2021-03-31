import decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr

from domainpy.application.mappers.eventmapper import EventRecord
from domainpy.infrastructure.eventsourced.recordmanager import (
    EventRecordManager,
    Session
)

class DynamoEventRecordManager(EventRecordManager):

    def __init__(self, table_name):
        dynamodb = boto3.resource('dynamodb')

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
        
        print('WRITING', event_record)
        
        self.writer.put_item(
            Item={
                'stream_id': serialize(event_record.stream_id),
                'number': serialize(event_record.number),
                'topic': serialize(event_record.topic),
                'version': serialize(event_record.version),
                'timestamp': serialize(event_record.timestamp),
                'message': serialize(event_record.message),
                'payload': serialize(event_record.payload)
            },
            ConditionExpression=(
                Attr('stream_id').not_exists()
                & Attr('number').not_exists()
            )
        )
        print('WRITTEN')

    def commit(self):
        pass

    def rollback(self):
        pass
    

def serialize(obj):
    if isinstance(obj, list):
        for i in xrange(len(obj)):
            obj[i] = serialize(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = serialize(obj[k])
        return obj
    elif isinstance(obj, float):
        return decimal.Decimal(str(obj))
    else:
        return obj


def deserialize(obj):
    if isinstance(obj, list):
        for i in xrange(len(obj)):
            obj[i] = deserialize(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = deserialize(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj