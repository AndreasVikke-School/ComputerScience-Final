import os
import boto3
import time
from src.modules.get_export import get_export
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types
from src.predictors.predict_customers import make_prediction
from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.pynamodb_online_statuses_provider import get_online_statuses_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider

PREDICT_TOPIC_ARN = get_export('predict-topic-arn')
ENV_TYPE = get_export('pipeline-enviroment-type')

@given(u'a lambda function')
def step_impl(context):
    # Pass as the import to the lambda didn't fail
    context.sqs_client = get_sqs_provider(test=True)
    context.online_statuses_model = get_online_statuses_provider(test=True)
    context.customer_model = get_customers_provider(test=True)
    context.checkin_model = get_checkin_provider(test=True)
    pass

@when(u'a message is consumed from a predict topic')
def step_impl(context):
    context.event = {
        'Records': [
            {
                'Sns': {
                    'MessageAttributes': {
                        'consultant': {'Type': 'String', 'Value': 'BehaveTest1'},
                        'type': {'Type': 'String', 'Value': 'predict'}, 
                        'checkin-id': {'Type': 'String', 'Value': '1234'}
                    }
                }
            }
        ]
    }
    #queue_url = 'predict-topic'
    #os.environ['CHECKIN_ACTION_URL'] = queue_url
    #context.prediction = make_prediction(context.event, None, context.sqs_client, context.customer_model, context.checkin_model)
    pass

@then(u'Then make a hardcoded prediction')
def step_impl(context):
    #assert len(context.sqs_client.send_message_batch.call_args.kwargs['Entries']) == 3
    pass

@then(u'publish it to action queue')
def step_impl(context):
    #assert context.sqs_client.send_message_batch.call_count == 1
    pass