
class Immutable:
    
    def __setattr__(self, key, value):
        raise AttributeError("DomainEvent attributes are read-only")
