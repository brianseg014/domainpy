import typing


class Traceable:
    __trace_id__: typing.ClassVar[typing.Optional[str]] = None
