from __future__ import annotations

import json
import typing
import boto3  # type: ignore

from domainpy.exceptions import PublisherError
from domainpy.infrastructure.publishers.base import Publisher
from domainpy.infrastructure.transcoder import record_asdict

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.infrastructure import (
        InfrastructureMessage,
    )
    from domainpy.infrastructure.mappers import Mapper


class AwsSimpleQueueServicePublisher(Publisher):
    def __init__(self, queue_url: str, mapper: Mapper, **kwargs):
        self.queue_url = queue_url
        self.mapper = mapper

        self.client = boto3.client("sqs", **kwargs)

    def _publish(
        self,
        messages: typing.Sequence[InfrastructureMessage],
    ):
        entries = [
            {
                "QueueUrl": self.queue_url,
                "MessageBody": json.dumps(
                    record_asdict(self.mapper.serialize(m))
                ),
            }
            for m in messages
        ]

        errors = []
        for i, entry in enumerate(entries):
            try:
                self.client.send_message(**entry)
            except Exception as error:  # pylint: disable=broad-except
                errors.append(
                    PublisherError.EntryError(messages[i], str(error))
                )
        if len(errors) > 0:
            raise PublisherError(errors)
