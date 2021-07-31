from __future__ import annotations

import json
import typing
import boto3  # type: ignore

from domainpy.exceptions import PublisherError
from domainpy.infrastructure.publishers.base import Publisher

if typing.TYPE_CHECKING:
    from domainpy.typing.application import SystemMessage  # type: ignore
    from domainpy.infrastructure.mappers import Mapper


class AwsSimpleNotificationServicePublisher(Publisher):
    def __init__(self, topic_arn: str, mapper: Mapper, **kwargs):
        self.topic_arn = topic_arn
        self.mapper = mapper

        self.client = boto3.client("sns", **kwargs)

    def _publish(
        self,
        messages: typing.Sequence[SystemMessage],
    ):
        entries = [
            {
                "TopicArn": self.topic_arn,
                "Message": json.dumps(self.mapper.serialize_asdict(m)),
            }
            for m in messages
        ]

        errors = []
        for i, entry in enumerate(entries):
            try:
                self.client.publish(**entry)
            except self.client.InternalErrorException as error:
                errors.append(
                    PublisherError.EntryError(messages[i], str(error))
                )
        if len(errors) > 0:
            raise PublisherError(f"Topic Arn: {self.topic_arn}", errors)
