import typing

if typing.TYPE_CHECKING:
    from domainpy.typing import SystemMessage, ApplicationService, IPublisher

from domainpy.utils.bus import ISubscriber


class ApplicationServiceSubscriber(ISubscriber):

    def __init__(self, application_service: 'ApplicationService'):
        self.application_service = application_service

    def __route__(self, message: 'SystemMessage'):
        self.application_service.handle(message)
    

class PublisherSubciber(ISubscriber):

    def __init__(self, publisher: 'IPublisher'):
        self.publisher = publisher

    def __route__(self, message: 'SystemMessage'):
        self.publisher.publish(message)
