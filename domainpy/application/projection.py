from __future__ import annotations

import abc
import typing
import functools

from domainpy.exceptions import DefinitionError

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.domain.model.event import DomainEvent


class Projection(abc.ABC):
    @abc.abstractmethod
    def project(self, event: DomainEvent):
        pass  # pragma: no cover


class projector:  # pylint: disable=invalid-name
    def __init__(self, func):
        functools.update_wrapper(self, func)

        self.func = func

        self.projectors = {}

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def __call__(self, projection: Projection, event: DomainEvent):
        if event.__class__ not in self.projectors:
            return

        p = self.projectors[event.__class__]
        p(projection, event)

    def event(self, event_type: typing.Type[DomainEvent]):
        def inner_function(func):
            if event_type in self.projectors:
                event_name = event_type.__name__
                func_name = self.func.__qualname__
                raise DefinitionError(
                    f"{event_name} projector already defined near {func_name}"
                )

            self.projectors[event_type] = func
            return func

        return inner_function
