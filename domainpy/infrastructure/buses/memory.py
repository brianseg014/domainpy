
from domainpy.application.bus import Bus


class MemoryBus(Bus):

    def __init__(self):
        self._handlers = []

    def attach(self, handler):
        self._handlers.append(handler)

    def detach(self, handler):
        self._handlers.remove(handler)

    def publish(self, publishable):
        for handler in self._handlers:
            handler.__handle__(publishable)
    