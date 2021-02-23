

class EventRecordManager:
    
    def session(self):
        raise NotImplementedError(f'{self.__class__.__name__} must override session method')
        
    def find(self, stream_id):
        raise NotImplementedError(f'{self.__class__.__name__} must override find method')


class Session:
    
    def append(self, event_record):
        raise NotImplementedError(f'{self.__class__.__name__} must override append method')
