from typing import Tuple

from domainpy.application.exceptions import ExtractorMatchNotFound, MalformedMessageError
from domainpy.application.mappers.commandmapper import CommandMapper
from domainpy.application.mappers.eventmapper import EventMapper
from domainpy.application.bus import Bus


class MessageExtractor:

    def match(self, message: dict):
        raise NotImplementedError(f'{self.__class__.__name__} should override match')

    def extract(self, message: dict):
        raise NotImplementedError(f'{self.__class__.__name__} should override extract')


class MessageProcessor:

    def __init__(self, 
            command_mapper: CommandMapper, 
            event_mapper: EventMapper, 
            command_handler_bus: Bus, 
            event_handler_bus: Bus, 
            extractors: Tuple[MessageExtractor]):
        self.command_mapper = command_mapper
        self.event_mapper = event_mapper
        self.command_handler_bus = command_handler_bus
        self.event_handler_bus = event_handler_bus
        self.extractors = extractors
    
    def process(self, message: dict):
        for extractor in self.extractors:
            if extractor.match(message):
                inner_message = extractor.extract(message)

                if '__message__' in inner_message and inner_message['__message__'] == 'command':
                    command = self.command_mapper.deserialize(inner_message)
                    self.command_handler_bus.publish(command)
                elif '__message__' in inner_message and inner_message['__message__'] == 'event':
                    event = self.event_mapper.deserialize(inner_message)
                    self.event_handler_bus.publish(event)
                else:
                    raise MalformedMessageError(f'Unrecognized message structure: {inner_message}')

                return # Message processed

        raise ExtractorMatchNotFound(f'Unable to find compatible extractor for: {message}')

