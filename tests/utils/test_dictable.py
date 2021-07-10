import pytest
from domainpy.utils.dictable import Dictable


def test_dictable_from_dict():
    class BasicDictable(Dictable):
        some_property: str

        def __init__(self, some_property: str):
            self.some_property = some_property

    x = BasicDictable.__from_dict__({
        'some_property': 'x'
    })
    assert x.some_property == 'x'
    assert isinstance(x.some_property, str)


def test_dictable_deep():
    class Level1Dictable(Dictable):
        some_property: str

        def __init__(self, some_property: str):
            self.some_property = some_property

    class Level0Dictable(Dictable):
        some_property: tuple[Level1Dictable]

        def __init__(self, some_property: tuple[Level1Dictable]):
            self.some_property = some_property

    x = Level0Dictable.__from_dict__({
        'some_property': [
            { 'some_property': 'x' }
        ]
    })
    assert isinstance(x.some_property, tuple)
    assert len(x.some_property) == 1
    assert isinstance(x.some_property[0], Level1Dictable)
    assert isinstance(x.some_property[0].some_property, str)
    assert x.some_property[0].some_property == 'x'

def test_dictable_fails():
    class Level1Dictable(Dictable):
        some_property: str

        def __init__(self, some_property: str):
            self.some_property = some_property

    class Level0Dictable(Dictable):
        some_property: Level1Dictable

        def __init__(self, some_property: Level1Dictable):
            self.some_property = some_property

    with pytest.raises(KeyError):
        x = Level0Dictable.__from_dict__({
            'some_property': { 'some_other_property': 'x' }
        })
    