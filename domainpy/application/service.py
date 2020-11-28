
from typing import Callable

from domainpy.application.command import ApplicationCommand

class ApplicationService:
    
    def __handle__(self, msg):
        self.handle(msg)
        
    def handle(self, msg):
        pass
    

    