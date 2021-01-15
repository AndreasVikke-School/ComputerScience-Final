"""
    Processes user input from slack
    :license: MIT
"""
import json
from typing import Dict

from src.modules.user_input_global import UserInputGlobal
from src.modules.user_input_handle_block_action import UserInputHandleBlockAction
from src.modules.user_input_handle_view_submission import UserInputHandleViewSubmission


def process(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    print("Context: ", context)

    return process_template(event)


def process_template(event: Dict, test: bool = False) -> Dict:
    '''
        Template processor
        -
        :param event: AWS event
        :param context: AWS Lambda context
        :param sqs_client: Boto3 sqs client
        :param requests_client: Request client
        :param checkin_modal: Checkin modal
        :param customers_model: Customer modal
        :param consultant_model: Consultant modal
    '''
    print("Event: ", event)

    response = event['body']['payload']
    payload = json.loads(response)

    user_input_global = UserInputGlobal(payload, test)
    payload_type = user_input_global.get_payload_type()

    if payload_type == 'block_actions':
        UserInputHandleBlockAction(payload, test).handle_block_action()
        # handle_block_action(payload, requests_client, checkin_model, customers_model,\
        #     sqs_client, consultant_model)
        update = {'statuscode': 200}

    elif payload['type'] == 'view_submission':
        update = UserInputHandleViewSubmission(payload, test).handle_view_submission()
        # update = handle_view_submission(payload, checkin_model,
        #     sqs_client, customers_model, stepfunctions_client)

    print('UPDATE: ', update)
    return update
