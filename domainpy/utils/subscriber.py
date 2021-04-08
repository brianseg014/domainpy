
class Subscriber(list):
    
    def __handle__(self, publishable):
        self.append(publishable)
    
    