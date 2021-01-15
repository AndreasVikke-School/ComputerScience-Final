"""
    Processes event api from slack
    :license: MIT
"""
import json
import os
from typing import Dict

from src.modules.create_signedup_homepage import create_home_tap
from src.dependencies.dependency_typing import Requests, PynamoDBConsultant
from src.dependencies.requests_provider import get_requests_provider
from src.dependencies.pynamodb_consultant_provider import get_consultants_provider


def process(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    print(event)
    print(context)

    requests_client = get_requests_provider()
    consultant_model = get_consultants_provider()

    return proccess_request(event, requests_client, consultant_model)

def proccess_request(event, requests_client: Requests,
                     consultant_model: PynamoDBConsultant) -> None:
    '''
        Proccess request
        -
        :param event: AWS event
        :param requests_client: Request Client
        :param consultant_model: Consultant Client
    '''
    event_body = event['body']

    if event_body['type'] == 'event_callback':
        if 'event' in event_body and event_body['event']['type'] == 'app_home_opened':
            user_id = event_body['event']['user']
            consultant = next(consultant_model.slack_id_index.query(user_id), None)

            if consultant is not None:
                home_tap = create_home_tap(consultant.uuid, consultant_model)
            else:
                with open("src/templates/{0}.json".format('home_tap_template_signup'), "r")\
                        as body:
                    home_tap = json.load(body)

            data = {
                'user_id': user_id,
                'view': home_tap
            }
            response = post('https://slack.com/api/views.publish', data, requests_client)
    elif event_body['type'] == 'url_verification':
        response = {
            'challenge': event_body['challenge']
        }
    print(response)
    return response

def post(url: str, data: Dict, requests_client: Requests) -> Requests:
    '''
        Posts the data
        -
        :param url: Url to slack api
        :param data: The data to post
        :param requests_client: Request client
    '''
    auth_token = os.environ['SlackAuth']
    hed = {'Authorization': 'Bearer ' + auth_token}
    response = requests_client.post(url, json=data, headers=hed)
    print('RESPONSE: ', response.json())
    return response.json()
