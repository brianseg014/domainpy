
from domainpy.typing import SystemMessage
from domainpy.application.service import ApplicationService
from domainpy.infrastructure.publishers.aws_eventbridge import AwsEventBridgePublisher
from domainpy.infrastructure.publishers.aws_sqs import AwsSimpleQueueServicePublisher
from domainpy.utils.bus import Subscriber


class ApplicationServiceSubscriber(Subscriber):

    def __init__(self, application_service: ApplicationService):
        self.application_service = application_service

    def __route__(self, message: SystemMessage):
        self.application_service.handle(message)
    

class AwsEventBridgePublisherSubscriber(Subscriber):

    def __init__(self, aws_event_bridge_publisher: AwsEventBridgePublisher):
        self.aws_event_bridge_publisher = aws_event_bridge_publisher

    def __route__(self, message: SystemMessage):
        self.aws_event_bridge_publisher.publish(message)


class AwsSimpleQueueServicePublisherSubscriber(Subscriber):

    def __init__(self, aws_sqs_publisher: AwsSimpleQueueServicePublisher):
        self.aws_sqs_publisher = aws_sqs_publisher

    def __route__(self, message: SystemMessage):
        self.aws_sqs_publisher.publish(message)
