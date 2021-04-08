import boto3
import json

from domainpy.utils.bus import Bus


class EventBridgeBus(Bus):

    def __init__(self, source, mapper):
        self.source = source
        self.mapper = mapper

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
                        'Detail': json.dumps(self.mapper.serialize(publishable)._asdict()),
                        'DetailType': publishable.__class__.__name__,
                        'EventBusName': name
                    }
                ]
            )
    