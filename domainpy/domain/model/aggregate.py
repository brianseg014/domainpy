from __future__ import annotations

import typing
import datetime
import functools

from domainpy.domain.model.entity import DomainEntity
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity
from domainpy.exceptions import DefinitionError, VersionError


class AggregateRoot(DomainEntity):
    def __init__(self, identity: Identity):
        super().__init__(identity, self)

        self.__version__: int = 0
        self.__changes__: typing.List[DomainEvent] = []  # New events
        self.__seen__: typing.List[DomainEvent] = []  # Routed events (mutated)

    @property
    def __selector__(self):
        return Selector(e for e in self.__seen__)

    def __stamp__(self, event_type: typing.Type[DomainEvent]):
        identity = self.__identity__.identity  # type: ignore
        aggregate_name = self.__class__.__name__

        return functools.partial(
            event_type,
            __stream_id__=f"{identity}:{aggregate_name}",
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


TDomainEvent = typing.TypeVar("TDomainEvent", bound=DomainEvent)


class Selector(tuple):
    def filter_trace(self, trace_id: str) -> Selector:
        return Selector([e for e in self if e.__trace_id__ == trace_id])

    def filter_event_type(
        self,
        event_type: typing.Union[
            typing.Type[TDomainEvent], typing.Tuple[typing.Type[TDomainEvent]]
        ],
    ) -> Selector:
        return Selector([e for e in self if isinstance(e, event_type)])

    def get_events_for_compensation(
        self,
        trace_id: str,
        empty_if_has_event: typing.Union[
            typing.Type[DomainEvent], typing.Tuple[typing.Type[DomainEvent]]
        ],
        return_event: typing.Union[
            typing.Type[TDomainEvent], typing.Tuple[typing.Type[TDomainEvent]]
        ],
    ) -> typing.Tuple[TDomainEvent, ...]:
        # fmt: off
        compensation_events = (
            self
            .filter_trace(trace_id)
            .filter_event_type(empty_if_has_event)
        )
        # fmt: on
        compensated = len(compensation_events) > 0

        if compensated:
            return ()

        return self.filter_trace(trace_id).filter_event_type(return_event)


class mutator:  # pylint: disable=invalid-name
    def __init__(self, func):
        functools.update_wrapper(self, func)

        self.func = func

        self.mutators = {}

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def __call__(self, aggregate, event: DomainEvent):
        if event.__class__ not in self.mutators:
            return

        m = self.mutators[event.__class__]
        m(aggregate, event)

    def event(self, event_type: typing.Type[DomainEvent]):
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
