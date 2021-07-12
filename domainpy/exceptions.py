
from typing import Sequence

from domainpy.typing import SystemMessage


class DefinitionError(Exception):
    pass


class MapperNotFoundError(Exception):
    pass


class ConcurrencyError(Exception):
    pass


class PublisherError(Exception):

    class EntryError:

        def __init__(self, message: SystemMessage, reason: str):
            self.message = message
            self.reason = reason
    
    def __init__(self, message: str, errors: Sequence[EntryError]):
        self.message = message
        self.errors = errors


class IdempotencyItemError(Exception):
    pass


class PartialBatchError(Exception):
    
    def __init__(self, message, errors):
        self.message = message
        self.errors = errors
    
    
class ConfigurationError(Exception):
    pass