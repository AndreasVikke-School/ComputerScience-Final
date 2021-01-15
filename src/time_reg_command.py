""" Slack /signup for registering user to database """
import os
import uuid
from datetime import date, datetime

from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.dependency_typing import Boto3SQS, PynamoDBConsultant
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types


def command(event, context):
    '''
        AWS Lambda Handler
        -
        :param event: AWS Event
        :param context: AWS Lambda context
    '''
    print("Context: ", context)
    print("Event: ", event)
    print("Date: ", event['body']['text'])

    try:
        checkin_date = datetime.strptime(event['body']['text'], '%Y-%m-%d').date()
    except ValueError:
        return {
            "response_type": "ephemeral",
            "text": "Error: Date formatting Error"
        }

    sqs_client = get_sqs_provider()
    consultant_model = get_consultants_provider()
    print("Test")
    return checkin(checkin_date, event['body']['user_id'], sqs_client, consultant_model)


def checkin(checkin_date: date, slack_id: str, sqs_client: Boto3SQS,\
            consultant_model: PynamoDBConsultant):
    '''
        Starts Checkin
        -
        :param sqs_client: AWS Event
        :param context: AWS Lambda context
    '''
    checkin_action_url = os.environ['CHECKIN_ACTION_URL']
    consultant = next(consultant_model.slack_id_index.query(slack_id), None)

    if consultant is not None:
        print(checkin_date)
        message = write_message(consultant.uuid, Types.Scheduled, checkin_date=str(checkin_date))
        send_scheduled = sqs_client.send_message(
                        QueueUrl=checkin_action_url,
                        MessageBody= 'Scheduled',
                        MessageAttributes=message,
                        MessageDeduplicationId= str(uuid.uuid4()),
                        MessageGroupId= "Scheduled")
        print(send_scheduled)
        response_text = "The CheckIn for '{}' will be with you shortly".format(checkin_date)
    else:
        response_text = "Error: Consultant not found"

    return {
        "response_type": "ephemeral",
        "text": response_text
    }
