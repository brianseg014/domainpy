import boto3

from domainpy.exceptions import PartialBatchError


class SimpleQueueServiceBatchProcessor:

    def __init__(self, queue_message, record_handler, **kwargs):
        self.queue_message = queue_message
        self.record_handler = record_handler

        self.success_messages: list = []
        self.fail_messages: list = []

        self.client = boto3.client('sqs', **kwargs)

    def __enter__(self):
        self.process()
        return self.success_messages, self.fail_messages

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.clean_queue()

    def get_records(self):
        return self.queue_message['Records']

    def process(self):
        records = self.get_records()
        for record in records:
            self.process_record(record)

    def process_record(self, record):
        try:
            self.record_handler(record)
            self.success_handler(record)
        except Exception as e:
            self.fail_handler(record, e)
        
    def success_handler(self, record):
        self.success_messages.append(record)

    def fail_handler(self, record, error):
        self.fail_messages.append((record, error))

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
            processor = SimpleQueueServiceBatchProcessor(queue_message, record_handler)
            with processor as (success_messages, fail_messages):
                return func(
                    queue_message, *args, **kwargs, 
                    success_messages=success_messages, 
                    fail_messages=fail_messages
                )
        return wrapper
    return inner_function