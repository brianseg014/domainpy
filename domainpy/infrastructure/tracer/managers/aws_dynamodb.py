import typing
import datetime
import boto3  # type: ignore

from domainpy.exceptions import (
    IdempotencyItemError,
    DefinitionError,
    TraceNotFound,
)
from domainpy.application.command import ApplicationCommand
from domainpy.application.integration import IntegrationEvent
from domainpy.infrastructure.tracer.tracestore import (
    TraceStore,
    TraceResolution,
)
from domainpy.infrastructure.records import CommandRecord, IntegrationRecord
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import record_asdict, record_fromdict
from domainpy.utils.dynamodb import (
    client_serialize as serialize,
    client_deserialize as deserialize,
)


class DynamoDBTraceStore(TraceStore):
    def __init__(self, mapper: Mapper, table_name: str, **kwargs):
        self.mapper = mapper
        self.table_name = table_name

        self.client = boto3.client("dynamodb", **kwargs)

    def get_resolution(self, trace_id: str) -> TraceResolution:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "ProjectionExpression": "resolution, contexts_resolutions",
            "ConsistentRead": True,
        }
        result = self.client.get_item(**item)

        if "Item" not in result:
            raise TraceNotFound()

        resolution = deserialize(result["Item"]["resolution"])
        contexts_resolutions = deserialize(
            result["Item"]["contexts_resolutions"]
        )

        return TraceResolution(
            resolution=resolution,
            errors=tuple(
                [
                    cr["error"]
                    for cr in contexts_resolutions.values()
                    if cr["error"] is not None
                ]
            ),
        )

    def get_integrations(
        self, trace_id: str
    ) -> typing.Generator[IntegrationEvent, None, None]:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "ProjectionExpression": "integrations",
            "ConsistentRead": True,
        }
        result = self.client.get_item(**item)

        if "Item" not in result:
            raise TraceNotFound()

        integrations = deserialize(result["Item"]["integrations"])

        return typing.cast(
            typing.Generator[IntegrationEvent, None, None],
            (
                self.mapper.deserialize(record_fromdict(i))
                for i in integrations
            ),
        )

    def start_trace(self, command: ApplicationCommand) -> None:
        try:
            resolvers = getattr(command, "__resolvers__")
        except AttributeError as error:
            raise DefinitionError(
                "command should have __resolvers__: "
                f"{command.__class__.__name__}"
            ) from error

        command_record = typing.cast(
            CommandRecord, self.mapper.serialize(command)
        )

        epoch = datetime.datetime.utcnow().timestamp()

        epoch_resolution = None
        resolution = TraceResolution.Resolutions.pending
        if len(resolvers) == 0:
            epoch_resolution = epoch
            resolution = TraceResolution.Resolutions.success

        item = {
            "TableName": self.table_name,
            "Item": {
                "trace_id": serialize(command_record.trace_id),
                "topic": serialize(command_record.topic),
                "command": serialize(record_asdict(command_record)),
                "resolution": serialize(resolution),
                "version": serialize(1),
                "timestamp": serialize(epoch),
                "timestamp_resolution": serialize(epoch_resolution),
                "contexts_resolutions": serialize(
                    {
                        context: {
                            "context": context,
                            "resolution": TraceResolution.Resolutions.pending,
                            "error": None,
                            "timestamp": None,
                        }
                        for context in resolvers
                    }
                ),
                "contexts_resolutions_unexpected": serialize({}),
                "integrations": serialize([]),
            },
            "ConditionExpression": "attribute_not_exists(trace_id)",
        }

        try:
            self.client.put_item(**item)
        except self.client.exceptions.ConditionalCheckFailedException as error:
            raise IdempotencyItemError() from error

    def resolve_context(
        self, integration: typing.Union[IntegrationEvent, IntegrationRecord]
    ) -> None:
        if isinstance(integration, IntegrationEvent):
            integration_record = typing.cast(
                IntegrationRecord, self.mapper.serialize(integration)
            )
        elif isinstance(integration, IntegrationRecord):
            integration_record = integration

        try:
            self._try_update_with_expected_context(integration_record)
        except self.client.exceptions.ConditionalCheckFailedException:
            try:
                # Unexpected context
                self._try_update_with_unexpected_context(integration_record)
            except (
                self.client.exceptions.ConditionalCheckFailedException
            ) as error:
                raise TraceNotFound() from error

        self._safe_try_to_resolve_trace(integration_record.trace_id)

    def _try_update_with_expected_context(
        self, integration_record: IntegrationRecord
    ):
        epoch = datetime.datetime.utcnow().timestamp()
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(integration_record.trace_id)},
            "UpdateExpression": "SET "
            "   contexts_resolutions.#context = :context_resolution, "
            "   integrations = list_append(integrations, :new_integrations)",
            "ExpressionAttributeNames": {
                "#context": integration_record.context
            },
            "ExpressionAttributeValues": {
                ":context_resolution": serialize(
                    {
                        "context": integration_record.context,
                        "resolution": integration_record.resolve,
                        "error": integration_record.error,
                        "timestamp": epoch,
                    }
                ),
                ":new_integrations": serialize(
                    [record_asdict(integration_record)]
                ),
            },
            # "ConditionExpression": """
            # attribute_exists(trace_id)
            # AND attribute_exists(contexts_resolutions.#context)
            # """
        }
        self.client.update_item(**item)

    def _try_update_with_unexpected_context(
        self, integration_record: IntegrationRecord
    ):
        epoch = datetime.datetime.utcnow().timestamp()
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(integration_record.trace_id)},
            "UpdateExpression": "SET "
            "   contexts_resolutions_unexpected.#context = :context_resolution, "  # noqa: E501
            "   integrations = list_append(integrations, :new_integrations)",
            "ExpressionAttributeNames": {
                "#context": integration_record.context
            },
            "ExpressionAttributeValues": {
                ":context_resolution": serialize(
                    {
                        "context": integration_record.context,
                        "resolution": integration_record.resolve,
                        "error": integration_record.error,
                        "timestamp": epoch,
                    }
                ),
                ":new_integrations": serialize(
                    [record_asdict(integration_record)]
                ),
            },
            # "ConditionExpression": """
            # attribute_exists(trace_id)
            # """
        }
        self.client.update_item(**item)

    def _safe_try_to_resolve_trace(self, trace_id: str) -> bool:
        item = {
            "TableName": self.table_name,
            "Key": {"trace_id": serialize(trace_id)},
            "ProjectionExpression": "contexts_resolutions",
            "ConsistentRead": True,
        }
        result = self.client.get_item(**item)

        contexts_resolutions = deserialize(
            result["Item"]["contexts_resolutions"]
        )

        # All not pending but not necessarily all same resolution
        # if no resolutions expected, True
        at_least_partial_resolved = all(
            cr["resolution"] != TraceResolution.Resolutions.pending
            for cr in contexts_resolutions.values()
        )
        if at_least_partial_resolved:
            resolutions = set(
                cr["resolution"] for cr in contexts_resolutions.values()
            )

            # If no resolutions expected, success
            if len(contexts_resolutions) == 0:
                resolutions = set([TraceResolution.Resolutions.success])

            # Unified resolution: All success or failure
            if len(resolutions) == 1:
                epoch_resolution = datetime.datetime.utcnow().timestamp()

                resolution = list(resolutions)[0]
                item = {
                    "TableName": self.table_name,
                    "Key": {"trace_id": serialize(trace_id)},
                    "UpdateExpression": "SET "
                    "   resolution = :resolution, "
                    "   timestamp_resolution = :timestamp_resolution",
                    "ExpressionAttributeValues": {
                        ":resolution": serialize(resolution),
                        ":timestamp_resolution": serialize(epoch_resolution),
                    },
                }
                self.client.update_item(**item)
                return True

        return False
