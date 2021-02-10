
import pytest
from typing import Tuple

from domainpy.utils.dictable import Dictable

class InnerDictableExample(Dictable):
    inner_id: str
    
    def __init__(self, inner_id):
        self.inner_id = inner_id


class DictableExample(Dictable):
    inner_examples: Tuple[InnerDictableExample]
    
    def __init__(self, inner_examples):
        self.inner_examples = inner_examples

    
@pytest.fixture
def dictionay():
    return {'inner_examples': ({'inner_id': 'A'}, {'inner_id': 'B'})}
    
def test_to_dict(dictionay):
    example = DictableExample(
        inner_examples=tuple([
            InnerDictableExample(inner_id="A"),
            InnerDictableExample(inner_id="B")
        ])
    )
    d = example.__to_dict__()
    assert d == dictionay

def test_from_dict(dictionay):
    assert DictableExample.__from_dict__(dictionay) is not None
