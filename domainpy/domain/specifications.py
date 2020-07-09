
from functools import wraps
from dataclasses import dataclass


def satisfies(spec):
    def inner_method(func):
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if spec.__satisfiedby__(self):
                func(self, *args, **kwargs)
        return wrapper
    return inner_method
            

class Specification:
    
    def __satisfiedby__(self, candidate):
        pass

    def __and__(self, other):
        return AndSpecification(self, other)
        
    def __or__(self, other):
        return OrSpecification(self, other)
        
    def __neg__(self):
        return NotSpecification(self)
        
        
@dataclass(frozen=True)
class AndSpecification(Specification):
    left: Specification
    right: Specification
    
    def __satisfiedby__(self, candidate):
        return (
            self.left.__satisfiedby__(candidate) 
            and self.right.__satisfiedby__(candidate)
        )
        
        
@dataclass(frozen=True)
class OrSpecification(Specification):
    left: Specification
    right: Specification
    
    def __satisfiedby__(self, candidate):
        return (
            self.left.__satisfiedby__(candidate) 
            or self.right.__satisfiedby__(candidate)
        )

@dataclass(frozen=True)
class NotSpecification(Specification):
    subject: Specification
    
    def __satisfiedby__(self, candidate):
        return not self.subject.__satisfiedby__(candidate)
