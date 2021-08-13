import typing


class Traceable:
    __trace_id__: typing.ClassVar[typing.Optional[str]] = None

    @classmethod
    def set_default_trace_id(cls, trace_id: str) -> None:
        if trace_id is None:
            raise TypeError("trace_id should not be None")

        Traceable.__trace_id__ = trace_id
