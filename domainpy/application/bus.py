
class Bus:
    
    def __init__(self):
        self._services = set()
    
    def register_service(self, service):
        self._services.add(service)
    
    def handle(self, handable):
        for s in self._services:
            s.__handle__(handable)
    