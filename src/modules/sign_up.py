""" Slack signup module """
import os
import uuid

from src.dependencies.dependency_typing import PynamoDBConsultant, Requests


def sign_up(user_id: dict, requests: Requests, consultant_model:PynamoDBConsultant) -> str:
    '''
        Takes email and user ID from a slack user and adds to database.
        :param event: AWS Event
        :param context: AWS Lambda context
        :param requests_client: Request client
        :param consultant_model: Consultant model
    '''
    auth_token = os.environ['SlackAuth']
    hed = {'Authorization': 'Bearer ' + auth_token}

    param = {"user" : user_id}

    url = "https://slack.com/api/users.info"
    request = requests.get(url, headers = hed, params = param)

    response = request.json()
    email = response['user']['profile']['email']

    text = ""
    consultant = next(consultant_model.email_index.query(email), None)

    if consultant is None:
        text = "There you go! You've been signed up and will now receive messages from Sterling."
        consultant = consultant_model(uuid=str(uuid.uuid4()), email=email, slack_id=user_id)
        consultant.save()
    else:
        text = "You're already signed up!"

    return text
