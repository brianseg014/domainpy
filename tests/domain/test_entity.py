import pytest

from domainpy.domain.entity import DomainEntity
from domainpy.domain.events import DomainEvent


class Created(DomainEvent):
    id: str
    
    def __mutate__(self, _):
        return Entity(self.id)

class Updated(DomainEvent):
    another_attribute: int
    
    def __mutate__(self, entity):
        entity.another_attribute = 1


class Entity(DomainEntity):
    __createdtype__ = Created
    
    def __init__(self, id):
        super().__init__()
        self.publishes = []
        self.id = id
        self.another_attribute = 0
        
    def __publish__(self, event):
        self.publishes.append(event)
        

def test_init_params_on_create_method():
    entity = Entity.__create__(id='id')
    assert entity.id == 'id'
    

def test_apply_event_changes_state():
    entity = Entity.__create__(id='id')
    updated = Updated()
    entity.__apply__(updated)
    assert entity.another_attribute == 1


def test_apply_event_publishes():
    entity = Entity.__create__(id='id')
    updated = Updated()
    entity.__apply__(updated)
    assert len(entity.publishes) == 2
    assert entity.publishes[1] == updated