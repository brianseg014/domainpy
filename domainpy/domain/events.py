import json

mutators = {}


class DomainEvent:
    
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
    
    def __mutate__(self, entity):
        handler = mutators.get(self.__class__)
        
        if handler is None:
            raise Exception("DomainEvent no mutator found for event {}".format(
                    self.__class__
                ))
        
        handler(entity, self)
    
    def __setattr__(self, key, value):
        raise AttributeError("DomainEvent attributes are read-only")

    def __hash__(self):
        return hash(json.dumps(self.__dict__, sort_keys=True))
        
    def __eq__(self, other):
        if other is None:
            return False
        
        return isinstance(other, DomainEvent) and self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not (self == other)


def mutatorfor(event: DomainEvent):
    if not event:
        raise TypeError("event type is required")
    
    if event in mutators:
        raise Exception("DomainEvent single mutator should be defined")
    
    def inner_function(func):
        mutators[event] = func
        
        def wrappper(*args, **kwargs):
            func(*args, **kwargs)
            
        return wrappper
        
    return inner_function
