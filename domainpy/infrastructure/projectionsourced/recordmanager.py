

class ProjectionRecordManager:
    
    def session(self):
        raise NotImplementedError(f'{self.__class__.__name__} must override session method')
        
    def get_item(self, attributes):
        raise NotImplementedError(f'{self.__class__.__name__} must override get_item method')


class Session:

    def put_item(self, item):
        raise NotImplementedError(f'{self.__class__.__name__} must override put_item method')

    def update_item(self, key, item):
        raise NotImplementedError(f'{self.__class__.__name__} must override update_item method')

    def delete_item(self, key):
        raise NotImplementedError(f'{self.__class__.__name__} must override delete_item method')