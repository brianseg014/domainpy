

class Specification:
    
    def is_satisfied_by(self, candidate):
        pass

    def and_(self, other):
        return ConjunctionSpecification(
            self,
            other
        )

    def or_(self, other):
        return DisjunctionSpecification(
            self,
            other
        )

    def not_(self):
        return NegationSpecification(self)

    def is_special_case_of(self, other):
        raise NotImplementedError(f'{self.__class__} should override is_special_case_of')

    def is_generalization_of(self, other):
        raise NotImplementedError(f'{self.__class__} should override is_generalization_of')

    def remainder_unsatisfied_by(self, candidate):
        if not self.is_satisfied_by(candidate):
            return self.__class__
        else:
            return None


class CompositeSpecification(Specification):
    
    def __init__(self, a: Specification, b: Specification):
        self.a = a
        self.b = b


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
