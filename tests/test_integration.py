import typing

from domainpy.application import (
    ApplicationService, 
    handler, 
    ApplicationCommand, 
    IntegrationEvent
)
from domainpy.domain.model import (
    AggregateRoot, 
    mutator, 
    DomainEntity, 
    DomainEvent, 
    ValueObject, 
    Identity,
    DomainError
)
from domainpy.domain import (
    IRepository,
    IDomainService
)
from domainpy.infrastructure import (
    Mapper,
    EventStore,
    make_eventsourced_repository_adapter as make_repo_adapter,
    Transcoder
)
from domainpy.utils import (
    Registry,
    Bus,
    ApplicationBusAdapter,
    ProjectionBusAdapter, 
    PublisherBusAdapter
)
from domainpy.mock import EventSourcedEnvironmentTestAdapter
from domainpy.typing.application import SystemMessage


def test_all_system():
    ################################## Infrastructure Utils ##################################

    command_mapper = Mapper(
        transcoder=Transcoder()
    )
    integration_mapper = Mapper(
        transcoder=Transcoder()
    )
    event_mapper = Mapper(
        transcoder=Transcoder()
    )


    ################################## Domain Layer ##################################

    ## Domain Model

    ### Value Objects
    class PetStoreId(Identity):
        identity: str

    class PetStoreName(ValueObject):
        name: str

        @classmethod
        def from_text(cls, name: str):
            return PetStoreName(name)

    ### Aggregates

    #### Events
    @event_mapper.register
    class PetStoreRegistered(DomainEvent):
        __version__: int = 1
        
        pet_store_id: PetStoreId
        pet_store_name: PetStoreName

    #### Aggregate root
    class PetStore(AggregateRoot):

        @classmethod
        def create(cls, pet_store_id: PetStoreId, pet_store_name: PetStoreName) -> 'PetStore':
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

    class PetStoreRepository(IRepository[PetStore, PetStoreId]):
        pass

    ################################## Application Layer ##################################

    ## Commands
    @command_mapper.register
    class RegisterPetStore(ApplicationCommand):
        pet_store_id: str
        pet_store_name: str

    ## Hanlder
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

    ## Integrations
    @integration_mapper.register
    class CreatePetStoreSucceeded(IntegrationEvent):
        __resolve__: str = 'success'
        __error__: typing.Optional[str] = None
        __version__: int = 1

    ## Resolver
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

    ############################## Infrastructure Layer ##################################

    ## Repositories
    Adapter = make_repo_adapter(PetStore, PetStoreId)
    class EventSourcedPetStoreRepository(PetStoreRepository, Adapter):
        pass


    ################################## Environment ######################################

    class Environment(
        EventSourcedEnvironmentTestAdapter
    ):

        def setup_registry(
            self, registry: Registry, 
            event_store: EventStore, 
            setupargs: dict
        ) -> None:
            registry.put(PetStoreRepository, EventSourcedPetStoreRepository(event_store))

        def setup_projection_bus(
            self, 
            projection_bus: ProjectionBusAdapter, 
            registry: Registry, 
            setupargs: dict
        ) -> None:
            pass
        
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

    ################################## Some tests ######################################

    env = Environment(
        context='some_context',
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
    env.then.domain_events.assert_has_event_n_times(PetStoreRegistered, times=2)
    env.then.integration_events.assert_has_integration(CreatePetStoreSucceeded)