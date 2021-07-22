from __future__ import annotations

import domainpy.compat_typing as typing

if typing.TYPE_CHECKING:
    from domainpy.typing.application import SystemMessage  # type: ignore


class IPublisher(typing.Protocol):
    def publish(
        self,
        messages: typing.Union[SystemMessage, typing.Sequence[SystemMessage]],
    ):
        pass
