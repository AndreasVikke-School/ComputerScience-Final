""" Slack /signup for registering user to database """
from typing import Dict

from src.dependencies.dependency_typing import PynamoDBConsultant, Requests
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.dependencies.requests_provider import get_requests_provider
from src.modules.sign_up import sign_up


def signup(event, context):
    '''
        AWS Lambda Handler
        -
        :param event: AWS Event
        :param context: AWS Lambda context
    '''
    print("context: ", context)
    print("event: ", event['body'])
    requests = get_requests_provider()
    consultant_model = get_consultants_provider()
    command = register(event, requests, consultant_model)
    return command

def register(event, requests: Requests, consultant_model:PynamoDBConsultant) -> Dict:
    '''
        Takes email and user ID from a slack user and adds to database.
        -
        :param event: AWS Event
        :param context: AWS Lambda context
        :param requests_client: Request client
        :param consultant_model: Consultant model
    '''

    user_id = event['body']['user_id']

    text = sign_up(user_id, requests, consultant_model)

    return {
        "response_type": "ephemeral",
        "text": text
    }
