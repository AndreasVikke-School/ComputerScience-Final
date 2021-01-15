"""
    Combines Template with CheckinId
    :license: MIT
"""
import json
import os
from typing import Dict
import datetime

from src.dependencies.dependency_typing import (PynamoDBCheckIn,
                                                PynamoDBConsultant, Requests)
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.dependencies.requests_provider import get_requests_provider
from src.modules.queue_message_loader import load_message
from src.modules.type_enum import Types


def consume(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda Context
    '''
    consultants_model = get_consultants_provider()
    checkin_model = get_checkin_provider()
    request_client = get_requests_provider()

    consume_sqs(event, context, consultants_model, checkin_model, request_client)


def consume_sqs(event: Dict, context, consultants_model: PynamoDBConsultant,
                checkin_model: PynamoDBCheckIn,
                request_client: Requests) -> None:
    '''
        Combines CheckInId with Start Modal Button
        -
        :param event: AWS event
        :param context: AWS Lambda Context
        :param consultants_model: PynamoDB Consultants Model
        :param checkin_model: PynamoDB Checkin Model
        :param request_client: Requests Client
    '''
    print("Context: ", context)
    print("Event: ", event)

    message = load_message(event['Records'][0]['messageAttributes'])
    checkin = checkin_model.get(message['checkin-id'])

    last_bus_day = datetime.datetime.strptime(checkin.date, '%Y-%m-%d')
    # last_bus_day = last_bus_day -\
    #     datetime.timedelta(max(1,(last_bus_day.weekday() + 6) % 7 - 3))

    with open('src/templates/modal_start_button.json', 'r') as start_button:
        start_button = json.load(start_button)
        if message['type'] == Types.Slack_Reminder:
            start_button[0]['text']['text'] = 'You forgot to Checkin the {0}\'th of {1}'\
                .format(last_bus_day.day, last_bus_day.strftime("%B"))
        else:
            start_button[0]['text']['text'] = 'Make Checkin for the {0}\'th of {1}'\
                .format(last_bus_day.day, last_bus_day.strftime("%B"))
        start_button[0]['accessory']['value'] = 'start;{0}'.format(message['checkin-id'])
        print("Body: ", start_button)

        consultant = consultants_model.get(message['consultant'])

        hed = {'Authorization': 'Bearer ' + os.environ['SlackAuth']}

        data = {
            "channel": consultant.slack_id,
            "text": "Start Checkin",
            "blocks": start_button
        }

        url = 'https://slack.com/api/chat.postMessage'
        response = request_client.post(url, json=data, headers=hed)
        print(response)
