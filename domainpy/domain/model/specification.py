
from typing import Any


class Specification:
    
    def is_satisfied_by(self, candidate: Any):
        pass

    def and_(self, other: 'Specification') -> 'ConjunctionSpecification':
        return ConjunctionSpecification(self, other)

    def or_(self, other: 'Specification') -> 'DisjunctionSpecification':
        return DisjunctionSpecification(self, other)

    def not_(self):
        return NegationSpecification(self)

    def is_special_case_of(self, other: 'Specification') -> 'bool':
        raise NotImplementedError(f'{self.__class__} should override is_special_case_of')

    def is_generalization_of(self, other: 'Specification') -> 'bool':
        raise NotImplementedError(f'{self.__class__} should override is_generalization_of')

    def remainder_unsatisfied_by(self, candidate: Any):
        if not self.is_satisfied_by(candidate):
            return [self]
        else:
            return []

    def __call__(self, candiate: Any):
        return self.is_satisfied_by(candiate)

    def __and__(self, other: 'Specification') -> 'ConjunctionSpecification':
        return self.and_(other)

    def __or__(self, other: 'Specification') -> 'DisjunctionSpecification':
        return self.or_(other)

    def __neg__(self, other: 'Specification') -> 'NegationSpecification':
        return self.not_(other)


class CompositeSpecification(Specification):
    
    def __init__(self, a: Specification, b: Specification):
        self.a = a
        self.b = b

    def remainder_unsatisfied_by(self, candidate: Any):
        remainder = []

        a_remainder = self.a.remainder_unsatisfied_by(candidate)
        remainder.extend(a_remainder)

        b_remainder = self.b.remainder_unsatisfied_by(candidate)
        remainder.extend(b_remainder)

        return remainder
        

class ConjunctionSpecification(CompositeSpecification):
    
    def is_satisfied_by(self, candidate):
        return (
            self.a.is_satisfied_by(candidate) 
            and self.b.is_satisfied_by(candidate)
        )

    def is_special_case_of(self, other: Specification):
        return (
            self.a.is_special_case_of(other)
            or self.b.is_special_case_of(other)
        )


class DisjunctionSpecification(CompositeSpecification):
    
    def is_satisfied_by(self, candidate):
        return (
            self.a.is_satisfied_by(candidate) 
            or self.b.is_satisfied_by(candidate)
        )

    def is_generalization_of(self, other: Specification):
        return (
            self.a.is_generalization_of(other)
            or self.b.is_generalization_of(other)
        )


class NegationSpecification(Specification):

    def __init__(self, spec: Specification):
        self.spec = spec
    
    def is_satisfied_by(self, candidate):
        return not self.spec.is_satisfied_by(candidate)

    def __repr__(self):
        return object.__repr__(self) + ' of ' + repr(self.spec)