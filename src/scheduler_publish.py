"""
    Scheduler Service for starting flow
    :license: MIT
"""
import os
import uuid
import time
from datetime import date, datetime, timezone, timedelta
from typing import Dict
import pytz

from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.dependency_typing import (Boto3SQS, PynamoDBCheckIn,
                                                PynamoDBConsultant)
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types


def pub(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    sqs_client = get_sqs_provider()
    consultants_model = get_consultants_provider()
    checkin_model = get_checkin_provider()

    run_scheduler(event, context, sqs_client, consultants_model, checkin_model)


def run_scheduler(event: Dict, context, sqs_client: Boto3SQS,
                  consultants_model: PynamoDBConsultant,
                  checkin_model: PynamoDBCheckIn) -> None:
    '''
        Runs Scheduler Services
        -
        :param event: AWS event
        :param context: AWS context
        :param sqs_client: Boto3 SQS client
        :param consultants_model: PynamoDB Consultant Model
        :param checkin_model: PynamoDB Checkin Model
    '''
    print("context:", context)
    print("event", event)

    today = datetime.today()
    print("UTC: ", today)
    today = today.replace(tzinfo=timezone.utc).astimezone(pytz.timezone('Europe/Berlin'))
    print("EU: ", today)

    if 'httpMethod' in event:
        consultants = consultants_model.scan()
        for consultant in consultants:
            scheduler_start_checkin(consultant, sqs_client, checkin_model)
    else:
        if today.weekday() < 5:
            consultants = consultants_model.scan()
            for consultant in consultants:
                if consultant.time_for_checkin is None:
                    checkin_normal_time(today, consultant, sqs_client,\
                        checkin_model, consultants_model)
                else:
                    checkin_custom_time(today, consultant, sqs_client,\
                        checkin_model, consultants_model)

def checkin_custom_time(today, consultant, sqs_client, checkin_model, consultants_model):
    '''
        Checkin for normal time of day (9 o'clock)
        -
        :param today: today time and day
        :param consultant: current consultant
        :param sqs_client: sqs client
        :param checkin_model: checkin model
        :param consultants_model: consultants model
    '''
    consultant_time = time.strptime(consultant.time_for_checkin, "%H:%M")
    if today.hour == consultant_time.tm_hour\
            and today.minute >= consultant_time.tm_min\
            and today.minute <= consultant_time.tm_min + 2:
        if consultant.absence_till is None:
            scheduler_start_checkin(consultant, sqs_client, checkin_model)
        else:
            update_absence_till(consultant, consultants_model)


def checkin_normal_time(today, consultant, sqs_client, checkin_model, consultants_model):
    '''
        Checkin for normal time of day (9 o'clock)
        -
        :param today: today time and day
        :param consultant: current consultant
        :param sqs_client: sqs client
        :param checkin_model: checkin model
        :param consultants_model: consultants model
    '''
    if today.hour == 9 and today.minute < 2:
        if consultant.absence_till is None:
            scheduler_start_checkin(consultant, sqs_client, checkin_model)
        else:
            update_absence_till(consultant, consultants_model)
    elif today.hour == 14 and today.minute < 2:
        scheduler_start_checkin(consultant, sqs_client, checkin_model,\
            reminder=True)


def update_absence_till(consultant, consultants_model: PynamoDBConsultant):
    '''
        Updates Absence till when not absence anymore
        -
        :param consultant: current consultant
        :param consultants_model: consultants model
    '''
    if date.today() >= datetime.strptime(consultant.absence_till, "%Y-%m-%d").date():
        consultant.update(
            actions=[
                consultants_model.absence_till.set(None)
            ]
        )


def scheduler_start_checkin(consultant: Dict, sqs_client: Boto3SQS,
                            checkin_model: PynamoDBCheckIn,
                            reminder = False) -> None:
    '''
        Starts the scheduler
        -
        :param consultant: current consultant
        :param sqs_client: Boto3 SQS client
        :param checkin_model: PynamoDB Checkin Model
        :param reminder: is the scheduler a reminder
    '''
    checkin_action_url = os.environ['CHECKIN_ACTION_URL']

    scheduled = []
    checkins = checkin_model.consultant_uuid_date_index.query(consultant.uuid,\
        checkin_model.date <= str(datetime.today()), checkin_model.completed == 'False')
    for checkin in checkins:
        message = write_message(consultant.uuid, Types.Scheduled_Reminder,\
            checkin_id=checkin.uuid)
        scheduled.append(create_scheduled(checkin.uuid, message))

    if not reminder:
        checkin_date = date.today()
        if consultant.same_day_checkin is None or consultant.same_day_checkin == 'False':
            checkin_date = checkin_date - timedelta(max(1,(checkin_date.weekday() + 6) % 7 - 3))

        message = write_message(consultant.uuid, Types.Scheduled,\
            checkin_date=checkin_date.strftime("%Y-%m-%d"))
        scheduled.append(create_scheduled(consultant.slack_id, message))

    if len(scheduled) > 0:
        for count in range((int(len(scheduled)/10) + 1)):
            batch = scheduled[10*(count):(10*(count+1))]
            if len(batch) > 0:
                send_scheduled  = sqs_client.send_message_batch(
                    QueueUrl=checkin_action_url,
                    Entries=batch)
                print(send_scheduled)


def create_scheduled(message_id: str, message: str) -> Dict:
    '''
        create a scheduled message
        -
        :param id: message id
        :param message: message
    '''
    return {
        'Id': message_id,
        'MessageBody': 'Scheduled',
        'MessageAttributes': message,
        'MessageDeduplicationId': str(uuid.uuid4()),
        'MessageGroupId': "Scheduled"
    }
