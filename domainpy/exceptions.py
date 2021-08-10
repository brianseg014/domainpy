from typing import Sequence


class DefinitionError(Exception):
    pass


class RegistryComponentNotFound(Exception):
    pass


class VersionError(Exception):
    pass


class ConcurrencyError(Exception):
    pass


class PublisherError(Exception):
    class EntryError:
        def __init__(self, message, reason: str):
            self.message = message
            self.reason = reason

    def __init__(self, message: str, errors: Sequence[EntryError]):
        super().__init__(message)
        self.message = message
        self.errors = errors


class IdempotencyItemError(Exception):
    pass


class PartialBatchError(Exception):
    def __init__(self, errors):
        self.errors = errors

        lines = [f"{len(self.errors)} record(s) processing raise error:"]
        for record, error in errors:
            lines.append(str(record) + ": " + repr(error))

        super().__init__("\n".join(lines))
