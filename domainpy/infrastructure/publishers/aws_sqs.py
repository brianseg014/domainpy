from __future__ import annotations

import json
import typing
import boto3  # type: ignore

from domainpy.exceptions import PublisherError
from domainpy.infrastructure.publishers.base import Publisher

if typing.TYPE_CHECKING:
    from domainpy.typing.application import SystemMessage  # type: ignore
    from domainpy.infrastructure.mappers import Mapper


class AwsSimpleQueueServicePublisher(Publisher):
    def __init__(self, queue_name: str, mapper: Mapper, **kwargs):
        self.queue_name = queue_name
        self.mapper = mapper

        self.client = boto3.client("sqs", **kwargs)

        self.queue_url = self.client.get_queue_url(QueueName=self.queue_name)[
            "QueueUrl"
        ]

    def _publish(
        self,
        messages: typing.Sequence[SystemMessage],
    ):
        entries = [
            {
                "QueueUrl": self.queue_url,
                "MessageBody": json.dumps(self.mapper.serialize_asdict(m)),
            }
            for m in messages
        ]

        errors = []
        for i, entry in enumerate(entries):
            try:
                self.client.send_message(**entry)
            except self.client.exceptions.InvalidMessageContents as error:
                errors.append(
                    PublisherError.EntryError(messages[i], str(error))
                )
        if len(errors) > 0:
            raise PublisherError(f"Queue name: {self.queue_name}", errors)
