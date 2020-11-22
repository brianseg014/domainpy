
from typing import Callable

from domainpy.application.command import ApplicationCommand

class ApplicationService:
    
    def __handle__(self, handable):
        self.handle(handable)
        
    def handle(self, handable):
        pass
    

    