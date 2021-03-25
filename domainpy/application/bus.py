
class Bus:

    def attach(self, handler):
        pass

    def detach(self, handler):
        pass
    
    def publish(self, publishable):
        pass


class Commutator:

    def __init__(self):
        self.buses = []

    def attach(self, bus):
        self.buses.append(bus)

    def publish(self, publishable):
        for bus in self.buses:
            bus.publish(publishable)
