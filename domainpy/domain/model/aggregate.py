from __future__ import annotations

import datetime
import functools
import typing

if typing.TYPE_CHECKING:
    from domainpy.domain.model.event import DomainEvent

from domainpy.domain.model.value_object import Identity
from domainpy.exceptions import DefinitionError, VersionError


class AggregateRoot:
    def __init__(self, id: Identity):
        self.__id__ = id

        self.__version__ = 0
        self.__changes__ = []  # New events
        self.__seen__ = []  # Routed events (mutated)

    @property
    def __selector__(self):
        return Selector(self)

    def __stamp__(self, event_type: typing.Type[DomainEvent]):
        return functools.partial(
            event_type,
            __stream_id__=f"{self.__id__.id}:{self.__class__.__name__}",
            __number__=self.__version__ + 1,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    def __apply__(self, event: DomainEvent):
        self.__route__(event)

        self.__changes__.append(event)

    def __route__(self, event: DomainEvent):
        next_version = self.__version__ + 1

        if event.__number__ != next_version:
            raise VersionError(next_version, event.__number__)

        self.__version__ = next_version
        self.__seen__.append(event)

        self.mutate(event)

    def mutate(self, event: DomainEvent):
        pass  # pragma: no cover


class Selector:
    def __init__(self, aggregate: AggregateRoot):
        self.aggregate = aggregate

    def get_trace(
        self, trace_id: str, include_event_type: type[DomainEvent] = None
    ) -> tuple[DomainEvent]:
        events = tuple(
            [e for e in self.aggregate.__seen__ if e.__trace_id__ == trace_id]
        )

        if include_event_type:
            events = tuple(
                [e for e in events if isinstance(e, include_event_type)]
            )

        return events

    def get_trace_if_not_compensated(
        self,
        trace_id: str,
        compensate_type: type[DomainEvent],
        include_event_type: type[DomainEvent] = None,
    ) -> tuple[DomainEvent]:

        events = self.get_trace(
            trace_id, include_event_type=include_event_type
        )

        compensated = any(isinstance(e, compensate_type) for e in events)

        if not compensated:
            return events
        else:
            return ()


class mutator:
    def __init__(self, func):
        functools.update_wrapper(self, func)

        self.func = func

        self.mutators = {}

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def __call__(self, aggregate, event: DomainEvent):
        if event.__class__ not in self.mutators:
            return

        mutator = self.mutators[event.__class__]
        mutator(aggregate, event)

    def event(self, event_type: type[DomainEvent]):
        def inner_function(func):
            if event_type in self.mutators:
                self_name = event_type.__name__
                func_name = self.func.__qualname__
                raise DefinitionError(
                    f"{self_name} mutator already defined near to {func_name}"
                )

            self.mutators[event_type] = func
            return func

        return inner_function
