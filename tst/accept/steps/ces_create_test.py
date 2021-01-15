import os
import boto3, datetime, time
from behave import *
from src.models.model_checkin import CheckInModel
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types
from src.modules.get_export import get_export
from src.checkin_consume import checkin_consumer
from src.dependencies.boto3_sns_provider import get_sns_provider
from src.dependencies.boto3_sfn_provider import get_sfn_provider
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_consultant_provider import get_consultants_provider
from src.dependencies.requests_provider import get_requests_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.pynamodb_contract_provider import get_contracts_provider

@given(u'a lambda function for database')
def step_impl(context):
    # Pass as the import to the lambda didn't fail
    context.sns_client = get_sns_provider(test=True)
    context.sfn_client = get_sfn_provider(test=True)
    context.checkin_model = get_checkin_provider(test=True)
    context.consultant_model = get_consultants_provider(test=True)
    context.request_model = get_requests_provider(test=True)
    context.customer_model = get_customers_provider(test=True)
    context.contract_model = get_contracts_provider(test=True)
    pass


@when(u'a message is consumed from action queue for database')
def step_impl(context):
    context.event = {
        'Records': [
            {
                'messageAttributes': {
                    'consultant': {'stringValue': 'BehaveTest1', 'dataType': 'String'},
                    'type': {'stringValue': 'scheduled', 'dataType': 'String.type'},
                    'checkin-date': {'stringValue': '2020-01-01', 'dataType': 'String'}
                }
            }
        ]
    }
    prediction_arn = get_export('predict-topic-arn')
    os.environ['TIMES_UP_MACHINE'] = 'times_up_machine'

    context.response = checkin_consumer(context.event, None, context.sns_client, context.sfn_client, context.checkin_model, context.consultant_model, context.request_model, context.consultant_model, context.contract_model)
    assert context.sns_client.publish.call_args.kwargs['TopicArn'] == prediction_arn

@then(u'create Null checkin in database')
def step_impl(context):
    assert context.checkin_model.call_count == 1
    assert context.checkin_model.call_args.kwargs['consultant_uuid'] == 'BehaveTest1'

@then(u'Publish a message to an SNS topic')
def step_impl(context):
    assert context.sns_client.publish.call_count == 1

@then(u'start waiter for Slack App Queue publisher')
def step_impl(context):
    assert context.sfn_client.start_execution.call_count == 1