from __future__ import annotations

import json
import typing
import requests

from domainpy.exceptions import PublisherError
from domainpy.application.integration import ScheduleIntegartionEvent
from domainpy.infrastructure.publishers.base import Publisher
from domainpy.infrastructure.transcoder import record_asdict
from domainpy.infrastructure.mappers import Mapper

if typing.TYPE_CHECKING:
    from domainpy.typing.infrastructure import (
        SequenceOfInfrastructureMessage,
    )
    from domainpy.infrastructure.mappers import Mapper


class SchedulerException(Exception):
    pass


class AwsSchedulerPublisher(Publisher):

    def __init__(self, url: str, mapper: Mapper) -> None:
        self.url = url
        self.mapper = mapper

    def _publish(self, messages: SequenceOfInfrastructureMessage):
        errors = []

        entries = [
            {
                'publish_at': getattr(m, m.__publish_at_field__),
                'payload': json.dumps(record_asdict(self.mapper.serialize(m)))
            }
            for m in messages
            if isinstance(m, ScheduleIntegartionEvent)
        ]

        for entry in entries:
            result = requests.post(self.url, json=entry)

            if result.status_code != 200:
                errors.append(
                    PublisherError.EntryError(
                        entry, 
                        SchedulerException(f'{result.status_code} - {result.text}')
                    )
                )
            
        if len(errors) > 0:
            raise PublisherError(errors)
