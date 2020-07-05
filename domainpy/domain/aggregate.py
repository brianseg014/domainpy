
from domainpy.domain.entity import DomainEntity


class AggregateRoot(DomainEntity):
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.__changes__ = []
        
    def __publish__(self, event):
        self.__changes__.append(event)
