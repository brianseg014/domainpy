
import pytest

from domainpy.utils.dictable import Dictable

class InnerDictableExample(Dictable):
    inner_id: str
    
    def __init__(self, inner_id):
        self.inner_id = inner_id


class DictableExample(Dictable):
    inner_example: InnerDictableExample
    
    def __init__(self, inner_example):
        self.inner_example = inner_example
    
    
@pytest.fixture
def dictionay():
    return { "inner_example": { "inner_id": "A" } }
    
def test_to_dict(dictionay):
    example = DictableExample(
        inner_example=InnerDictableExample(inner_id="A")     
    )
    d = example.__to_dict__()
    assert d == dictionay

def test_from_dict(dictionay):
    assert DictableExample.__from_dict__(dictionay) is not None
