from typing import Type
from _pytest.config import exceptions
import pytest

from domainpy import exceptions as excs
from domainpy.domain.model.value_object import ValueObject, Identity


def test_value_object_equality():
    class BasicValueObject(ValueObject):
        some_property: str

    a = BasicValueObject(some_property='x')
    b = BasicValueObject(some_property='x')
    assert a == b

def test_value_object_inequality():
    class BasicValueObject(ValueObject):
        some_property: str

    a = BasicValueObject(some_property='x')
    b = BasicValueObject(some_property='y')
    assert a != b
    assert a != None

def test_value_object_immutability():
    class BasicValueObject(ValueObject):
        some_property: str

    x = BasicValueObject(some_property='x')

    with pytest.raises(AttributeError):
        x.some_property = 'y'

def test_identity_definition():
    class BasicIdentity(Identity):
        id: str

    x = BasicIdentity(id='id')
    assert x.id == 'id'

def test_identity_bad_definition():
    with pytest.raises(excs.DefinitionError):
        type('BasicIdentity', (Identity,), { '__annotations__': { 'id2': str } })

    with pytest.raises(excs.DefinitionError):
        type('BasicIdentity', (Identity,), { '__annotations__': { 'id': int } })

    with pytest.raises(excs.DefinitionError):
        type('BasicIdentity', (Identity,), { '__annotations__': { 'id': str, 'id2': str } })

    
    