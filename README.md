# Domainpy - A library for DDD, ES, CQRS and microservices

## Install

To install the library

```console
$ pip install domainpy
```

## Quickstart

Domainpy is a library to implement the ideas around domain driven design,
cqrs and event sourcing in python.

The library follows clean architecture principle with three main layers:
application, domain and infrastructure.

## Let's see some code

We start by defining some business objects.

### Value Objecs

`Value Objects` are concepts that belongs to the ubiquitous language of 
the business. This objects are identified by its own attributes. Examples of
value objects are identities, names, dates, prices or addresses.  Immutables, 
if you need to change some attribute, you should generate a new instace. 
They can only hold primatives or other value objects. And you should try to 
have semantic constructors.

```python
from domainpy.domain.model import ValueObject, Identity

class PetStoreId(Identity):
        id: str

class PetStoreName(ValueObject):
    name: str

    @classmethod
    def from_text(cls, name: str):
        return PetStoreName(name)
```

### Domain events

An event decribe something that already happened as fact.
We should write event names in past tense. Also, is a concept that belongs to
the ubiquitous language of the business. An event can only happen once, and if
the same thing happens again later, then it is a different event. And of course,
the are immutable as we cannot change the history.

```python
from domainpy.domain.model import DomainEvent

class PetStoreRegistered(DomainEvent):
    __version__: int = 1
    
    pet_store_id: PetStoreId
    pet_store_name: PetStoreName
```

### Aggregate

`Aggregate` is an encapsulation of domain objects (`entities` and
`value objects`) which should be stored atomically. It's also known as
transactional boundry (all within should be save or none).

**Domain Entity** is the absctraction of something that changes in
time and has its own identity. This example does not contains one.

```python
from domainpy.domain.model import AggregateRoot, mutator

class PetStore(AggregateRoot):

        @classmethod
        def create(
            cls, 
            pet_store_id: PetStoreId, 
            pet_store_name: PetStoreName
        ) -> 'PetStore':

            pet_store = PetStore(pet_store_id)
            pet_store.__apply__(
                pet_store.__stamp__(PetStoreRegistered)(
                    pet_store_id=pet_store_id,
                    pet_store_name=pet_store_name
                )
            )
            return pet_store

        @mutator
        def mutate(self, message: DomainEvent) -> None:
            pass

        @mutate.event(PetStoreRegistered)
        def _(self, e: PetStoreRegistered):
            self.pet_store_id = e.pet_store_id
            self.pet_store_name = e.pet_store_name
```

An `aggregate` creates `domain events` and apply to itself, which is handled
by `mutate` method, changing the state of the aggregate. The state of the 
`aggregate` exists with sole purpose of enforce business invariants (business 
rules).

### Repository

Repository is an interface to represent the store of an aggregate.
IRepository contains the methods get and save.

```python
from domainpy.domain import IRepository

class PetStoreRepository(IRepository[PetStore, PetStoreId]):
        pass
```

Every time a repository creates an aggregate, all events are loaded and
replayed in the aggregate, handled by aggregate mutate method.

### Application Command

Describes the intention of change the system. This intention can be 
fulfilled or rejected by the domain.

```python
from domainpy.application import ApplicationCommand

class RegisterPetStore(ApplicationCommand):
    pet_store_id: str
    pet_store_name: str
```

### Application Service (Handler)

Conducts a command to appropiate aggregate in the domain layer. Also,
is the responsable to call save in a domain repository.

```python
from domainpy.application import ApplicationSerivce, handler
from domainpy.utils import Registry
from domainpy.typing import SystemMessage

class PetStoreSerivce(ApplicationService):

        def __init__(self, registry: Registry):
            self.pet_store_repository = registry.get(PetStoreRepository)

        @handler
        def handle(self, message: SystemMessage) -> None:
            pass

        @handle.command(RegisterPetStore)
        def _(self, c: RegisterPetStore) -> None:
            pet_store = PetStore.create(
                pet_store_id=PetStoreId.from_text(c.pet_store_id),
                pet_store_name=PetStoreName.from_text(c.pet_store_name)
            )
            self.pet_store_repository.save(pet_store)
```

### Integration Events

Domain events live in a bounded context (microservice) and should not perm
into another bounded context avoiding coupling. Integration events are used
as messages with low level of detail, just for another microservice knows if
everything is ok or something fails.

```python
from domainpy.application import IntegrationEvent

class CreatePetStoreSucceeded(IntegrationEvent):
    __resolve__: str = 'success'
    __error__: typing.Optional[str] = None
    __version__: int = 1

```

### Application Service (Resolvers)

Another application service (just as a handler) but the semantic function
of listening system messages and publish an integration message for other
bounded contexts.

