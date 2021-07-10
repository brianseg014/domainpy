
from collections import namedtuple

from domainpy.domain.model.specification import Specification


Device = namedtuple('Device', ('type', 'color'))


class CommunicationDeviceSpecification(Specification):
    pass


class PhoneSpecification(CommunicationDeviceSpecification):
    
    def is_satisfied_by(self, candidate: Device):
        return candidate.type == 'phone'


class WhiteSpecification(Specification):
    
    def is_satisfied_by(self, candidate: Device):
        return candidate.color == 'white'


def test_not():
    device = Device(type='phone', color='red')

    white_spec = WhiteSpecification()

    assert white_spec.not_().is_satisfied_by(device)
    
def test_and():
    device = Device(type='phone', color='white')

    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.and_(white_spec)

    assert some_rule_spec.is_satisfied_by(device)

def test_or():
    device = Device(type='phone', color='white')

    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.or_(white_spec)

    assert some_rule_spec.is_satisfied_by(device)

def test_remainder_unsatisfied():
    device = Device(type='computer', color='white')

    phone_spec = PhoneSpecification()
    white_spec = WhiteSpecification()

    some_rule_spec = phone_spec.and_(white_spec)

    remainder = some_rule_spec.remainder_unsatisfied_by(device)
    assert len(remainder) == 1
    assert remainder[0] == phone_spec
