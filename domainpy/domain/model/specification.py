from __future__ import annotations

import abc
import typing


class Specification(abc.ABC):
    @abc.abstractmethod
    def is_satisfied_by(self, candidate: typing.Any) -> bool:
        pass  # pragma: no cover

    def and_(self, other: Specification) -> ConjunctionSpecification:
        return ConjunctionSpecification(self, other)

    def or_(self, other: Specification) -> DisjunctionSpecification:
        return DisjunctionSpecification(self, other)

    def not_(self):
        return NegationSpecification(self)

    def is_special_case_of(self, other: Specification) -> bool:
        return other.is_generalization_of(self)

    @abc.abstractmethod
    def is_generalization_of(self, other: Specification) -> bool:
        pass

    def remainder_unsatisfied_by(
        self, candidate: typing.Any
    ) -> typing.Optional[Specification]:
        if not self.is_satisfied_by(candidate):
            return self

        return None

    def __call__(self, candiate: typing.Any):
        return self.is_satisfied_by(candiate)

    def __and__(self, other: Specification) -> ConjunctionSpecification:
        return self.and_(other)

    def __or__(self, other: Specification) -> DisjunctionSpecification:
        return self.or_(other)

    def __neg__(self) -> NegationSpecification:
        return self.not_()


class CompositeSpecification(Specification):
    def __init__(self, left: Specification, right: Specification):
        self.left = left
        self.right = right


class ConjunctionSpecification(CompositeSpecification):
    def is_satisfied_by(self, candidate: typing.Any) -> bool:
        return self.left.is_satisfied_by(
            candidate
        ) and self.right.is_satisfied_by(candidate)

    def remainder_unsatisfied_by(
        self, candidate: typing.Any
    ) -> typing.Optional[Specification]:
        left_remainder = self.left.remainder_unsatisfied_by(candidate)
        right_remainder = self.right.remainder_unsatisfied_by(candidate)

        if left_remainder is not None and right_remainder is not None:
            return self

        if left_remainder is not None:
            return left_remainder

        if right_remainder is not None:
            return right_remainder

        return None

    def is_special_case_of(self, other: Specification) -> bool:
        return other in (self.left, self.right)

    def is_generalization_of(self, other: Specification) -> bool:
        return False


class DisjunctionSpecification(CompositeSpecification):
    def is_satisfied_by(self, candidate: typing.Any) -> bool:
        return self.left.is_satisfied_by(
            candidate
        ) or self.right.is_satisfied_by(candidate)

    def remainder_unsatisfied_by(
        self, candidate: typing.Any
    ) -> typing.Optional[Specification]:
        left_remainder = self.left.remainder_unsatisfied_by(candidate)
        right_remainder = self.right.remainder_unsatisfied_by(candidate)

        if left_remainder is None:
            return None

        if right_remainder is None:
            return None

        return self

    def is_special_case_of(self, other: Specification) -> bool:
        return False

    def is_generalization_of(self, other: Specification) -> bool:
        return other in (self.left, self.right)


class NegationSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, candidate):
        return not self.spec.is_satisfied_by(candidate)

    def is_generalization_of(self, other: Specification) -> bool:
        return False

    def __repr__(self):
        return object.__repr__(self) + " of " + repr(self.spec)
