
from unittest import mock

from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.value_object import Identity
from domainpy.infrastructure.eventsourced.repository import make_adapter, SnapshotConfiguration


def test_save():
    event = mock.MagicMock()
    event_store = mock.MagicMock()
    event_store.store_events = mock.Mock()
    aggregate = mock.MagicMock()
    aggregate.__changes__ = [event]
    aggregate.take_snapshot = mock.Mock()

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(event_store)
    rep.save(aggregate)
    
    event_store.store_events.assert_called()
    aggregate.take_snapshot.assert_not_called()

def test_save_snapshot_on_n_events():
    event = mock.MagicMock()
    event_store = mock.MagicMock()
    event_store.store_events = mock.Mock()
    aggregate = mock.MagicMock()
    aggregate.__seen__ = [event]
    aggregate.__changes__ = [event]
    aggregate.take_snapshot = mock.Mock()

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(
            enabled=True,
            every_n_events=1
        )
    )
    rep.save(aggregate)

    aggregate.take_snapshot.assert_called()
    event_store.store_events.assert_called()

def test_save_snapshot_on_store_event():
    event = mock.MagicMock()
    event_store = mock.MagicMock()
    event_store.store_events = mock.Mock()
    aggregate = mock.MagicMock()
    aggregate.__seen__ = [event]
    aggregate.__changes__ = [event]
    aggregate.take_snapshot = mock.Mock()

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(
            enabled=True,
            when_store_event=event.__class__
        )
    )
    rep.save(aggregate)

    aggregate.take_snapshot.assert_called()
    event_store.store_events.assert_called()

def test_get():
    id = mock.MagicMock(spec=Identity.create())
    event = mock.MagicMock()
    event.__number__ = 1

    event_store = mock.MagicMock()
    event_store.get_events = mock.Mock(return_value=[event])

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(event_store)

    aggregate = rep.get(id)
    assert isinstance(aggregate, Aggregate)

def test_get_with_snapshot():
    id = mock.MagicMock(spec=Identity.create())
    snapshot = mock.MagicMock()
    snapshot.__number__ = 1
    event = mock.MagicMock()
    event.__number__ = 2

    def get_events(stream_id: str, **kwargs):
        if stream_id.endswith('Snapshot'):
            return [snapshot]
        else:
            return [event]

    event_store = mock.MagicMock()
    event_store.get_events = mock.Mock(side_effect=get_events)

    Aggregate = type(
        'Aggregate',
        (mock.MagicMock,),
        { }
    )
    Aggregate.create_stream_id = mock.Mock(return_value='sid')
    Aggregate.create_snapshot_stream_id = mock.Mock(return_value='sid:Snapshot')
    Aggregate.__version__ = 1
    Aggregate.__route__ = mock.Mock()

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(
        event_store, 
        snapshot_configuration=SnapshotConfiguration(enabled=True)
    )

    aggregate = rep.get(id)
    aggregate.__route__.assert_has_calls([
        mock.call(snapshot, is_snapshot=True),
        mock.call(event)
    ])