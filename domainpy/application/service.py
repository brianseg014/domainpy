from __future__ import annotations

import abc
import datetime
import functools
import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.application import ApplicationMessage  # type: ignore # noqa: E501
    from domainpy.application.command import ApplicationCommand
    from domainpy.application.integration import IntegrationEvent
    from domainpy.domain.model.event import DomainEvent
    from domainpy.domain.model.exceptions import DomainError


class ApplicationService(abc.ABC):
    @classmethod
    def stamp_integration(
        cls, integration_type: typing.Type[IntegrationEvent]
    ):
        return functools.partial(
            integration_type,
            __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
        )

    @abc.abstractmethod
    def handle(self, message: ApplicationMessage) -> None:
        pass  # pragma: no cover


class handler:  # pylint: disable=invalid-name
    def __init__(self, func):
        functools.update_wrapper(self, func)

        self.func = func

        self.handlers = dict()

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def __call__(
        self, service: ApplicationService, message: ApplicationMessage
    ):
        handlers = self.handlers.get(message.__class__, None)
        if handlers:
            for h in handlers:
                h(service, message)

        if hasattr(service, "__partials__"):
            partials = service.__partials__.get(  # type: ignore
                message.__class__, None
            )
            if partials:
                for p in set(partials):
                    p(service, message)
                    partials.remove(p)

    def command(self, command_type: typing.Type[ApplicationCommand]):
        def inner_function(func):
            def wrapper(service, message, *args, **kwargs):
                handle = getattr(message, "__handle__", "default")
                if handle == "default":
                    func(service, message, *args, **kwargs)

            command_handlers = self.handlers.setdefault(command_type, set())
            command_handlers.add(wrapper)
            return func

        return inner_function

    def integration(self, integration_type: typing.Type[IntegrationEvent]):
        def inner_function(func):
            def wrapper(service, message, *args, **kwargs):
                handle = getattr(message, "__handle__", "default")
                if handle == "default":
                    func(service, message, *args, **kwargs)

            integration_handlers = self.handlers.setdefault(
                integration_type, set()
            )
            integration_handlers.add(wrapper)
            return func

        return inner_function

    def event(self, event_type: typing.Type[DomainEvent]):
        def inner_function(func):
            def wrapper(service, message, *args, **kwargs):
                handle = getattr(message, "__handle__", "default")
                if handle == "default":
                    func(service, message, *args, **kwargs)

            event_handlers = self.handlers.setdefault(event_type, set())
            event_handlers.add(wrapper)
            return func

        return inner_function

    def error(self, error_type: typing.Type[DomainError]):
        def inner_func(func):
            def wrapper(service, message, *args, **kwargs):
                handle = getattr(message, "__handle__", "default")
                if handle == "default":
                    func(service, message, *args, **kwargs)

            error_handlers = self.handlers.setdefault(error_type, set())
            error_handlers.add(wrapper)
            return func

        return inner_func

    def trace(
        self,
        *messages: typing.Union[
            typing.Type[ApplicationMessage],
            typing.Tuple[typing.Type[ApplicationMessage], ...],
        ]
    ):
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

                    _leadings = leadings[0]
                    if not isinstance(_leadings, tuple):
                        _leadings = tuple([_leadings])

                    for _leading in _leadings:
                        partials = service.__partials__.setdefault(
                            _leading, set()
                        )
                        partials.add(
                            functools.partial(
                                wrapper,
                                __trace__=new_trace,
                                __leadings__=leadings[1:],
                            )
                        )
                    return None

                # Avoid to call function if the message is being process
                # due to rebuilding state
                handle = getattr(args[-1], "__handle__", "default")
                if handle == "rebuilding":
                    return None

                return func(service, *trace, *args[1:], **kwargs)

            _messages = messages[0]
            if not isinstance(_messages, tuple):
                _messages = tuple([_messages])

            for _message in _messages:
                trace_handlers = self.handlers.setdefault(_message, set())
                trace_handlers.add(
                    functools.partial(
                        wrapper, __trace__=[], __leadings__=messages[1:]
                    )
                )

            return wrapper

        return inner_function

    @classmethod
    def any(
        cls, *messages: typing.Tuple[typing.Type[ApplicationMessage], ...]
    ):
        return tuple(*messages)
