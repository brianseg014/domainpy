
import json
from datetime import datetime, date
from uuid import UUID, uuid4

from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable
from domainpy.domain.model.exceptions import ValueObjectIsNotSerializable

class ValueObject(Constructable, Immutable):
    
    def __hash__(self):
        return hash(json.dumps(self.__to_dict__(), sort_keys=True))
    
    def __eq__(self, other):
        if other is None:
            return False
        
        return isinstance(other, ValueObject) and self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not (self == other)
    
    def __to_dict__(self):
        d = dict()
        for k in self.__dict__:
            v = self.__dict__[k]
            if isinstance(v, (str, int, float, bool)):
                d[k] = v
            elif isinstance(v, ValueObject):
                d[k] = v.__to_dict__()
            else:
                raise ValueObjectIsNotSerializable(self.__class__.__name__ + " by attribute \"" + k + "\" of type " + v.__class__.__name__)
        return d
     
    def __repr__(self):
        return f'{self.__class__.__name__}({json.dumps(self.__to_dict__())})'

class Identity(ValueObject):
    
    def __init__(self, id: str):
        self.__dict__.update(id=id)
        
    @classmethod
    def from_text(cls, id: str):
        return cls(id=id)
        
    @classmethod
    def create(cls):
        return cls(id=uuid4())
    