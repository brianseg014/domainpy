
from collections import namedtuple


IntegrationRecord = namedtuple(
    'IntegrationRecord', 
    ('trace_id', 'context', 'topic', 'resolve', 'version', 'timestamp', 'message', 'error', 'payload')
)


class IntegrationMapper:
    
    def __init__(self, context):
        self.context = context

        self.map = dict()
        
    def register(self, cls):
        self.map[cls.__name__] = cls
        return cls
    
    def is_integration(self, topic):
        return topic in self.map
    
    def serialize(self, event):
        if hasattr(event.__class__, '__annotations__'):
            attrs = event.__class__.__dict__['__annotations__']
            
            return IntegrationRecord(
                trace_id=event.__trace_id__, # pylint: disable=maybe-no-member
                context=self.context, # pylint: disable=maybe-no-member
                topic=event.__class__.__name__,
                resolve=event.__resolve__,
                version=event.__version__, # pylint: disable=maybe-no-member
                timestamp=event.__timestamp__, # pylint: disable=maybe-no-member
                message=event.__message__,
                error=event.__error__,
                payload=event.__to_dict__()
            )
        else:
            raise NotImplementedError(
                f'{event.__class__.__name__} should have annotations'
            )
    
    def deserialize(self, integration_record: IntegrationRecord):
        integration_class = self.map[integration_record.topic]
        integration = integration_class.__from_dict__(integration_record.payload)
        
        integration.__dict__.update({
            '__trace_id__': integration_record.trace_id,
            '__context__': integration_record.context,
            '__version__': integration_record.version,
            '__timestamp__': integration_record.timestamp,
            '__message__': integration_record.message,
            '__error__': integration_record.error
        })
        
        return integration
    