
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import ValueObject, Identity


class ExampleValueObject(ValueObject):
    something: str
    
    
class ExampleIdentity(Identity):
    pass

class ExampleEvent(DomainEvent):
    something: ExampleValueObject


class ExampleAggregate(AggregateRoot):
    
    def __init__(self, *args, **kwargs):
        super(ExampleAggregate, self).__init__(*args, **kwargs)

        self.counter = 0
    
    def mutate(self, event):
        if(event.__class__ is ExampleEvent):
            self.mutated = True
            self.counter = self.counter + 1
    