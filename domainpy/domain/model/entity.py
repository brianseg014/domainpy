
class DomainEntity:
    
    def __init__(self, aggregate):
        self.__aggregate__ = aggregate
        
    def __apply__(self, event):
        self.__aggregate__.__apply__(event)
    
    def __route__(self, event):
        self.mutate(event)
        
    def mutate(self, event):
        pass
    
