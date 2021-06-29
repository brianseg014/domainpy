
from domainpy.utils.bus import Bus


class MemoryBus(Bus):

    def __init__(self, publish_exceptions=[]):
        self._handlers = []
        self.publish_exceptions = tuple(publish_exceptions)

    def attach(self, handler):
        self._handlers.append(handler)

    def detach(self, handler):
        self._handlers.remove(handler)

    def publish(self, publishable):
        exceptions = []

        for handler in self._handlers:
            try:
                handler.__handle__(publishable)
            except Exception as e:
                if len(self.publish_exceptions) > 0 and isinstance(e, self.publish_exceptions):
                    exceptions.append(e)
                else:
                    raise e

        for e in exceptions:
            self.publish(e)
    