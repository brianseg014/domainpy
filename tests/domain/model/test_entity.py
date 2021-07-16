
import pytest
from unittest import mock

from domainpy.exceptions import DefinitionError
from domainpy.domain.model.entity import DomainEntity
from domainpy.domain.model.value_object import Identity


def test_entity_apply_calls_aggregate_apply():
    aggregate = mock.MagicMock()
    aggregate.__apply__ = mock.Mock()
    entity_id = mock.MagicMock()
    event = mock.MagicMock()

    entity = DomainEntity(entity_id, aggregate)
    entity.__apply__(event)

    aggregate.__apply__.assert_called_with(event)

def test_entity_equality():
    aggregate = mock.MagicMock()
    entity_id = mock.MagicMock(spec=Identity.create())

    a = DomainEntity(id=entity_id, aggregate=aggregate)
    b = DomainEntity(id=entity_id, aggregate=aggregate)

    assert a == b
    assert a == entity_id

def test_entity_inequality():
    aggregate = mock.MagicMock()
    entity_a_id = mock.MagicMock(spec=Identity.create())
    entity_b_id = mock.MagicMock(spec=Identity.create())

    a = DomainEntity(id=entity_a_id, aggregate=aggregate)
    b = DomainEntity(id=entity_b_id, aggregate=aggregate)

    assert a != b
    assert a != entity_b_id
    assert a != None

def test_entity_equality_failes():
    aggregate = mock.MagicMock()
    entity_id = mock.MagicMock(spec=Identity.create())

    x = DomainEntity(id=entity_id, aggregate=aggregate)
    
    with pytest.raises(DefinitionError):
        x == {}
