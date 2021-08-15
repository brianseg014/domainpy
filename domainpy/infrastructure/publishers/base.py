from __future__ import annotations

import abc
import typing
import collections.abc

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.infrastructure import (
        SequenceOfInfrastructureMessage,
        SingleOrSequenceOfInfrastructureMessage,
    )


class IPublisher(abc.ABC):
    @abc.abstractmethod
    def publish(self, messages: SingleOrSequenceOfInfrastructureMessage):
        pass


class Publisher(IPublisher):
    def publish(self, messages: SingleOrSequenceOfInfrastructureMessage):
        if not isinstance(messages, collections.abc.Sequence):
            messages = tuple([messages])
        self._publish(messages)

    @abc.abstractmethod
    def _publish(self, messages: SequenceOfInfrastructureMessage):
        pass
