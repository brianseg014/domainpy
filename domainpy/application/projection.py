from __future__ import annotations

import typing
import functools

if typing.TYPE_CHECKING:
    from domainpy.domain.model.event import DomainEvent

from domainpy.exceptions import DefinitionError


class Projection:

    def __route__(self, e: DomainEvent):
        self.project(e)

    def project(self, e: DomainEvent):
        pass


class projector:

    def __init__(self, func):
        functools.update_wrapper(self, func)

        self.func = func

        self.projectors = {}

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def __call__(self, projection: Projection, event: DomainEvent):
        if event.__class__ not in self.projectors:
            return

        projector = self.projectors[event.__class__]
        projector(projection, event)

    def event(self, event_type: type[DomainEvent]):
        def inner_function(func):
            if event_type in self.projectors:
                raise DefinitionError(f'{event_type.__name__} projector already defined near to {self.func.__qualname__}')

            self.projectors[event_type] = func
            return func
        return inner_function
    