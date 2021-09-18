# pylint: disable=super-init-not-called,unused-argument


from domainpy.infrastructure.eventsourced.managers.memory import (
    MemoryEventRecordManager,
)
from domainpy.infrastructure.publishers.memory import MemoryPublisher
from domainpy.infrastructure.tracer.managers.memory import (
    MemoryTraceStore,
    MemoryTraceSegmentStore,
)
from domainpy.infrastructure.mappers import Mapper


class DynamoDBEventRecordManager(MemoryEventRecordManager):
    def __init__(self, table_name, **kwargs):
        super().__init__()


class AwsEventBridgePublisher(MemoryPublisher):
    def __init__(self, bus_name: str, context: str, mapper: Mapper, **kwargs):
        pass


class AwsStepFunctionSchedulerPublisher(MemoryPublisher):
    def __init__(self, state_machine_arn: str, mapper: Mapper, **kwargs):  #
        pass


class AwsSimpleNotificationServicePublisher(MemoryPublisher):
    def __init__(self, topic_arn: str, context: str, mapper: Mapper, **kwargs):
        pass


class AwsSimpleQueueServicePublisher(MemoryPublisher):
    def __init__(self, queue_name: str, mapper: Mapper, **kwargs):
        pass


class DynamoDBTraceStore(MemoryTraceStore):
    def __init__(self, table_name: str, mapper: Mapper, **kwargs):
        pass


class DynamoDBTraceSegmentStore(MemoryTraceSegmentStore):
    def __init__(self, table_name: str, mapper: Mapper, **kwargs):
        pass
