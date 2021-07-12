from domainpy.exceptions import DefinitionError
import pytest
from unittest import mock

from domainpy.domain.model.value_object import Identity
from domainpy.domain.model.aggregate import AggregateRoot
from domainpy.domain.model.entity import DomainEntity
from domainpy.domain.model.event import DomainEvent


@pytest.fixture
def aggregate():
    return AggregateRoot(id=Identity.create())

def test_entity_apply_calls_aggregate_apply(aggregate):
    aggregate.__apply__ = mock.Mock()

    event = DomainEvent()

    entity = DomainEntity(id=Identity.create(), aggregate=aggregate)
    entity.__apply__(event)

    aggregate.__apply__.assert_called_with(event)

def test_entity_equality(aggregate):
    id = Identity.create()
    a = DomainEntity(id=id, aggregate=aggregate)
    b = DomainEntity(id=id, aggregate=aggregate)

    assert a == b
    assert a == id

def test_entity_inequality(aggregate):
    id_a = Identity.create()
    a = DomainEntity(id=id_a, aggregate=aggregate)

    id_b = Identity.create()
    b = DomainEntity(id=id_b, aggregate=aggregate)

    assert a != b
    assert a != id_b
    assert a != None

def test_entity_equality_failes(aggregate):
    id = Identity.create()
    a = DomainEntity(id=id, aggregate=aggregate)

    with pytest.raises(DefinitionError):
        a == {}
