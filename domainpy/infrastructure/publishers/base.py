from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from domainpy.typing import SystemMessage


class IPublisher(typing.Protocol):
    def publish(
        self,
        messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]],
    ):
        pass
