from __future__ import annotations

import typing

from domainpy.infrastructure.publishers.base import IPublisher

if typing.TYPE_CHECKING:
    from domainpy.typing.application import SystemMessage  # type: ignore


class MemoryPublisher(IPublisher, list):
    def _publish(
        self,
        messages: typing.Sequence[SystemMessage],
    ):
        self.extend(messages)
