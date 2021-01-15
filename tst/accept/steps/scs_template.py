import uuid
import os
from datetime import date
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types
from src.modules.get_export import get_export
from src.combine_template_to_slack import consume_sqs
from src.process_user_input import process_template
from src.models.model_checkin import CheckInModel
from src.dependencies.boto3_sns_provider import get_sns_provider
from src.dependencies.requests_provider import get_requests_provider
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.pynamodb_consultant_provider import get_consultants_provider
from src.dependencies.boto3_sfn_provider import get_sfn_provider

@given(u'a lambda function connected to an sqs')
def step_impl(context):
    # Pass as the import to the lambda didn't fail
    pass

@when(u'a message is consumed from a queue')
def step_impl(context):
    event = {'body': {'payload': '{"type": "block_actions", "trigger_id":"xxx","actions":[{"action_id":"XVB","block_id":"0Inw","text":{"type":"plain_text","text":"Start Checkin","emoji":true},"value":"start;BehaveCheckinId1","style":"primary","type":"button","action_ts":"1600434376.198756"}]}'}}

    os.environ['SlackAuth'] = "Auth"
    context.request = process_template(event, True)

@then(u'Combine message and template')
def step_impl(context):
    pass
    # print(context.requests_client.post.call_args)
    # print(context.requests_client.post.call_args.kwargs['json'])
    # assert 'view' in context.requests_client.post.call_args.kwargs['json']

@then(u'Publish template to slack')
def step_impl(context):
    pass
    # assert context.requests_client.post.call_count == 1