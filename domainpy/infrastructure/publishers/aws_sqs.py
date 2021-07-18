from __future__ import annotations

import collections.abc
import json
import typing

import boto3

if typing.TYPE_CHECKING:
    from domainpy.typing import SystemMessage
    from domainpy.infrastructure.mappers import Mapper

from domainpy.exceptions import PublisherError
from domainpy.infrastructure.publishers.base import IPublisher


class AwsSimpleQueueServicePublisher(IPublisher):
    def __init__(self, queue_name: str, mapper: Mapper, **kwargs):
        self.queue_name = queue_name
        self.mapper = mapper

        self.client = boto3.client("sqs", **kwargs)

        self.queue_url = self.client.get_queue_url(QueueName=self.queue_name)[
            "QueueUrl"
        ]

    def publish(
        self,
        messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]],
    ):
        if not isinstance(messages, collections.abc.Sequence):
            messages = tuple([messages])

        entries = [
            {
                "QueueUrl": self.queue_url,
                "MessageBody": json.dumps(self.mapper.serialize_asdict(m)),
            }
            for m in messages
        ]

        errors = []
        for i, e in enumerate(entries):
            try:
                self.client.send_message(**e)
            except self.client.exceptions.InvalidMessageContents as e:
                errors.append(PublisherError.EntryError(messages[i], str(e)))
        if len(errors) > 0:
            raise PublisherError(f"Queue name: {self.queue_name}", errors)
