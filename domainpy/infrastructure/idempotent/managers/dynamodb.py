import boto3

from domainpy import exceptions as excs
from domainpy.infrastructure.idempotent.recordmanager import IdempotencyRecordManager
from domainpy.utils.dynamodb import client_serialize as serialize


class DynamoDBIdempotencyRecordManager(IdempotencyRecordManager):

    def __init__(self, table_name, **kwargs):
        self.table_name = table_name

        self.client = boto3.client('dynamodb', **kwargs)

    def store_in_progress(self, record):
        item = {
            'TableName': self.table_name,
            'Item': {
                'trace_id': serialize(record['trace_id']),
                'topic': serialize(record['topic']),
                'payload': serialize(record),
                'status': serialize('progress'),
                'error': serialize(None)
            },
            'ConditionExpression': '(attribute_not_exists(trace_id) and attribute_not_exists(topic)) or #status = :failure',
            'ExpressionAttributeNames': {
                '#status': 'status'
            },
            'ExpressionAttributeValues': {
                ':failure': serialize('failure')
            }
        }

        try:
            self.client.put_item(**item)
        except self.client.exceptions.ConditionalCheckFailedException as e:
            raise excs.IdempotencyItemError() from e

    def store_success(self, record):
        item = {
            'TableName': self.table_name,
            'Key': {
                'trace_id': serialize(record['trace_id']),
                'topic': serialize(record['topic'])
            },
            'UpdateExpression': 'set #status = :status',
            'ExpressionAttributeNames': {
                '#status': 'status'
            },
            'ExpressionAttributeValues': {
                ':status': serialize('success')
            }
        }
        self.client.update_item(**item)
        

    def store_failure(self, record, exc):
        item = {
            'TableName': self.table_name,
            'Key': {
                'trace_id': serialize(record['trace_id']),
                'topic': serialize(record['topic'])
            },
            'UpdateExpression': 'set #status = :status, #error = :error',
            'ExpressionAttributeNames': {
                '#status': 'status',
                '#error': 'error'
            },
            'ExpressionAttributeValues': {
                ':status': serialize('failure'),
                ':error': serialize(str(exc))
            }
        }
        self.client.update_item(**item)
    