from __future__ import annotations

import typing

from domainpy.infrastructure.publishers.base import Publisher

if typing.TYPE_CHECKING:
    from domainpy.typing.infrastructure import (
        SequenceOfInfrastructureMessage,
    )


class MemoryPublisher(Publisher, list):
    def _publish(
        self,
        messages: SequenceOfInfrastructureMessage,
    ):
        self.extend(messages)
