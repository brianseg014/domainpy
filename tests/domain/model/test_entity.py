
from unittest import mock

from domainpy.exceptions import DefinitionError
from domainpy.domain.model.entity import DomainEntity
from domainpy.domain.model.value_object import Identity


def test_entity_apply_calls_aggregate_apply():
    aggregate = mock.MagicMock()
    aggregate.__apply__ = mock.Mock()
    entity_id = mock.MagicMock()
    event = mock.MagicMock()

    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    entity = Entity(entity_id, aggregate)
    entity.__apply__(event)

    aggregate.__apply__.assert_called_with(event)

def test_entity_equality():
    aggregate = mock.MagicMock()
    entity_id = mock.MagicMock(spec=Identity.create())

    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    a = Entity(identity=entity_id, aggregate=aggregate)
    b = Entity(identity=entity_id, aggregate=aggregate)

    assert a == b
    assert a == entity_id

def test_entity_inequality():
    aggregate = mock.MagicMock()
    entity_a_id = mock.MagicMock(spec=Identity.create())
    entity_b_id = mock.MagicMock(spec=Identity.create())

    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    a = Entity(identity=entity_a_id, aggregate=aggregate)
    b = Entity(identity=entity_b_id, aggregate=aggregate)

    assert a != b
    assert a != entity_b_id
    assert a != None
    assert a != {}

def test_entity_route():
    identity = mock.MagicMock()
    aggregate = mock.MagicMock()
    event = mock.MagicMock()

    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    entity = Entity(identity, aggregate)
    entity.mutate = mock.Mock()
    entity.__route__(event)

    entity.mutate.assert_called_once_with(event)

def test_entity_stamp():
    identity = mock.MagicMock()
    aggregate = mock.MagicMock()
    aggregate.__stamp__ = mock.Mock()

    event = mock.MagicMock()

    class Entity(DomainEntity):
        def mutate(self, event):
            pass

    entity = Entity(identity, aggregate)
    entity.__stamp__(event)

    aggregate.__stamp__.assert_called()