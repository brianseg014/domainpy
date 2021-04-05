
from domainpy.infrastructure.eventsourced.eventstream import EventStream


class EventStore:
    
    def __init__(self, event_mapper, record_manager, bus):
        self.event_mapper = event_mapper
        self.record_manager = record_manager
        self.bus = bus
    
    def store_events(self, stream):
        with self.record_manager.session() as session:
            for e in stream:
                session.append(
                    self.event_mapper.serialize(e)
                )
            
            session.commit()

            for e in stream:
                self.bus.publish(e)
        
    def get_events(self, stream_id: str):
        events = self.record_manager.find(
            stream_id=stream_id
        )
        
        stream = EventStream()
        for e in events:
            stream.append(
                self.event_mapper.deserialize(e)
            )
            
        return stream
        