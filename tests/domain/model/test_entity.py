import pytest
from unittest import mock

from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.entity import DomainEntity
from domainpy.domain.model.event import DomainEvent
from domainpy.domain.model.value_object import Identity

@pytest.fixture
def identity():
    return Identity.create()

@pytest.fixture
def event():
    return DomainEvent(
        __stream_id__ = 'sid',
        __number__ = 1,
        __timestamp__ = 0.0,
    )

@pytest.fixture
def aggregate():
    class Aggregate(AggregateRoot):
        def mutate(self, event: DomainEvent) -> None:
            pass

    return Aggregate(Identity.create())

def test_entity_apply_calls_aggregate_apply(identity, aggregate, event):
    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    aggregate.__apply__ = mock.Mock()

    entity = Entity(identity, aggregate)
    entity.__apply__(event)

    aggregate.__apply__.assert_called_with(event)

def test_entity_equality(identity, aggregate):
    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    a = Entity(identity=identity, aggregate=aggregate)
    b = Entity(identity=identity, aggregate=aggregate)

    assert a == b
    assert a == identity

def test_entity_inequality(aggregate):
    identity_a = Identity.create()
    identity_b = Identity.create()
    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    a = Entity(identity=identity_a, aggregate=aggregate)
    b = Entity(identity=identity_b, aggregate=aggregate)

    assert a != b
    assert a != identity_b
    assert a != None
    assert a != {}

def test_entity_route(identity, aggregate, event):
    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    entity = Entity(identity, aggregate)
    entity.mutate = mock.Mock()
    entity.__route__(event)

    entity.mutate.assert_called_once_with(event)

def test_entity_stamp(identity, aggregate, event):
    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    aggregate.__stamp__ = mock.Mock()

    entity = Entity(identity, aggregate)
    entity.__stamp__(event)

    aggregate.__stamp__.assert_called()