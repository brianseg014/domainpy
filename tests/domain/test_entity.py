import pytest

from domainpy.domain.entity import (
    DomainEntity, 
    usecreated
)
from domainpy.domain.events import DomainEvent, mutatorfor


class Created(DomainEvent):
    id: str
    
    def __mutate__(self, _):
        return Entity(self.id)

class Updated(DomainEvent):
    another_attribute: int
    
    def __mutate__(self, entity):
        entity.another_attribute = 1


class Entity(DomainEntity):

    def __init__(self, id):
        super().__init__()
        self.publishes = []
        self.id = id
        self.another_attribute = 0
        
    def __publish__(self, event):
        self.publishes.append(event)
        

class DecoratedUpdated(DomainEvent):
    another_attribute: int
    
    
@usecreated(Created)
class DecoratedEntity(DomainEntity):
    
    def __init__(self, id):
        super().__init__()
        self.publishes = []
        self.id = id
        self.another_attribute = 0
        
    def __publish__(self, event):
        self.publishes.append(event)
        
    @mutatorfor(DecoratedUpdated)
    def update(self, event: DecoratedUpdated):
        self.another_attribute = event.another_attribute


def test_init_params_on_create_method():
    entity = Entity.__create__(Created(id='id'))
    assert entity.id == 'id'
    assert len(entity.publishes) == 1
    

def test_create_method_with_decorator():
    entity = DecoratedEntity.__create__(Created(id='id'))
    assert entity.id == 'id'
    assert len(entity.publishes) == 1
    

def test_apply_event_changes_state():
    entity = Entity.__create__(Created(id='id'))
    updated = Updated()
    entity.__apply__(updated)
    assert entity.another_attribute == 1
    

def test_apply_event_publishes():
    entity = Entity.__create__(Created(id='id'))
    updated = Updated()
    entity.__apply__(updated)
    assert len(entity.publishes) == 2
    assert entity.publishes[1] == updated
