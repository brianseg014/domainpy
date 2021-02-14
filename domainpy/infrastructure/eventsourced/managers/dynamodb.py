import boto3

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


class DynamoSession(Session):

    def __init__(self, record_manager):
        self.writer = record_manager.table.batch_writer()

    def __enter__(self):
        self.writer.__enter__()

    def __exit__(self, *args, **kwargs):
        self.writer.__exit__(*args, **kwargs)

    def append(self, event_record: EventRecord):
        if event_record is None:
            raise TypeError('event_record cannot be None')

        self.writer.put_item(
            Item=event_record
        )

    def commit(self):
        pass

    def rollback(self):
        pass
    