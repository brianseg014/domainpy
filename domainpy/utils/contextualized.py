import typing


class Contextualized:
    __context__: typing.ClassVar[typing.Optional[str]] = None

    @classmethod
    def set_default_context(cls, context: str) -> None:
        if context is None:
            raise ValueError("context should not be NoneType")

        Contextualized.__context__ = context
