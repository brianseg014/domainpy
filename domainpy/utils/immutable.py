
class Immutable:
    
    def __setattr__(self, key, value):
        raise AttributeError("attributes are read-only")
