import boto3
import json

from domainpy.utils.bus import Bus


class SimpleQueueServiceBus(Bus):

    def __init__(self, mapper, region_name=None):
        self.mapper = mapper

        self.sqs = boto3.resource('sqs', region_name=region_name)
        self.names = []

    def attach(self, handler):
        self.names.append(handler)

    def detach(self, handler):
        self.names.remove(handler)

    def publish(self, publishable):
        for name in self.names:
            queue = self.sqs.get_queue_by_name(QueueName=name)
            queue.send_message(
                MessageBody=json.dumps(self.mapper.serialize(publishable)._asdict())
            )
        