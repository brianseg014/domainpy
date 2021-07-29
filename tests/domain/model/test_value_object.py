import pytest

from domainpy.exceptions import DefinitionError
from domainpy.domain.model.value_object import ValueObject, Identity
from domainpy.utils.data import ImmutableError


def test_value_object_equality():
    a = ValueObject(some_property='x')
    b = ValueObject(some_property='x')
    assert a == b

def test_value_object_inequality():
    a = ValueObject(some_property='x')
    b = ValueObject(some_property='y')
    assert a != b
    assert a != None

def test_value_object_immutability():
    x = ValueObject(some_property='x')

    with pytest.raises(ImmutableError):
        x.some_property = 'y'

def test_identity_definition():
    class BasicIdentity(Identity):
        id: str

    x = BasicIdentity(id='id')
    assert x.id == 'id'

def test_identity_bad_definition():
    with pytest.raises(DefinitionError):
        type('BasicIdentity', (Identity,), { '__annotations__': { 'id2': str } })

    with pytest.raises(DefinitionError):
        type('BasicIdentity', (Identity,), { '__annotations__': { 'id': int } })

    with pytest.raises(DefinitionError):
        type('BasicIdentity', (Identity,), { '__annotations__': { 'id': str, 'id2': str } })
