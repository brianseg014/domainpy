from __future__ import annotations

import typing
import boto3  # type: ignore

from domainpy.infrastructure.publishers.base import Publisher
from domainpy.infrastructure.transcoder import record_asdict
from domainpy.utils.dynamodb import client_serialize as serialize

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.infrastructure import (
        SequenceOfInfrastructureMessage,
    )
    from domainpy.infrastructure.mappers import Mapper


class AwsDynamoDBTablePublisher(Publisher):
    def __init__(
        self,
        table_name: str,
        mapper: Mapper,
        sort_key: typing.Optional[str] = None,
        **kwargs
    ) -> None:
        self.table_name = table_name
        self.mapper = mapper
        self.sort_key = sort_key

        self.client = boto3.client("dynamodb", **kwargs)

    def _publish(self, messages: SequenceOfInfrastructureMessage):
        if self.sort_key is None:
            self._publish_with_partition_key(messages)
        else:
            self._publish_with_partition_key_and_sort_key(messages)

    def _publish_with_partition_key(
        self, messages: SequenceOfInfrastructureMessage
    ):
        entries = [
            {
                "TableName": self.table_name,
                "Item": {
                    "trace_id": serialize(m.__trace_id__),
                    "body": serialize(record_asdict(self.mapper.serialize(m))),
                },
            }
            for m in messages
        ]

        for entry in entries:
            self.client.put_item(**entry)

    def _publish_with_partition_key_and_sort_key(
        self, messages: SequenceOfInfrastructureMessage
    ):
        _sort_key = self.sort_key
        if _sort_key is None:
            raise ValueError("sort_key should not be NoneType")

        entries = [
            {
                "TableName": self.table_name,
                "Item": {
                    "trace_id": serialize(m.__trace_id__),
                    _sort_key: serialize(getattr(messages, _sort_key)),
                    "body": serialize(record_asdict(self.mapper.serialize(m))),
                },
            }
            for m in messages
        ]

        for entry in entries:
            self.client.put_item(**entry)
