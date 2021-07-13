import typing


class IdempotencyRecordManager:

    def store_in_progress(self, record: dict):
        pass # pragma: no cover

    def store_success(self, record: dict):
        pass # pragma: no cover

    def store_failure(self, record: dict, exc: typing.Type[Exception]):
        pass # pragma: no cover
    