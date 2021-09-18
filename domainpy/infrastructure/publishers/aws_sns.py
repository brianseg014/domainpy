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


class AwsSimpleNotificationServicePublisher(Publisher):
    def __init__(self, topic_arn: str, context: str, mapper: Mapper, **kwargs):
        self.topic_arn = topic_arn
        self.context = context
        self.mapper = mapper

        self.client = boto3.client("sns", **kwargs)

    def _publish(
        self,
        messages: typing.Sequence[InfrastructureMessage],
    ):
        entries = [
            {
                "TopicArn": self.topic_arn,
                "MessageAttributes": {
                    "context": {
                        "DataType": "String",
                        "StringValue": self.context,
                    },
                    "topic": {
                        "DataType": "String",
                        "StringValue": m.__class__.__name__,
                    },
                },
                "Message": json.dumps(record_asdict(self.mapper.serialize(m))),
            }
            for m in messages
        ]

        errors = []
        for i, entry in enumerate(entries):
            try:
                self.client.publish(**entry)
            except Exception as error:  # pylint: disable=broad-except
                errors.append(PublisherError.EntryError(entries[i], error))
        if len(errors) > 0:
            raise PublisherError(errors)
