from domainpy.infrastructure.records import EventRecord
import pytest
import datetime
from unittest import mock

from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity
from domainpy.infrastructure.eventsourced.eventstore import EventStore
from domainpy.infrastructure.eventsourced.managers.memory import MemoryEventRecordManager
from domainpy.infrastructure.eventsourced.repository import make_adapter, SnapshotConfiguration
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.utils.bus import Bus


@pytest.fixture
def event_mapper():
    return Mapper(transcoder=Transcoder())

@pytest.fixture
def record_manager():
    return MemoryEventRecordManager()

@pytest.fixture
def bus():
    return Bus()

@pytest.fixture
def event_store(event_mapper, record_manager, bus):
    return EventStore(event_mapper, record_manager, bus)

def test_save(record_manager, event_store):
    class Aggregate(AggregateRoot):
        def proof_of_work(self):
            self.__apply__(
                self.__stamp__(DomainEvent)(
                    __trace_id__ = 'tid',
                    __context__ = 'ctx'
                )
            )

        def mutate(self, event):
            pass
        
    identity = Identity.create()
    aggregate = Aggregate(identity)
    aggregate.proof_of_work()

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(event_store)
    rep.save(aggregate)
    
    records = record_manager.get_records(
        Aggregate.create_stream_id(identity)
    )
    assert len(list(records)) == 1

def test_save_snapshot_on_n_events(record_manager, event_store):
    class Aggregate(AggregateRoot):
        def proof_of_work(self):
            self.__apply__(
                self.__stamp__(DomainEvent)(
                    __trace_id__ = 'tid',
                    __context__ = 'ctx'
                )
            )

        def mutate(self, event):
            pass

        def take_snapshot(self) -> DomainEvent:
            return DomainEvent(
                __stream_id__=self.create_snapshot_stream_id(self.__identity__),
                __number__=self.__version__ + 1,
                __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
                __trace_id__='tid',
                __context__='ctx'
            )
        
    identity = Identity.create()
    aggregate = Aggregate(identity)
    aggregate.proof_of_work()

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(
            enabled=True,
            every_n_events=1
        )
    )
    rep.save(aggregate)

    records = record_manager.get_records(
        Aggregate.create_stream_id(identity)
    )
    snapshots = record_manager.get_records(
        Aggregate.create_snapshot_stream_id(identity)
    )
    assert len(list(records)) == 1
    assert len(list(snapshots)) == 1

def test_save_snapshot_on_store_event(record_manager, event_store):
    class Aggregate(AggregateRoot):
        def proof_of_work(self):
            self.__apply__(
                self.__stamp__(DomainEvent)(
                    __trace_id__ = 'tid',
                    __context__ = 'ctx'
                )
            )

        def mutate(self, event):
            pass

        def take_snapshot(self) -> DomainEvent:
            return DomainEvent(
                __stream_id__=self.create_snapshot_stream_id(self.__identity__),
                __number__=self.__version__ + 1,
                __timestamp__=datetime.datetime.timestamp(datetime.datetime.now()),
                __trace_id__='tid',
                __context__='ctx'
            )
        
    identity = Identity.create()
    aggregate = Aggregate(identity)
    aggregate.proof_of_work()

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(
            enabled=True,
            when_store_event=DomainEvent
        )
    )
    rep.save(aggregate)

    records = record_manager.get_records(
        Aggregate.create_stream_id(identity)
    )
    snapshots = record_manager.get_records(
        Aggregate.create_snapshot_stream_id(identity)
    )
    assert len(list(records)) == 1
    assert len(list(snapshots)) == 1

def test_get(event_mapper, record_manager, event_store):
    event_mapper.register(DomainEvent)

    identity = Identity.create()

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            self.proof_of_work(event)

        def proof_of_work(self, event):
            pass

    Aggregate.proof_of_work = mock.Mock()

    with record_manager.session() as session:
        session.append(
            EventRecord(
                stream_id=Aggregate.create_stream_id(identity),
                number=1,
                topic=DomainEvent.__name__,
                version=1,
                timestamp=0.0,
                trace_id='tid',
                message='domain_event',
                context='ctx',
                payload={ }
            )
        )
        session.commit()

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(
            enabled=True,
            when_store_event=DomainEvent
        )
    )

    aggregate = rep.get(identity)
    aggregate.proof_of_work.assert_called()

def test_get_with_snapshot(event_mapper, record_manager, event_store):
    event_mapper.register(DomainEvent)

    identity = Identity.create()

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            self.proof_of_work(event)

        def proof_of_work(self, event):
            pass

    Aggregate.proof_of_work = mock.Mock()

    with record_manager.session() as session:
        session.append(
            EventRecord(
                stream_id=Aggregate.create_stream_id(identity),
                number=2,
                topic=DomainEvent.__name__,
                version=1,
                timestamp=0.0,
                trace_id='tid',
                message='domain_event',
                context='ctx',
                payload={ }
            )
        )
        session.append(
            EventRecord(
                stream_id=Aggregate.create_snapshot_stream_id(identity),
                number=1,
                topic=DomainEvent.__name__,
                version=1,
                timestamp=0.0,
                trace_id='tid',
                message='domain_event',
                context='ctx',
                payload={ }
            )
        )
        session.commit()
        
    aggregate = Aggregate(identity)

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(enabled=True)
    )

    aggregate = rep.get(identity)
    assert len(aggregate.proof_of_work.mock_calls) == 2

def test_get_with_snapshot_only_newer_events(event_mapper, record_manager, event_store):
    event_mapper.register(DomainEvent)

    identity = Identity.create()

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            self.proof_of_work(event)

        def proof_of_work(self, event):
            pass

    Aggregate.proof_of_work = mock.Mock()

    with record_manager.session() as session:
        session.append(
            EventRecord(
                stream_id=Aggregate.create_stream_id(identity),
                number=1,
                topic=DomainEvent.__name__,
                version=1,
                timestamp=0.0,
                trace_id='tid',
                message='domain_event',
                context='ctx',
                payload={ }
            )
        )
        session.append(
            EventRecord(
                stream_id=Aggregate.create_snapshot_stream_id(identity),
                number=1,
                topic=DomainEvent.__name__,
                version=1,
                timestamp=0.0,
                trace_id='tid',
                message='domain_event',
                context='ctx',
                payload={ }
            )
        )
        session.commit()
        
    aggregate = Aggregate(identity)

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(enabled=True)
    )

    aggregate = rep.get(identity)
    assert len(aggregate.proof_of_work.mock_calls) == 1
