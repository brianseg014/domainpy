
from unittest import mock

from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.value_object import Identity
from domainpy.infrastructure.eventsourced.repository import make_adapter


def test_save():
    event = mock.MagicMock()
    event_store = mock.MagicMock()
    aggregate = mock.MagicMock()
    aggregate.__changes__ = [event]

    class Aggregate(AggregateRoot):
        def mutate(self, event):
            pass

    EventSourcedRpository = make_adapter(Aggregate, Identity)
    rep = EventSourcedRpository(event_store)
    rep.save(aggregate)
    
    event_store.store_events.assert_called_with([event])

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
    