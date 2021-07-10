from typing import Type
from datetime import datetime

from domainpy.domain.model.event import DomainEvent

class EventStream(list[DomainEvent]):

    def substream(self, 
            topic_type: Type[DomainEvent]=None, 
            from_timestamp: datetime=None, to_timestamp: datetime=None, 
            from_number: int=None, to_number: int=None) -> 'EventStream':

        filters = []
        if topic_type is not None:
            filters.append(
                lambda e: isinstance(e, topic_type)
            )

        if from_timestamp is not None:
            filters.append(
                lambda e: e.__timestamp__ >= from_timestamp
            )

        if to_timestamp is not None:
            filters.append(
                lambda e: e.__timestamp__ <= to_timestamp
            )

        if from_number is not None:
            filters.append(
                lambda e: e.__number__ >= from_number
            )

        if to_number is not None:
            filters.append(
                lambda e: e.__number__ <= to_number
            )

        filtered = EventStream([
            e for e in self
            if all(f(e) for f in filters)
        ])

        return filtered
    