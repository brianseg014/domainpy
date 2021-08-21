from __future__ import annotations

import json
import typing
import boto3  # type: ignore

from domainpy.application.integration import ScheduleIntegartionEvent
from domainpy.infrastructure.publishers.base import Publisher
from domainpy.infrastructure.transcoder import record_asdict

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.infrastructure import (
        InfrastructureMessage,
    )
    from domainpy.infrastructure.mappers import Mapper


class AwsStepFunctionSchedulerPublisher(Publisher):
    def __init__(self, state_machine_arn: str, mapper: Mapper, **kwargs):
        self.state_machine_arn = state_machine_arn
        self.mapper = mapper

        self.client = boto3.client("stepfunctions", **kwargs)

    def _publish(
        self,
        messages: typing.Sequence[InfrastructureMessage],
    ):
        entries = [
            {
                "stateMachineArn": self.state_machine_arn,
                "input": json.dumps({
                    "publish_at": getattr(m, m.__publish_at_field__),
                    "payload": record_asdict(self.mapper.serialize(m))
                })
            }
            for m in messages
            if isinstance(m, ScheduleIntegartionEvent)
        ]

        for entry in entries:
            self.client.start_execution(**entry)
