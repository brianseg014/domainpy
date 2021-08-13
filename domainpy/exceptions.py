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
        def __init__(self, message, error):
            self.message = message
            self.error = error

    def __init__(self, errors: typing.Sequence[EntryError]):
        self.errors = errors

        summary = f"{len(errors)} message(s) failed to be published"
        super().__init__(
            json.dumps(
                {
                    "message": summary,
                    "errors": [
                        {
                            "message": entry_error.message,
                            "error": traceback.format_exception(
                                None, entry_error.error, entry_error.error.__traceback__
                            ),
                        }
                        for entry_error in errors
                    ],
                }
            )
        )


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
