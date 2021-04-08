
from collections import namedtuple


CommandRecord = namedtuple(
    'CommandRecord', 
    ('trace_id', 'topic', 'version', 'timestamp', 'message', 'payload')
)


class CommandMapper:
    
    def __init__(self):
        self.map = dict()
        
    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls

    def is_command(self, topic):
        return topic in self.map
    
    def serialize(self, command):
        if hasattr(command.__class__, '__annotations__'):
            attrs = command.__class__.__dict__['__annotations__']
            
            return CommandRecord(
                trace_id=command.__trace_id__,
                topic=command.__class__.__name__,
                version=command.__version__, # pylint: disable=maybe-no-member
                timestamp=command.__timestamp__, # pylint: disable=maybe-no-member
                message=command.__message__,
                payload=command.__to_dict__()
            )
        else:
            raise NotImplementedError(
                f'{command.__class__.__name__} should have annotations'
            )
    
    def deserialize(self, command_record: CommandRecord):
        command_class = self.map[command_record.topic]
        command = command_class.__from_dict__(command_record.payload)
        
        command.__dict__.update({
            '__trace_id__': command_record.trace_id,
            '__version__': command_record.version,
            '__timestamp__': command_record.timestamp,
            '__message__': command_record.message
        })
        
        return command
    