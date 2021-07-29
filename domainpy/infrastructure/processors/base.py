import abc
import typing


class Processor(abc.ABC):
    def __init__(
        self, raw_message: dict, record_handler: typing.Callable[[dict], None]
    ):
        self.raw_message = raw_message
        self.record_handler = record_handler

        self.success_messages: list = []
        self.fail_messages: list = []

    def __enter__(self):
        self.process()
        return self.success_messages, self.fail_messages

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.cleanup()

    def process(self):
        records = self.get_records()
        for record in records:
            self.process_record(record)

    def process_record(self, record):
        try:
            self.record_handler(record)
            self.success_handler(record)
        except Exception as error:  # pylint: disable=broad-except
            self.fail_handler(record, error)

    def success_handler(self, record):
        self.success_messages.append(record)

    def fail_handler(self, record, error):
        self.fail_messages.append((record, error))

    @abc.abstractmethod
    def get_records(self) -> typing.List[dict]:
        pass

    @abc.abstractmethod
    def cleanup(self):
        pass
