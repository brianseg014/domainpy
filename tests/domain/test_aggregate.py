
from domainpy.domain.aggregate import AggregateRoot
from domainpy.domain.events import DomainEvent


class Created(DomainEvent):
    
    def __mutate__(self, _):
        return Aggregate()

class Updated(DomainEvent):
    
    def __mutate__(self, _):
        pass

class Aggregate(AggregateRoot):
    __createdtype__ = Created
    

def test_aggregate_create_accumulate_changes():
    aggregate = Aggregate.__create__()
    assert len(aggregate.__changes__) == 1
    

def test_aggregate_apply_accumulate_changes():
    aggregate = Aggregate.__create__()
    updated = Updated()
    aggregate.__apply__(updated)
    assert len(aggregate.__changes__) == 2
