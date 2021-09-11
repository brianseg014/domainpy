import typing

from domainpy.exceptions import DefinitionError
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.typing.infrastructure import InfrastructureMessage
from domainpy.typing.infrastructure import InfrastructureRecord


class MessageTypeNotFoundError(Exception):
    pass


class Mapper:
    def __init__(self, transcoder: Transcoder) -> None:
        self.transcoder = transcoder

        self._map: typing.Dict[str, typing.Any] = {}

    def register(self, cls):
        context = getattr(cls, "__context__", "default")
        topic = cls.__name__

        default = f"default:{topic}"
        contexted = f"{context}:{topic}"
        if contexted in self._map:
            if default == contexted:
                raise DefinitionError(
                    "Ambiguous name. "
                    "Consider add __context__ field for disambiguation."
                )

        self._map[default] = cls
        self._map[contexted] = cls
        return cls

    def get(
        self, topic: str, context: str = "default"
    ) -> typing.Optional[type]:
        default = f"default:{topic}"
        contexted = f"{context}:{topic}"
        if default in self._map:
            return self._map[default]

        if contexted in self._map:
            return self._map[contexted]

        return None

    def serialize(
        self, message: InfrastructureMessage
    ) -> InfrastructureRecord:
        return typing.cast(
            InfrastructureRecord, self.transcoder.serialize(message)
        )

    def deserialize(
        self, record: InfrastructureRecord
    ) -> InfrastructureMessage:
        context = getattr(record, "context", "default")
        topic = record.topic

        message_type = self.get(topic, context)
        if message_type is None:
            raise MessageTypeNotFoundError(f"unable to find type {topic}")

        return self.transcoder.deserialize(record, message_type)
