import os
from src.scheduler_publish import run_scheduler
from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.pynamodb_consultant_provider import get_consultants_provider
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider

@given(u'a lambda function for scheduler')
def step_impl(context):
    # Pass as the import to the lambda didn't fail
    context.sqs_client = get_sqs_provider(test=True)
    context.consultants_model = get_consultants_provider(test=True)
    context.checkin_model = get_checkin_provider(test=True)
    pass

@when(u'the time is 9 o’clock')
def step_impl(context):
    queue_url = 'scheduler'
    os.environ['CHECKIN_ACTION_URL'] = queue_url
    run_scheduler({'httpMethod': 'true'}, None, context.sqs_client, context.consultants_model, context.checkin_model)
    assert context.sqs_client.send_message_batch.call_count == 3
    assert context.consultants_model.scan.call_count == 1

@then(u'Publish a message with a username to an sqs')
def step_impl(context):
    # assert len(context.sqs_client.send_message_batch.call_args.kwargs['Entries']) == 3
    pass
