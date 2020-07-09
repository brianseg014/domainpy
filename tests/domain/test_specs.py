import pytest

from domainpy.domain.specifications import Specification, satisfies


class ZeroSpecification(Specification):
    
    def __satisfiedby__(self, agg):
        return agg.val == 0
    

class OneSpecification(Specification):
    
    def __satisfiedby__(self, agg):
        return agg.val == 1


class GreaterThanOne(Specification):
    
    def __satisfiedby__(self, agg):
        return agg.val > 1
        
class LowerThanFive(Specification):

    def __satisfiedby__(self, agg):
        return agg.val < 5

class Aggregate:
    
    def __init__(self, val):
        self.val = val
        self.executed = None
    
    @satisfies(ZeroSpecification())
    def zero(self):
        self.executed = 'zero'
    
    @satisfies(OneSpecification())
    def one(self):
        self.executed = 'one'
        
    @satisfies(GreaterThanOne() & LowerThanFive())
    def greater_than_one_and_lower_than_faive(self):
        self.executed = 'greater_than_one_and_lower_than_faive'
        
    @satisfies(ZeroSpecification() | OneSpecification())
    def zero_or_one(self):
        self.executed = 'zero_or_one'


def test_specification_satisfied():
    agg = Aggregate(0)
    agg.zero()
    assert agg.executed == 'zero'

def test_specification_unsatisfied():
    agg = Aggregate(0)
    agg.one()
    assert agg.executed is None

def test_specification_and_operator_satisfied():
    agg = Aggregate(3)
    agg.greater_than_one_and_lower_than_faive()
    assert agg.executed == 'greater_than_one_and_lower_than_faive'
    
def test_specification_and_operator_unsatisfied():
    agg = Aggregate(0)
    agg.greater_than_one_and_lower_than_faive()
    assert agg.executed is None
    
def test_specification_or_operator_left_satisfied():
    agg = Aggregate(0)
    agg.zero_or_one()
    assert agg.executed == 'zero_or_one'
    
def test_specification_or_operator_right_satisfied():
    agg = Aggregate(1)
    agg.zero_or_one()
    assert agg.executed == 'zero_or_one'

def test_specification_or_operator_unsatisfied():
    agg = Aggregate(2)
    agg.zero_or_one()
    assert agg.executed is None
