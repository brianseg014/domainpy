from functools import update_wrapper, partial

from domainpy import exceptions as excs
from domainpy.domain.model.event import DomainEvent


class Projection:

    def __route__(self, e: DomainEvent):
        self.project(e)

    def project(self, e: DomainEvent):
        pass


class projector:

    def __init__(self, func):
        update_wrapper(self, func)

        self.func = func

        self.projectors = {}

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)

    def __call__(self, projection: Projection, event: DomainEvent):
        if event.__class__ not in self.projectors:
            return

        projector = self.projectors[event.__class__]
        projector(projection, event)

    def event(self, event_type: type):
        def inner_function(func):
            if event_type in self.projectors:
                raise excs.DefinitionError(f'{event_type.__name__} projector already defined near to {self.func.__qualname__}')

            self.projectors[event_type] = func
            return func
        return inner_function
    