import abc
import enum
import typing

from domainpy.exceptions import DefinitionError


class MISSING:
    pass


Message = typing.TypeVar("Message")


class ISubscriber(typing.Generic[Message], abc.ABC):
    @abc.abstractmethod
    def __route__(self, message: Message) -> None:
        pass  # pragma: no cover


class IBus(typing.Generic[Message], abc.ABC):
    @abc.abstractmethod
    def attach(self, subscriber: ISubscriber[Message]) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def publish(self, message: Message) -> None:
        pass  # pragma: no cover


class Bus(IBus[Message]):
    def __init__(self):
        self.subscribers: typing.List[ISubscriber[Message]] = []

    def attach(self, subscriber: ISubscriber[Message]) -> None:
        if not hasattr(subscriber, "__route__"):
            sub_name = subscriber.__class__.__name__
            raise DefinitionError(
                f"{sub_name} should have __route__ method. "
                "Check bus_subscribers."
            )

        self.subscribers.append(subscriber)

    def publish(self, message: Message) -> None:
        for subscriber in self.subscribers:
            subscriber.__route__(message)


class FilterPolicy(ISubscriber[Message], Bus[Message]):
    class Effect(enum.Enum):
        MATCH = "MATCH"
        NOT_MATCH = "NOT_MATCH"

    def __init__(
        self,
        *,
        contexts: typing.Optional[typing.Sequence[str]] = None,
        topics: typing.Optional[typing.Sequence[str]] = None,
        concepts: typing.Optional[typing.Sequence[str]] = None,
        types: typing.Optional[typing.Sequence[type]] = None,
        targets: typing.Optional[typing.Sequence[ISubscriber]] = None,
        effect: Effect = Effect.MATCH,
    ) -> None:
        super().__init__()

        self.contexts = contexts
        self.topics = topics
        self.concepts = concepts
        self.types = types
        self.effect = effect

        if targets is not None:
            for target in targets:
                self.attach(target)

    def __route__(self, message: Message) -> None:
        if self.effect == FilterPolicy.Effect.MATCH:
            if self.match(message):
                self.publish(message)
        elif self.effect == FilterPolicy.Effect.NOT_MATCH:
            if not self.match(message):
                self.publish(message)

    def match(self, message: Message) -> bool:
        if self.contexts is not None:
            context = getattr(message, "__context__", MISSING)
            if context is MISSING:
                raise DefinitionError("message should have __context__ field")

            if context not in self.contexts:
                return False

        if self.topics is not None:
            topic = getattr(message, "__topic__", MISSING)
            if topic is MISSING:
                raise DefinitionError("message should have __topic__ field")

            if topic not in self.topics:
                return False

        if self.concepts is not None:
            concept = getattr(message, "__concept__", MISSING)
            if concept is MISSING:
                raise DefinitionError("message should have __concept__ field")

            if concept not in self.concepts:
                return False

        if self.types is not None:
            if not isinstance(message, tuple(self.types)):
                return False

        return True
