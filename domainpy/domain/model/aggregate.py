
class AggregateRoot:
    
    def __init__(self):
        self.__changes__ = []
    
    def __apply__(self, event):
        self.mutate(event)
        self.__changes__.append(event)
    
    def mutate(self, event):
        pass
    
