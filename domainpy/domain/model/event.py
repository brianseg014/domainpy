import time
from datetime import datetime, date

from domainpy.domain.model.value_object import ValueObject
from domainpy.domain.model.exceptions import EventParameterIsNotValueObjectError
from domainpy.utils.constructable import Constructable
from domainpy.utils.immutable import Immutable

class DomainEvent(Constructable, Immutable):
    pass
