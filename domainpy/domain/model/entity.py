
import uuid

class DomainEntity:
    
    def __init__(self, aggregate):
        self.__aggregate__ = aggregate
        
        self.id = uuid.uuid4()
        
    def __apply__(self, event):
        self.__aggregate__.__apply__(event)
    
    def __route__(self, event):
        self.mutate(event)
        
    def mutate(self, event):
        pass
    
    def __eq__(self, other):
        if other is None:
            return False
        
        if isinstance(other, self.__class__):
            return self.id == other.id
        elif isinstance(other, self.id.__class__):
            return self.id == other
        else:
            return False
            
    def __repr__(self):
        return f'{self.__class__.__name__}(id={self.id})'
    