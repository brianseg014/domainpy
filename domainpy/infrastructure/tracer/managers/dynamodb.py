import boto3  # type: ignore
import typing
import datetime
import dataclasses

from domainpy.infrastructure.records import TraceRecord
from domainpy.utils.dynamodb import client_deserialize as deserialize
from domainpy.utils.dynamodb import client_serialize as serialize


class DynamodbTraceRecordManager:
    def __init__(self, table_name: str, **kwargs):
        self.table_name = table_name

        self.client = boto3.client("dynamodb", **kwargs)

    def get_trace_contexts(
        self, trace_id: str
    ) -> typing.Tuple[TraceRecord.ContextResolution, ...]:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "ProjectionExpression": "contexts_resolutions",
        }
        dynamodb_item = self.client.get_item(**item)

        contexts_resolutions = deserialize(
            dynamodb_item["Item"]["contexts_resolutions"]
        )
        return tuple(
            [
                TraceRecord.ContextResolution(
                    context=cr["context"],
                    resolution=cr["resolution"],
                    timestamp_resolution=cr["timestamp_resolution"],
                    error=cr["error"],
                )
                for cr in contexts_resolutions.values()
            ]
        )

    def store_in_progress(
        self,
        trace_id: str,
        command: dict,
        contexts_resolutions: typing.Tuple[str],
    ) -> None:
        resolutions: typing.Dict[str, dict] = {
            context_name: dataclasses.asdict(
                TraceRecord.ContextResolution(
                    context=context_name,
                    resolution=TraceRecord.Resolution.pending,
                )
            )
            for context_name in contexts_resolutions
        }

        item = {
            "TableName": self.table_name,
            "Item": {
                "trace_id": serialize(trace_id),
                "command": serialize(command),
                "status_code": serialize(TraceRecord.StatusCode.CODE_200),
                "number": serialize(0),
                "resolution": serialize(TraceRecord.Resolution.pending),
                "version": serialize(1),
                "timestamp": serialize(
                    datetime.datetime.timestamp(datetime.datetime.now())
                ),
                "contexts_resolutions": serialize(resolutions),
            },
        }
        self.client.put_item(**item)

    def store_resolve_success(self, trace_id: str) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": "SET resolution = :resolution",
            "ExpressionAttributeValues": {
                ":resolution": serialize(TraceRecord.Resolution.success)
            },
        }
        self.client.update_item(**item)

    def store_resolve_failure(self, trace_id: str) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": "SET resolution = :resolution",
            "ExpressionAttributeValues": {
                ":resolution": serialize(TraceRecord.Resolution.failure)
            },
        }
        self.client.update_item(**item)

    def store_context_resolve_success(
        self, trace_id: str, context: str
    ) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": f"SET contexts_resolutions.{context}.resolution = :resolution",  # noqa: E501
            "ExpressionAttributeValues": {
                ":resolution": serialize(TraceRecord.Resolution.success)
            },
        }
        self.client.update_item(**item)

    def store_context_resolve_failure(
        self, trace_id: str, context: str, error: str
    ) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": f"SET contexts_resolutions.{context}.resolution = :resolution",  # noqa: E501
            "ExpressionAttributeValues": {
                ":resolution": serialize(TraceRecord.Resolution.failure)
            },
        }
        self.client.update_item(**item)
