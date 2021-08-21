import pytest
import json
import boto3
import moto
import datetime
from unittest import mock

from domainpy.application.integration import ScheduleIntegartionEvent
from domainpy.infrastructure.mappers import Mapper
from domainpy.infrastructure.transcoder import Transcoder
from domainpy.infrastructure.publishers.aws_sfn import AwsStepFunctionSchedulerPublisher


@pytest.fixture
def region_name():
    return 'us-east-1'

@pytest.fixture
def iam(region_name):
    with moto.mock_iam():
        yield boto3.client('iam', region_name=region_name)

@pytest.fixture
def stepfunctions(region_name):
    with moto.mock_stepfunctions():
        yield boto3.client('stepfunctions', region_name=region_name)

@pytest.fixture(autouse=True)
def state_machine_arn(stepfunctions, iam):
    role = iam.create_role(
        RoleName='role',
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "states.amazonaws.com"
                    },
                    "Action": "*"
                }
            ]
        }),
        Description='This is a test role',
        Tags=[
            {
                'Key': 'Owner',
                'Value': 'msb'
            }
        ]
    )
    roleArn = role['Role']['Arn']

    response = stepfunctions.create_state_machine(
        name='scheduler',
        definition=json.dumps({
            "StartAt": "pass",
            "States": {
                "pass": {
                    "Type": "Pass",
                    "Next": "End"
                }
            }
        }),
        roleArn=roleArn
    )
    return response['stateMachineArn']

def test_stepfunction_scheduler_publish(stepfunctions, state_machine_arn, region_name):
    integration = ScheduleIntegartionEvent(
        __publish_at_field__='publish_at',
        __timestamp__=0.0,
        __trace_id__='tid',
        __context__='ctx',
        publish_at=datetime.datetime.now().isoformat()
    )

    mapper = Mapper(transcoder=Transcoder())
    mapper.register(ScheduleIntegartionEvent)

    pub = AwsStepFunctionSchedulerPublisher(state_machine_arn, mapper, region_name=region_name)
    pub.publish(integration)

    executions = stepfunctions.list_executions(stateMachineArn=state_machine_arn)['executions']
    assert len(executions) == 1
    
    execution = stepfunctions.describe_execution(executionArn=executions[0]['executionArn'])
    input = json.loads(execution['input'])
    assert tuple(input.keys()) == ('publish_at', 'payload')
