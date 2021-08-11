import typing

from domainpy.application import (
    ApplicationService, 
    handler, 
    ApplicationCommand, 
    IntegrationEvent,
    Projection
)
from domainpy.domain.model import (
    AggregateRoot, 
    mutator, 
    DomainEvent, 
    ValueObject, 
    Identity,
)
from domainpy.domain import (
    IRepository,
    IDomainService
)
from domainpy.infrastructure import (
    Mapper,
    EventStore,
    make_eventsourced_repository_adapter as make_repo_adapter,
    Transcoder,
    MemoryEventRecordManager,
    IPublisher,
    MemoryPublisher
)
from domainpy.utils import (
    Registry,
    Bus,
)
from domainpy.bootstrap import Environment, IFactory
from domainpy.test.bootstrap import EventSourcedProcessor, TestEnvironment
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

    ################################## Bootstrap ######################################

    class IntegrationTestFactory(IFactory):

        def __init__(self, event_store: EventStore):
            self.event_store = event_store

        def create_projection(self, key: typing.Type[Projection]) -> Projection:
            pass

        def create_repository(self, key: typing.Type[IRepository]) -> IRepository:
            if key is PetStoreRepository:
                return EventSourcedPetStoreRepository(self.event_store)

        def create_domain_service(self, key: typing.Type[IDomainService]) -> IDomainService:
            pass

        def create_event_publisher(self) -> IPublisher:
            return MemoryPublisher()

        def create_integration_publisher(self) -> IPublisher:
            return MemoryPublisher()

    event_store = EventStore(
        event_mapper=event_mapper,
        record_manager=MemoryEventRecordManager()
    )

    factory = IntegrationTestFactory(event_store)
    env = Environment('ctx', factory)
    
    env.add_repository(PetStoreRepository)

    env.add_handler(PetStoreSerivce(env.registry))

    env.add_resolver(PetStoreResolver(env.integration_bus))

    ################################## Some tests ######################################

    adap = TestEnvironment(env, EventSourcedProcessor(event_store))
    adap.given(
        adap.stamp_event(
            PetStoreRegistered, PetStore, PetStoreId.create().identity
        )(
            pet_store_id=PetStoreId.create(),
            pet_store_name=PetStoreName.from_text('noe')
        )
    )
    adap.when(
        RegisterPetStore.stamp()(
            pet_store_id='ark',
            pet_store_name='ark'
        )
    )
    adap.then.domain_events.assert_has_event_n_times(PetStoreRegistered, times=2)
    adap.then.integration_events.assert_has_integration(CreatePetStoreSucceeded)
