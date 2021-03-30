import boto3
import json

from domainpy.application.bus import Bus


class EventBridgeBus(Bus):

    def __init__(self, source):
        self.source = source

        self.cloudwatch_events = boto3.client('events')
        self.names = []

    def attach(self, handler):
        self.names.append(handler)

    def detach(self, handler):
        self.names.remove(handler)

    def publish(self, publishable):
        for name in self.names:
            self.cloudwatch_events.put_events(
                Entries=[
                    {
                        'Source': self.source,
                        'Detail': json.dumps(publishable.__to_dict__()),
                        'DetailType': publishable.__class__.__name__,
                        'EventBusName': name
                    }
                ]
            )
    