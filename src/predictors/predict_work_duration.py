"""
    Predict Work Duration for User
    :license: MIT
"""
import datetime
import json
import os
import uuid
from typing import Dict, Tuple

from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.dependency_typing import Boto3SQS, PynamoDBOnlineStatuses
from src.dependencies.pynamodb_online_statuses_provider import \
    get_online_statuses_provider
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
    online_status_model = get_online_statuses_provider()

    make_prediction(event, context, sqs_client, online_status_model)


def make_prediction(event: Dict, context, sqs_client: Boto3SQS,
                    online_status_model: PynamoDBOnlineStatuses) -> None:
    '''
        Subscribes to SNS Topic to predict work duration
        -
        :param event: AWS event
        :param context: AWS Lambda context
        :param sqs_client: Boto3 SQS client
        :param online_status_model: PynamoDB Online Statuses Model
    '''
    print("Request ID:", context)
    print("event", event)

    attributes = load_message(
        event['Records'][0]['Sns']['MessageAttributes'], True)

    if ('type' not in attributes) or (attributes['type'] != Types.Predict):
        print('Type not found')

    entries = [
        create_entrie(attributes['consultant'],
                      attributes['checkin-id'], online_status_model)
    ]

    send = sqs_client.send_message_batch(
        QueueUrl=os.environ['CHECKIN_ACTION_URL'],
        Entries=entries
    )
    print(send)


def create_entrie(consultant: str, checkin_id: str,
                  online_status_model: PynamoDBOnlineStatuses) -> Dict:
    '''
        Creates an entrie for sending in message batch
        -
        :param consultant: consultant uuid
        :param checkin_id: checkin uuid
        :param online_status_model: PynamoDB Online Statuses Model
    '''
    payload = {
        "header": {
            "prediction-type": "duration",
            "posibility": 95,
            "source": "slack"
        },
        "body": {
            "type": "start-end",
            "starttime": "",
            "endtime": ""
        }
    }
    entrie = {
        'Id': "",
        'MessageBody': 'Prediction',
        'MessageAttributes': "",
        'MessageDeduplicationId': str(uuid.uuid4()),
        'MessageGroupId': "Prediction"
    }

    start_time, end_time = calculate_start_end_time(
        consultant, online_status_model)
    payload['body']['starttime'] = start_time['time']
    payload['body']['endtime'] = end_time['time']

    entrie['Id'] = str(uuid.uuid4()).replace('-', '_')
    entrie['MessageAttributes'] = write_message(consultant, Types.Prediction,
                                                checkin_id=checkin_id, payload=payload)

    return entrie


def calculate_start_end_time(consultant: str, online_status_model: PynamoDBOnlineStatuses) -> Tuple:
    '''
        Calculates Start and end time for consultant, from yesterday
        -
        :param consultant: consultant uuid
        :param online_status_model: PynamoDB Online Statuses Model
    '''
    last_day = datetime.datetime.today() - datetime.timedelta(days=1) \
        if datetime.datetime.today().weekday() != 0 \
        else datetime.datetime.today() - datetime.timedelta(days=3)
    last_day = last_day.strftime('%Y-%m-%d')

    print(consultant, last_day)
    online_status = online_status_model.get(consultant, last_day)

    statuses = sorted(json.loads(online_status.statuses),
                      key=lambda x: x['time'], reverse=False)
    print(statuses)

    start_time = \
        list(filter(lambda x: datetime.datetime.strptime(x['time'].split(" ")[1], '%H:%M:%S.%f')
                    > datetime.datetime.strptime('04:00:00.000000', '%H:%M:%S.%f'), statuses))[0]
    end_time = \
        list(filter(lambda x: datetime.datetime.strptime(x['time'].split(" ")[1], '%H:%M:%S.%f')
                    < datetime.datetime.strptime('17:00:00.000000', '%H:%M:%S.%f'), statuses))[-1]

    print(start_time, end_time)

    return(start_time, end_time)
