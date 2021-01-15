import os
from behave import *
from datetime import date
import boto3, time, uuid, json
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

@given(u'a lambda function to update database')
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


@when(u'a message is consumed from action queue')
def step_impl(context):
    context.event = {
        'Records': [
            {
                'messageAttributes': {
                    'consultant': {'stringValue': 'BehaveTest1', 'dataType': 'String'}, 
                    'type': {'stringValue': 'prediction', 'dataType': 'String.type'},
                    'checkin-id': {'stringValue': "BehaveCheckinId1", 'dataType': 'String'},
                    'device-id': {'stringValue': '1234', 'dataType': 'String'},
                    'payload': 
                        {'stringValue': json.dumps({
                            "header": {
                                "prediction-type": "activity",
                                "posibility": "95",
                                "source": "geofencing"
                            },
                            "body": {
                                "type": "customer",
                                "customer": "Customer A",
                                "project": "Project Alpha",
                                "starttime": "2020-09-10 12:43:23.099428",
                                "endtime": "2020-09-10 12:43:23.099428",
                                "description": "Description"
                            }
                        }), 
                        'dataType': 'String.json' }
                }
            }
        ]
    }

    context.response = checkin_consumer(context.event, None, context.sns_client, context.sfn_client, context.checkin_model, context.consultant_model, context.request_model, context.consultant_model, context.contract_model)
    assert context.checkin_model.get.call_count == 1
    
@then(u'Update checkin in database with predictions')
def step_impl(context):
    assert context.checkin_model.predictions.set.call_count == 1