import boto3

from domainpy.exceptions import PartialBatchError
from domainpy.infrastructure.processors.base import Processor


class AwsSimpleQueueServiceBatchProcessor(Processor):

    def __init__(self, **kwargs):
        super().__init__()
        self.client = boto3.client('sqs', **kwargs)
    
    def get_records(self):
        return self.raw_message['Records']

    def cleanup(self):
        self.clean_queue()

    def get_queue_url(self):
        *_, account_id, queue_name = self.get_records()[0]['eventSourceARN'].split(":")
        return f"{self.client._endpoint.host}/{account_id}/{queue_name}"

    def get_entries_succeeded(self):
        return [
            { 'Id': r['messageId'], 'ReceiptHandle': r['receiptHandle'] }
            for r in self.success_messages
        ]

    def clean_queue(self):
        if len(self.fail_messages) == 0:
            # Let the standard flow to clean the queue
            return

        queue_url = self.get_queue_url()
        entries_to_delete = self.get_entries_succeeded()
        
        if len(entries_to_delete) > 0:
            self.client.delete_message_batch(QueueUrl=queue_url, Entries=entries_to_delete)

        raise PartialBatchError(
            f'{len(self.fail_messages)} records processing raise error',
            errors=self.fail_messages
        )


def sqs_batch_processor(record_handler):
    def inner_function(func):
        def wrapper(queue_message, *args, **kwargs):
            processor = AwsSimpleQueueServiceBatchProcessor()
            with processor(queue_message, record_handler) as (success_messages, fail_messages):
                return func(
                    queue_message, *args, **kwargs, 
                    success_messages=success_messages, 
                    fail_messages=fail_messages
                )
        return wrapper
    return inner_function