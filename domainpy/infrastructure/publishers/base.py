from __future__ import annotations

import abc
import typing
import collections.abc

if typing.TYPE_CHECKING:  # pragma: no cover
    from domainpy.typing.application import SystemMessage  # type: ignore


class IPublisher(abc.ABC):
    def publish(
        self,
        messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]],
    ):
        if not isinstance(messages, collections.abc.Sequence):
            messages = tuple([messages])
        self._publish(messages)

    @abc.abstractmethod
    def _publish(self, messages: typing.Sequence[SystemMessage]):
        pass
