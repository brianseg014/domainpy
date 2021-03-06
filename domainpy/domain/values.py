import json


class ValueObject:
    
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
        self.__validate__()
        
    def __validate__(self):
        pass
    
    def __setattr__(self, key, value):
        raise AttributeError("DomainEvent attributes are read-only")
        
    def __hash__(self):
        return hash(json.dumps(self.__dict__, sort_keys=True))
        
    def __eq__(self, other):
        if other is None:
            return False
        
        return isinstance(other, ValueObject) and self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not (self == other)
