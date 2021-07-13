from __future__ import annotations

import typing
import collections.abc

if typing.TYPE_CHECKING:
    from domainpy.typing import SystemMessage

from domainpy.infrastructure.publishers.base import IPublisher


class MemoryPublisher(IPublisher):

    def __init__(self, *args, **kwargs):
        self.heap = []

    def publish(self, messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]]):
        if not isinstance(messages, collections.abc.Sequence):
            messages = tuple([messages])

        self.heap.extend(messages)
    