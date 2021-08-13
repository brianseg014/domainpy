import json
import traceback
import typing


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

    def __init__(self, message: str, errors: typing.Sequence[EntryError]):
        super().__init__(message)
        self.message = message
        self.errors = errors


class IdempotencyItemError(Exception):
    pass


class PartialBatchError(Exception):
    def __init__(self, errors):
        self.errors = errors

        summary = f"{len(self.errors)} record(s) processing raise error:"
        super().__init__(
            json.dumps(
                {
                    "summary": summary,
                    "errors": [
                        {
                            "record": record,
                            "error": traceback.format_exception(
                                None, error, error.__traceback__
                            ),
                        }
                        for record, error in errors
                    ],
                }
            )
        )
