"""
    Predict Standup for User
    :license: MIT
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Tuple

from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.dependency_typing import (Boto3SQS, PynamoDBConsultant,
                                                Requests)
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.dependencies.requests_provider import get_requests_provider
from src.modules.queue_message_loader import load_message
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types


def sub(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    sqs_client = get_sqs_provider()
    consultants_model = get_consultants_provider()
    requests_client = get_requests_provider()

    make_prediction(event, context, sqs_client,
                    consultants_model, requests_client)


def make_prediction(event: Dict, context, sqs_client: Boto3SQS,
                    consultants_model: PynamoDBConsultant,
                    requests_client: Requests) -> None:
    '''
        Subscribes to SNS Topic to predict standup hints
        -
        :param event: AWS event
        :param context: AWS Lambda context
        :param sqs_client: Boto3 SQS client
        :param consultants_model: PynamoDB Consultants Model
        :param requests_client: Requests Client
    '''
    print("Request ID:", context)
    print("event", event)

    attributes = load_message(
        event['Records'][0]['Sns']['MessageAttributes'], True)

    if ('type' not in attributes) or (attributes['type'] != Types.Predict):
        print('Type not found')

    entries = [
        create_entrie(attributes['consultant'], True, attributes['checkin-id'],
                      consultants_model, requests_client),
        create_entrie(attributes['consultant'], False, attributes['checkin-id'],
                      consultants_model, requests_client)
    ]
    entries = list(filter(lambda x: x is not None, entries))

    send = sqs_client.send_message_batch(
        QueueUrl=os.environ['CHECKIN_ACTION_URL'],
        Entries=entries
    )
    print(send)


def create_entrie(consultant: str, today: bool, checkin_id: str,
                  consultants_model: PynamoDBConsultant,
                  requests_client: Requests) -> Dict:
    '''
        Creates an entrie for sending in message batch
        -
        :param consultant: consultant uuid
        :param today: is it today or yesterday true/false
        :param checkin_id: checkin uuid
        :param consultants_model: PynamoDB Consultants Model
        :param requests_client: Requests Client
    '''
    payload = {
        "header": {
            "prediction-type": "hint",
            "posibility": 95 if today else 90,
            "source": "slack"
        },
        "body": {
            "type": "standup",
            "message": "",
        }
    }
    entrie = {
        'Id': "",
        'MessageBody': 'Prediction',
        'MessageAttributes': "",
        'MessageDeduplicationId': str(uuid.uuid4()),
        'MessageGroupId': "Prediction"
    }

    message = get_standups_for_consultant(
        consultant, today, consultants_model, requests_client)

    payload['body']['message'] = message

    entrie['Id'] = str(uuid.uuid4()).replace('-', '_')
    entrie['MessageAttributes'] = write_message(consultant, Types.Prediction,
                                                checkin_id=checkin_id, payload=payload)

    return entrie if message is not None else None


def get_standups_for_consultant(consultant: str, today: bool, consultants_model: PynamoDBConsultant,
                                requests_client: Requests) -> Tuple:
    '''
        Get standups for today and yesterday
        -
        :param consultant: consultant uuid
        :param today: is it today or yesterday true/false
        :param consultants_model: PynamoDB Consultants Model
        :param requests_client: Requests Client
    '''
    date_today = datetime.today()
    if today:
        date = date_today
    else:
        date = date_today - timedelta(days=1) \
            if date_today.weekday() != 0 \
            else date_today - timedelta(days=3)

    date = datetime(date.year, date.month, date.day, 0, 0).timestamp()

    auth_token = os.environ['SlackAuth']
    hed = {'Authorization': 'Bearer ' + auth_token}

    url = 'https://slack.com/api/conversations.history?channel={0}&oldest={1}'\
        .format('C6NEF8SQ2', date)
    response = requests_client.post(url, headers=hed)

    response_data = response.json()

    consultant_data = consultants_model.get(consultant)

    def iterator_func(item):
        if 'user' in item:
            if item['user'] == consultant_data.slack_id:
                return True
        return False

    consultent_messages = list(
        filter(iterator_func, response_data['messages']))
    print(consultent_messages)

    if len(consultent_messages) > 0:
        message = "_{0}:_ {1}".format("Todays DSU" if today else "Yesterdays DSU",
                                      consultent_messages[-1]['text'].split('\n')
                                      [0 if today else 1][3:])
    else:
        message = None

    return message
