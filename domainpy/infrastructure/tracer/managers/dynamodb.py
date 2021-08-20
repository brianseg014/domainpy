import typing
import datetime
import dataclasses
import boto3  # type: ignore
import botocore.exceptions  # type: ignore

from domainpy.infrastructure.records import CommandRecord
from domainpy.infrastructure.tracer.recordmanager import (
    TraceRecordManager,
    ContextResolution,
    Resolution,
    StatusCode,
)
from domainpy.utils.dynamodb import client_deserialize as deserialize
from domainpy.utils.dynamodb import client_serialize as serialize


class DynamoDBTraceRecordManager(TraceRecordManager):
    def __init__(self, table_name: str, **kwargs):
        self.table_name = table_name

        self.client = boto3.client("dynamodb", **kwargs)

    def get_trace_contexts(
        self, trace_id: str
    ) -> typing.Generator[ContextResolution, None, None]:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "ProjectionExpression": "contexts_resolutions",
            "ConsistentRead": True,
        }
        dynamodb_item = self.client.get_item(**item)

        contexts_resolutions = deserialize(
            dynamodb_item["Item"]["contexts_resolutions"]
        )
        return (
            ContextResolution(
                context=cr["context"],
                resolution=cr["resolution"],
                timestamp_resolution=cr["timestamp_resolution"],
                error=cr["error"],
            )
            for cr in contexts_resolutions.values()
        )

    def store_in_progress(
        self,
        trace_id: str,
        command_record: CommandRecord,
        contexts_resolutions: typing.Tuple[str, ...],
    ) -> None:
        resolutions: typing.Dict[str, dict] = {
            context_name: dataclasses.asdict(
                ContextResolution(
                    context=context_name,
                    resolution=Resolution.pending,
                )
            )
            for context_name in contexts_resolutions
        }

        command_record_dict = dataclasses.asdict(command_record)
        item = {
            "TableName": self.table_name,
            "Item": {
                "trace_id": serialize(trace_id),
                "topic": serialize(command_record.topic),
                "command": serialize(command_record_dict),
                "resolution": serialize(Resolution.pending),
                "version": serialize(1),
                "timestamp": serialize(
                    datetime.datetime.timestamp(datetime.datetime.now())
                ),
                "contexts_resolutions": serialize(resolutions),
                "contexts_resolutions_unexpected": serialize({}),
            },
        }
        self.client.put_item(**item)

    def store_resolve_success(self, trace_id: str) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": "SET resolution = :resolution",
            "ExpressionAttributeValues": {
                ":resolution": serialize(Resolution.success)
            },
        }
        self.client.update_item(**item)

    def store_resolve_failure(self, trace_id: str) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": "SET resolution = :resolution",
            "ExpressionAttributeValues": {
                ":resolution": serialize(Resolution.failure)
            },
        }
        self.client.update_item(**item)

    def store_context_resolve_success(
        self, trace_id: str, context: str
    ) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": (
                f"SET contexts_resolutions.{context}.resolution = :resolution, "  # noqa: E501 # pylint: disable=line-too-long
                f"contexts_resolutions.{context}.timestamp_resolution = :timestamp"  # noqa: E501 # pylint: disable=line-too-long
            ),
            "ExpressionAttributeValues": {
                ":resolution": serialize(Resolution.success),
                ":timestamp": serialize(
                    datetime.datetime.timestamp(datetime.datetime.now())
                ),
            },
        }

        try:
            self.client.update_item(**item)
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "ValidationException":
                item = {
                    "TableName": self.table_name,
                    "Key": {"trace_id": serialize(trace_id)},
                    "UpdateExpression": (
                        f"SET contexts_resolutions_unexpected.{context} = :context_resolution "  # noqa: E501 # pylint: disable=line-too-long
                    ),
                    "ExpressionAttributeValues": {
                        ":context_resolution": serialize(
                            {
                                "resolution": Resolution.success,
                                "timestamp_resolution": datetime.datetime.timestamp(  # noqa: E501
                                    datetime.datetime.now()
                                ),
                            }
                        )
                    },
                }
                self.client.update_item(**item)
            else:
                raise error

    def store_context_resolve_failure(
        self, trace_id: str, context: str, error: str
    ) -> None:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "UpdateExpression": (
                f"SET contexts_resolutions.{context}.resolution = :resolution, "  # noqa: E501 # pylint: disable=line-too-long
                f"contexts_resolutions.{context}.#error = :error, "
                f"contexts_resolutions.{context}.timestamp_resolution = :timestamp"  # noqa: E501 # pylint: disable=line-too-long
            ),
            "ExpressionAttributeValues": {
                ":resolution": serialize(Resolution.failure),
                ":error": serialize(error),
                ":timestamp": serialize(
                    datetime.datetime.timestamp(datetime.datetime.now())
                ),
            },
            "ExpressionAttributeNames": {"#error": "error"},
        }

        try:
            self.client.update_item(**item)
        except botocore.exceptions.ClientError as boto_error:
            if boto_error.response["Error"]["Code"] == "ValidationException":
                item = {
                    "TableName": self.table_name,
                    "Key": {"trace_id": serialize(trace_id)},
                    "UpdateExpression": (
                        f"SET contexts_resolutions_unexpected.{context} = :context_resolution "  # noqa: E501 # pylint: disable=line-too-long
                    ),
                    "ExpressionAttributeValues": {
                        ":context_resolution": serialize(
                            {
                                "resolution": Resolution.failure,
                                "error": error,
                                "timestamp_resolution": datetime.datetime.timestamp(  # noqa: E501
                                    datetime.datetime.now()
                                ),
                            }
                        )
                    },
                }
                self.client.update_item(**item)
            else:
                raise boto_error
