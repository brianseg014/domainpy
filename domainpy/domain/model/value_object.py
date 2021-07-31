import uuid

from domainpy.exceptions import DefinitionError
from domainpy.utils.data import SystemData, MetaSystemData


class ValueObject(SystemData):
    pass


class MetaIdentity(MetaSystemData):
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)

        if not hasattr(new_cls, "__annotations__"):
            raise DefinitionError(
                f"{cls.__name__} must include id: str annotation"
            )

        new_cls_annotations = new_cls.__annotations__
        if "identity" in new_cls_annotations:
            if new_cls_annotations["identity"] != str:
                raise DefinitionError(
                    f"{new_cls.__name__}.identity must be type of str"
                )
        else:
            raise DefinitionError(
                f"{new_cls.__name__} must include identity: str annotation"
            )

        if len(new_cls_annotations) > 1:
            raise DefinitionError(
                f"{new_cls.__name__} must include only identity: "
                "str annotation, some other annotations found"
            )

        return new_cls


class Identity(ValueObject, metaclass=MetaIdentity):
    identity: str

    @classmethod
    def from_text(cls, identity: str):
        return cls(identity=identity)  # type: ignore

    @classmethod
    def create(cls):
        return cls.from_text(str(uuid.uuid4()))
