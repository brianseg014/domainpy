import boto3
import json
import collections.abc
from typing import Union, Sequence

from domainpy.exceptions import PublisherError
from domainpy.typing import SystemMessage
from domainpy.infrastructure.mappers import Mapper


class AwsSimpleNotificationServicePublisher:

    def __init__(self, topic_arn: str, mapper: Mapper, **kwargs):
        self.topic_arn = topic_arn
        self.mapper = mapper

        self.client = boto3.client('sns', **kwargs)

    def publish(self, messages: Union[SystemMessage, Sequence[SystemMessage]]):
        if not isinstance(messages, collections.abc.Sequence):
            messages = tuple([messages])

        entries = [
            {
                'TopicArn': self.topic_arn,
                'Message': json.dumps(self.mapper.serialize_asdict(m)),
            }
            for m in messages
        ]

        errors = []
        for i,e in enumerate(entries):
            try:
                self.client.publish(**e)
            except self.client.InternalErrorException as e:
                errors.append(
                    PublisherError.EntryError(messages[i], str(e))
                )
        if len(errors) > 0:
            raise PublisherError(f'Topic Arn: {self.topic_arn}', errors)
