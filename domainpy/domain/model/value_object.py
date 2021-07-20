import json
import uuid

from domainpy.exceptions import DefinitionError
from domainpy.utils.data import SystemData, system_data


class ValueObject(SystemData):
    def __hash__(self) -> int:
        return hash(json.dumps(self.__to_dict__(), sort_keys=True))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        if other is None:
            return False

        return self.__hash__() == other.__hash__()

    def __repr__(self):
        self_name = self.__class__.__name__
        self_json = json.dumps(self.__to_dict__())
        return f"{self_name}({self_json})"  # pragma: no cover


class identity(system_data):
    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)

        if name == "Identity":
            return new_cls

        if not hasattr(new_cls, "__annotations__"):
            raise DefinitionError(
                f"{cls.__name__} must include id: str annotation"
            )
        else:
            new_cls_annotations = new_cls.__annotations__
            if "id" in new_cls_annotations:
                if new_cls_annotations["id"] != str:
                    raise DefinitionError(
                        f"{new_cls.__name__}.id must be type of str"
                    )
            else:
                raise DefinitionError(
                    f"{new_cls.__name__} must include id: str annotation"
                )

            if len(new_cls_annotations) > 1:
                raise DefinitionError(
                    f"{new_cls.__name__} must include only id: str annotation,"
                    "some other annotations found"
                )

        return new_cls


class Identity(ValueObject, metaclass=identity):
    @classmethod
    def from_text(cls, id: str):
        return cls(id=id)

    @classmethod
    def create(cls):
        return cls.from_text(str(uuid.uuid4()))
