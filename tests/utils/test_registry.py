
import pytest

from domainpy.utils.registry import Registry


def test_registry():
    SomeType = type('SomeType', (), {})
    some_instance = SomeType()

    r = Registry()
    r.put(SomeType, some_instance)

    assert r.has(SomeType)
    assert r.get(SomeType) == some_instance

def test_registry_fails():
    SomeType = type('SomeType', (), {})

    r = Registry()

    assert not r.has(SomeType)
    with pytest.raises(AssertionError):
        r.assert_component(SomeType)
    