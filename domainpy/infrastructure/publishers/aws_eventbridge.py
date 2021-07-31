from __future__ import annotations

import json
import typing
import boto3  # type: ignore

from domainpy.exceptions import PublisherError
from domainpy.infrastructure.publishers.base import Publisher

if typing.TYPE_CHECKING:
    from domainpy.typing.application import SystemMessage  # type: ignore
    from domainpy.infrastructure.mappers import Mapper


class AwsEventBridgePublisher(Publisher):
    def __init__(self, bus_name: str, context: str, mapper: Mapper, **kwargs):
        self.bus_name = bus_name
        self.context = context
        self.mapper = mapper

        self.client = boto3.client("events", **kwargs)

    def _publish(
        self,
        messages: typing.Sequence[SystemMessage],
    ):
        entries = [
            {
                "Source": self.context,
                "Detail": json.dumps(self.mapper.serialize_asdict(m)),
                "DetailType": m.__class__.__name__,
                "EventBusName": self.bus_name,
            }
            for m in messages
        ]

        response = self.client.put_events(Entries=entries)
        if response["FailedEntryCount"] > 0:
            errors = [
                PublisherError.EntryError(messages[i], e["ErrorCode"])
                for i, e in enumerate(response["Entries"])
                if "EventId" not in e  # Failed
            ]
            raise PublisherError(f"Bus name: {self.bus_name}", errors)