```python
from domainpy.application import ApplicationService, handler

class PetStoreResolver(ApplicationService):

        def __init__(self, integration_bus: Bus[IntegrationEvent]):
            self.integration_bus = integration_bus

        @handler
        def handle(self, message: SystemMessage):
            pass

        @handle.trace(RegisterPetStore, PetStoreRegistered)
        def _(self, c: RegisterPetStore, e: PetStoreRegistered):
            self.integration_bus.publish(
                CreatePetStoreSucceeded(
                    __timestamp__=0.0
                )
            )
```

### Implmentation of repository in infrastructure

The library provides a function to create an adaptar for a event sourced
repository, which implements the methods get and save.

```python
from domainpy.infrastructure import (
    make_eventsourced_repository_adapter as make_repo_adapter
)

Adapter = make_repo_adapter(PetStore, PetStoreId)
class EventSourcedPetStoreRepository(PetStoreRepository, Adapter):
    pass
```

### Environment

Putting all togheter. An EventSourcedEnvionment creates internally some
buses which will transport system messages and an event store which stores
and retreives events from a record manager such as dynamodb.

`Projection Bus` distrubite domain events to projections subscibed.

`Resolver Bus` distribute all system messages to application services
with semantic role of resolvers.

`Handler Bus` distribute all system messages to application services
with semantic role of handlers.

`Domain Publisher Bus` all domain events to be published in an infrastructure
bus such as aws event bridge.

`Integration Publisher Bus` all integration events to be publisher in an
infrastructure bus such as aws event bridge.

```python
from domainpy.environments import EventSourcedEnvironment

class Environment(
        EventSourcedEnvironment
    ):

        def setup_registry(
            self, registry: Registry, 
            event_store: EventStore, 
            setupargs: dict
        ) -> None:
            registry.put(
                PetStoreRepository, 
                EventSourcedPetStoreRepository(event_store)
            )
        
        def setup_resolver_bus(
            self, 
            resolver_bus: ApplicationBusAdapter, 
            publisher_integration_bus: Bus[DomainEvent], 
            setupargs: dict
        ) -> None:
            resolver_bus.attach(
                PetStoreResolver(publisher_integration_bus)
            )

        def setup_handler_bus(
            self, 
            handler_bus: ApplicationBusAdapter, 
            registry: Registry, 
            setupargs: dict
        ) -> None:
            handler_bus.attach(
                PetStoreSerivce(registry)
            )
```

### One last thing, an utility (Mapper)

As you me guess, all system messages (command, integration event and domain
event) will need to be serialized in exposed in the infrastructure. There is a 
built-in system.

```python
from domainpy.infrastructure import (
    Mapper
    BuiltinCommandTranscoder, 
    BuiltinIntegrationTranscoder,
    BuiltinEventTranscoder
)

command_mapper = Mapper(
    transcoder=BuiltinCommandTranscoder()
)
integration_mapper = Mapper(
    transcoder=BuiltinIntegrationTranscoder('context')
)
event_mapper = Mapper(
    transcoder=BuiltinEventTranscoder('context')
)
...
```

Context referes to a name that identifies the current bounded context 
(microservice) that will be added to all events on its way to the
infrastructure.

Now, you just need to add a decorator to add a auto-serializer-deserializer
support.

```python
...

@command_mapper.register
class RegisterPetStore(ApplicationCommand):
    pet_store_id: str
    pet_store_name: str

@integration_mapper.register
class CreatePetStoreSucceeded(IntegrationEvent):
    __resolve__: str = 'success'
    __error__: typing.Optional[str] = None
    __version__: int = 1

@event_mapper.register
class PetStoreRegistered(DomainEvent):
    pet_store_id: PetStoreId
    pet_store_name: PetStoreName
```

Mapper has serialize and deserlize method you need. We are not
using mapper in this example as I'm not definig infrastructure.

### Finally

How do we use all this?

```python
env = Environment(
    command_mapper=command_mapper,
    integration_mapper=integration_mapper,
    event_mapper=event_mapper
)
env.handle(
    env.stamp(RegisterPetStore)(
        pet_store_id='pet_store_id',
        pet_store_name='noe'
    )
)
```

`stamp` method is used to add some meta information, so
you don't have to add it.

### Testing

For testing we need to create a new environment with an adapter.
This will enable some useful methods: given, when then

```python
class TestingEnvrionment(
    Environment,
    EventSourcedEnvironmentTestAdapter
):
    pass

env = TestingEnvrionment(
    command_mapper=command_mapper,
    integration_mapper=integration_mapper,
    event_mapper=event_mapper
)
env.given(
    env.stamp_event(PetStoreRegistered, PetStore)(
        pet_store_id=PetStoreId.create(),
        pet_store_name=PetStoreName.from_text('noe')
    )
)
env.when(
    env.stamp_command(RegisterPetStore)(
        pet_store_id='ark',
        pet_store_name='ark'
    )
)
env.then.domain_events.assert_has_event_n(PetStoreRegistered, n=2)
env.then.integration_events.assert_has_integration(CreatePetStoreSucceeded)
```

This example can be found in tests/test_integration.py