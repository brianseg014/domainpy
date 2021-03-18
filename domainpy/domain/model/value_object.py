
import json
from typing import TypeVar, Generic
from datetime import datetime, date
from uuid import UUID, uuid4

from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.utils.dictable import Dictable
from domainpy.domain.exceptions import ValueObjectIsNotSerializable


class ValueObject(Constructable, Immutable, Dictable):
    
    def __hash__(self):
        return hash(json.dumps(self.__to_dict__(), sort_keys=True))
    
    def __eq__(self, other):
        if other is None:
            return False
        
        return isinstance(other, ValueObject) and self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not (self == other)
    
    def __repr__(self):
        return f'{self.__class__.__name__}({json.dumps(self.__to_dict__())})'

class Identity(ValueObject):
    
    def __init__(self, id: str):
        if hasattr(self.__class__, '__annotations__'):
            attrs = self.__class__.__dict__['__annotations__']
            
            assert attrs == { "id": str }
        
        if not isinstance(id, str):
            raise TypeError(f'id should be instance of str, found {id.__class__.__name__}')
        
        self.__dict__.update(id=id)
        
    @classmethod
    def from_text(cls, id: str):
        return cls(id=id)
    
    @classmethod
    def create(cls):
        return cls.from_text(
            str(uuid4())
        )
    