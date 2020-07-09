import pytest

from domainpy.domain.values import ValueObject


class Quantity(ValueObject):
    quantity: int
    
    def __validate__(self):
        if self.quantity < 0:
            raise ValueError("Quantity must be greater than zero")
            
            
def test_value_object_generates_constructor():
    q = Quantity(quantity=1)
    assert q
    assert q.quantity == 1
    
    
def test_value_object_execute_validate():
    with pytest.raises(ValueError):
        Quantity(quantity=-1)
        

def test_value_object_immutable():
    with pytest.raises(AttributeError):
        q = Quantity(quantity=1)
        q.quantity = 2

        
def test_value_object_equality():
    q1 = Quantity(quantity=1)
    q2 = Quantity(quantity=1)
    assert q1 == q2
    
    
def test_value_object_inequality():
    q1 = Quantity(quantity=1)
    q2 = Quantity(quantity=2)
    assert not (q1 == q2)
