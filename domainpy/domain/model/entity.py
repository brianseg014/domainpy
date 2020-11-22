
class DomainEntity:
    
    def __route__(self, event):
        self.mutate(event)
        
    def mutate(self, event):
        pass
    
