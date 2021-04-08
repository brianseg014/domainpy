
from .command import ApplicationCommand
from .integration import IntegrationEvent

class tracer:

    def __call__(self, func):
        def wrapper(service, message):

            if isinstance(message, (ApplicationCommand, IntegrationEvent)):
                self.trace = [(service, message)]
            else:
                self.trace.append((service, message))

            return func(service, message)
        return wrapper

    def inject(self, func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs, trace=self.trace)

        return wrapper
