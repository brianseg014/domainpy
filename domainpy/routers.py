
from domainpy.application.command import ApplicationCommand
from domainpy.application.query import ApplicationQuery
from domainpy.application.integration import IntegrationEvent
from domainpy.application.integration import ScheduleIntegartionEvent
from domainpy.domain.model.event import DomainEvent
from domainpy.utils.bus import ISubscriber, FilterPolicy
from domainpy.typing.infrastructure import InfrastructureMessage


class LayeredContextRouter(ISubscriber[InfrastructureMessage]):

    def __init__(self) -> None:
        self.application_policy = FilterPolicy(
            effect=FilterPolicy.Effect.NOT_MATCH,
            types=[ScheduleIntegartionEvent],
            targets=[
                FilterPolicy(
                    types=[
                        ApplicationCommand,
                        ApplicationQuery,
                        IntegrationEvent
                    ]
                )
            ]
        )
        self.schedule_policy = FilterPolicy(
            types=[ScheduleIntegartionEvent]
        )
        self.domain_policy = FilterPolicy(
            types=[DomainEvent]
        )

    def attach_to_application_policy(self, subscriber: ISubscriber) -> None:
        self.application_policy.attach(subscriber)

    def attach_to_schedule_policy(self, subscriber: ISubscriber) -> None:
        self.schedule_policy.attach(subscriber)

    def attach_to_domain_policy(self, subscriber: ISubscriber) -> None:
        self.domain_policy.attach(subscriber)

    def __route__(self, message: InfrastructureMessage) -> None:
        self.application_policy.publish(message)
        self.schedule_policy.publish(message)
        self.domain_policy.publish(message)
