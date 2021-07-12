

class Processor:

    def __init__(self, **kwargs):
        self.success_messages: list = []
        self.fail_messages: list = []

    def __call__(self, raw_message: dict, record_handler):
        self.raw_message = raw_message
        self.record_handler = record_handler
        return self

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
        except Exception as e:
            self.fail_handler(record, e)

    def success_handler(self, record):
        self.success_messages.append(record)

    def fail_handler(self, record, error):
        self.fail_messages.append((record, error))

    def get_records(self):
        pass

    def cleanup(self):
        pass


class BasicProcessor(Processor):

    def get_records(self):
        return [self.raw_message]
    