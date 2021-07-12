from typing import Type
import uuid
import json

from domainpy import exceptions as excs
from domainpy.utils.constructable import Constructable, constructable
from domainpy.utils.dictable import Dictable
from domainpy.utils.immutable import Immutable

class ValueObject(Constructable, Dictable, Immutable):

    def __hash__(self):
        return hash(json.dumps(self.__to_dict__(), sort_keys=True))
    
    def __eq__(self, other):
        if other is None:
            return False

        return (
            self.__class__ == other.__class__
            and self.__hash__() == other.__hash__()
        )
    
    def __repr__(self):
        return f'{self.__class__.__name__}({json.dumps(self.__to_dict__())})' # pragma: no cover


class identity(constructable):

    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)
        
        if not hasattr(new_cls, '__annotations__'):
            raise excs.DefinitionError(f'{cls.__name__} must include id: str annotation')
        else:
            new_cls_annotations = new_cls.__annotations__
            if 'id' in new_cls_annotations:
                if new_cls_annotations['id'] != str:
                    raise excs.DefinitionError(f'{new_cls.__name__}.id must be type of str')
            else:
                raise excs.DefinitionError(f'{new_cls.__name__} must include id: str annotation')
                
            if len(new_cls_annotations) > 1:
                raise excs.DefinitionError(f'{new_cls.__name__} must include only id: str annotation, some other annotations found')

        return new_cls
    
class Identity(ValueObject, metaclass=identity):
    id: str
    
    @classmethod
    def from_text(cls, id: str):
        return cls(id=id)
    
    @classmethod
    def create(cls):
        return cls.from_text(
            str(uuid.uuid4())
        )