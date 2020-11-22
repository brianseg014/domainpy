
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import ValueObject


class ExampleValueObject(ValueObject):
    something: str


class ExampleEvent(DomainEvent):
    something: ExampleValueObject


class ExampleAggregate(AggregateRoot):
    
    def __init__(self, *args, **kwargs):
        super(ExampleAggregate, self).__init__(*args, **kwargs)
    
    def mutate(self, event):
        if(event.__class__ is ExampleEvent):
            self.mutated = True
    
    