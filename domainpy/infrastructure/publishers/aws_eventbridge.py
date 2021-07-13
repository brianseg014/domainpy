import boto3
import json
import collections.abc
from typing import Union, Sequence

from domainpy.exceptions import PublisherError
from domainpy.typing import SystemMessage
from domainpy.infrastructure.mappers import Mapper


class AwsEventBridgePublisher:

    def  __init__(self, bus_name: str, mapper: Mapper, **kwargs):
        self.bus_name = bus_name
        self.mapper = mapper
        
        self.client = boto3.client('events', **kwargs)

    def publish(self, messages: Union[SystemMessage, Sequence[SystemMessage]]):
        if not isinstance(messages, collections.abc.Sequence):
            messages = tuple([messages])

        entries = [
            {
                'Source': self.mapper.context,
                'Detail': json.dumps(self.mapper.serialize_asdict(m)),
                'DetailType': m.__class__.__name__,
                'EventBusName': self.bus_name
            }
            for m in messages
        ]

        response = self.client.put_events(Entries=entries)
        if response['FailedEntryCount'] > 0:
            errors = [
                PublisherError.EntryError(messages[i], e['ErrorCode'])
                for i,e in enumerate(response['Entries'])
                if 'EventId' not in e # Failed
            ]
            raise PublisherError(f'Bus name: {self.bus_name}', errors)