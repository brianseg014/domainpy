import pytest

from domainpy.utils.constructable import Constructable


def test_constructable():
    class BasicConstructable(Constructable):
        some_property: str
        some_other_property: int

    x = BasicConstructable(some_property='x', some_other_property=1)
    
    assert x.some_property == 'x'
    assert isinstance(x.some_property, str)

    assert x.some_other_property == 1
    assert isinstance(x.some_other_property, int)

def test_fail_on_mismatch_type():
    class BasicConstructable(Constructable):
        some_property: str

    with pytest.raises(TypeError):
        x = BasicConstructable(some_property=1)

def test_constructable_with_kwargs():
    class BasicConstructable(Constructable):
        some_property: str

    x = BasicConstructable(some_property='x', some_other_property=1)
    assert x.some_other_property == 1

def test_constructable_with_custom_type():
    class CustomType(Constructable):
        some_property: str

    class BasicConstructable(Constructable):
        some_property: CustomType

    x = BasicConstructable(
        some_property=CustomType(some_property='x')
    )