import pytest

from domainpy.utils.constructable import Constructable

class ConstructableExample(Constructable):
    id: str

def test_constructable():
    assert ConstructableExample(id="A").id == "A"
    assert ConstructableExample("A").id == "A"
