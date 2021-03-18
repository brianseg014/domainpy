from collections import namedtuple
from domainpy.infrastructure.projectionsourced.recordmanager import (
    ProjectionRecordManager,
    Session
)

Operation = namedtuple('Operation', ('type', 'key', 'item'))

class MemoryProjectionRecordManager(ProjectionRecordManager):
    
    def __init__(self):
        self._heap = []
        
    def session(self):
         return MemorySession(self)
     
    def get_item(self, key, attributes):
        items = []

        for item in self._heap:
            if key.items() <= item.items():
                items.append({ key: item[key] for key in attributes })

        return tuple(items)
        
    def get_all_items(self, attributes):
        items = []

        for item in self._heap:
            items.append({ key: item[key] for key in attributes })

        return tuple(items)

class MemorySession(Session):
    
    def __init__(self, record_manager):
        self.record_manager = record_manager

        self._log = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        self.rollback()
    
    def put_item(self, item):
        if item is None:
            raise TypeError('item cannot be none')
        
        self._log.append(
            Operation(
                type='put',
                key=None,
                item=item
            )
        )

    def update_item(self, key, item):
        self._log.append(
            Operation(
                type='update',
                key=key,
                item=item
            )
        )

    def delete_item(self, key):
        self._log.append(
            Operation(
                type='delete',
                key=key,
                item=None
            )
        )
    
    def commit(self):
        for operation in self._log:
            if(operation.type == 'put'):
                self._put_item(operation.item)
            elif (operation.type == 'update'):
                self._update_item(operation.key, operation.item)
            elif (operation.type == 'delete'):
                self._delete_item(operation.key)
    
    def rollback(self):
        pass

    def _put_item(self, item):
        self.record_manager._heap.append(item)

    def _update_item(self, key, item):
        items = (i for i in self.record_manager._heap if self._match(key, i))
        for i in items:
            if callable(item):
                i.update(item(i))
            else:
                i.update(item)

    def _delete_item(self, key):
        items = (i for i in self.record_manager._heap if self._match(key, i))
        for i in items:
            self.record_manager._heap.remove(i)

    def _match(self, key, item):
        return key.items() <= item.items()
