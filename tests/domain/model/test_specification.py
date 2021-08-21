
from collections import namedtuple

from domainpy.domain.model.specification import Specification


Device = namedtuple('Device', ('type', 'color'))


class CommunicationDeviceSpecification(Specification):
    
    def is_satisfied_by(self, candidate: Device) -> bool:
        return hasattr(candidate, 'type')

    def is_generalization_of(self, other: Specification) -> bool:
        return issubclass(other.__class__, self.__class__)


class PhoneSpecification(CommunicationDeviceSpecification):
    
    def is_satisfied_by(self, candidate: Device):
        return candidate.type == 'phone'


class WhiteSpecification(Specification):
    
    def is_satisfied_by(self, candidate: Device):
        return candidate.color == 'white'

    def is_generalization_of(self, other: Specification) -> bool:
        return False


def test_not():
    device = Device(type='phone', color='red')

    white_spec = WhiteSpecification()

    assert white_spec.not_().is_satisfied_by(device)
    assert (-white_spec)(device)
    
def test_and():
    device = Device(type='phone', color='white')

    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.and_(white_spec)
    assert some_rule_spec.is_satisfied_by(device)

    some_rule_spec = phone_spec & white_spec
    assert some_rule_spec.is_satisfied_by(device)

def test_or():
    device = Device(type='phone', color='white')

    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.or_(white_spec)
    assert some_rule_spec.is_satisfied_by(device)

    some_rule_spec = phone_spec | white_spec
    assert some_rule_spec.is_satisfied_by(device)

def test_conjuntion_remainder():
    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    # satisfry both
    some_rule_spec = phone_spec.and_(white_spec)
    device = Device(type='phone', color='white')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == None

    # unsatisfy right
    some_rule_spec = phone_spec.and_(white_spec)
    device = Device(type='computer', color='white')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == phone_spec

    # unsatisfy left
    some_rule_spec = white_spec.and_(phone_spec)
    device = Device(type='computer', color='white')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == phone_spec

    # unsatisfy both
    some_rule_spec = white_spec.and_(phone_spec)
    device = Device(type='computer', color='red')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == some_rule_spec

def test_disjuntion_remainder():
    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.or_(white_spec)
    device = Device(type='phone', color='white')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == None

    # satisfy left
    some_rule_spec = phone_spec.or_(white_spec)
    device = Device(type='phone', color='red')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == None

    # satisfy right
    some_rule_spec = white_spec.or_(phone_spec)
    device = Device(type='phone', color='red')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == None

    # unsatisfy all
    some_rule_spec = white_spec.or_(phone_spec)
    device = Device(type='computer', color='red')
    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert remainder == some_rule_spec

def test_generalization_case():
    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.or_(white_spec)
    assert some_rule_spec.is_generalization_of(phone_spec)

    some_rule_spec = phone_spec.and_(white_spec)
    assert not some_rule_spec.is_generalization_of(phone_spec)

def test_special_case():
    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.and_(white_spec)
    assert some_rule_spec.is_special_case_of(phone_spec)

    some_rule_spec = phone_spec.or_(white_spec)
    assert not some_rule_spec.is_special_case_of(phone_spec)

    assert not phone_spec.not_().is_generalization_of(phone_spec)

def test_special_case_inheritance():
    comm_spec = CommunicationDeviceSpecification()
    phone_spec = PhoneSpecification()

    assert phone_spec.is_special_case_of(comm_spec)
    assert comm_spec.is_generalization_of(phone_spec)
