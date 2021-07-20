from __future__ import annotations

import datetime
import functools
import typing

if typing.TYPE_CHECKING:
    from domainpy.typing.application import SystemMessage  # type: ignore # noqa: E501
    from domainpy.application.command import ApplicationCommand
    from domainpy.application.integration import IntegrationEvent
    from domainpy.domain.model.event import DomainEvent


class ApplicationService:
    def stamp_integration(self, integration_type: type[IntegrationEvent]):
        return functools.partial(
            integration_type,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    def handle(self, message: SystemMessage):
        pass


class handler:
    def __init__(self, func):
        functools.update_wrapper(self, func)

        self.func = func

        self.handlers = dict()

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def __call__(self, service: ApplicationService, message: SystemMessage):
        handlers = self.handlers.get(message.__class__, None)
        if handlers:
            for h in handlers:
                h(service, message)

        if hasattr(service, "__partials__"):
            partials = service.__partials__.get(message.__class__, None)  # type: ignore # noqa: E501
            if partials:
                for p in set(partials):
                    p(service, message)
                    partials.remove(p)

    def command(self, command_type: typing.Type[ApplicationCommand]):
        def inner_function(func):
            command_handlers = self.handlers.setdefault(command_type, set())
            command_handlers.add(func)
            return func

        return inner_function

    def integration(self, integration_type: typing.Type[IntegrationEvent]):
        def inner_function(func):
            integration_handlers = self.handlers.setdefault(
                integration_type, set()
            )
            integration_handlers.add(func)
            return func

        return inner_function

    def event(self, event_type: typing.Type[DomainEvent]):
        def inner_function(func):
            event_handlers = self.handlers.setdefault(event_type, set())
            event_handlers.add(func)
            return func

        return inner_function

    def trace(self, *messages: typing.Sequence[typing.Type[SystemMessage]]):
        def inner_function(func):
            def wrapper(*args, **kwargs):
                service = args[0]
                trace = kwargs.pop("__trace__")
                leadings = kwargs.pop("__leadings__")

                if not hasattr(service, "__partials__"):
                    service.__partials__ = {}

                if len(leadings) > 0:
                    new_trace = []
                    new_trace.extend(trace)
                    new_trace.append(args[1])

                    partials = service.__partials__.setdefault(
                        leadings[0], set()
                    )
                    partials.add(
                        functools.partial(
                            wrapper,
                            __trace__=new_trace,
                            __leadings__=leadings[1:],
                        )
                    )
                else:
                    return func(service, *trace, *args[1:], **kwargs)

            trace_handlers = self.handlers.setdefault(messages[0], set())
            trace_handlers.add(
                functools.partial(
                    wrapper, __trace__=[], __leadings__=messages[1:]
                )
            )

            return wrapper

        return inner_function
