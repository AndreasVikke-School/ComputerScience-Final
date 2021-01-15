"""
    Scheduler Service for weekly report
    :license: MIT
"""
import datetime
import json
import os

from src.dependencies.dependency_typing import (PynamoDBCheckIn,
                                                PynamoDBConsultant,
                                                PynamoDBCustomers, Requests)
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.requests_provider import get_requests_provider


def pub(event, context):
    '''
        AWS Serverless Handler

        :param event: AWS event
        :param context: AWS Lambda context

    '''
    print("Context: ", context)
    print("Event: ", event)

    checkin_model = get_checkin_provider()
    consultant_model = get_consultants_provider()
    customer_model = get_customers_provider()
    requests = get_requests_provider()
    create_report(checkin_model, consultant_model, customer_model, requests)

def create_report(checkin_model: PynamoDBCheckIn, consultant_model: PynamoDBConsultant,
            customer_model: PynamoDBCustomers, requests: Requests) -> None:
    '''
        Runs Scheduler Services
        -
        :param checkin_model: Checkin model
        :param consultant_model: Consultant model
        :param customer_model: Customer model
        :param requests: Request client
    '''
    auth_token = os.environ['SlackAuth']
    hed = {'Authorization': 'Bearer ' + auth_token}

    today = datetime.datetime.today()
    last_week = (today - datetime.timedelta(weeks=1)).date()

    consultants_list = list(consultant_model.scan())
    customers_list = list(customer_model.scan())
    checkins_list = list(checkin_model.scan(checkin_model.date.between(str(last_week),\
                         str(today)) & (checkin_model.completed == 'True')))

    for con in consultants_list:
        con_data = list(filter(lambda x: con.uuid == x.consultant_uuid, checkins_list))
        cust_time = {}
        for data in con_data:
            customers = next((x for x in json.loads(data.user_input) if\
                              x['action_id'] == 'customers'), None)
            if customers is not None:
                customers = list(filter(lambda x: not x['unchecked'], customers['value']))
                times = [x for x in json.loads(data.user_input)\
                         if x['action_id'].startswith('time_desc_input')]
                for cust in customers:
                    time = next((z for z in times if z['customer'] == cust['value']), None)
                    if time is not None:
                        name = next((c for c in customers_list if\
                                     c.uuid == cust['value']), None).friendlyName
                        cust_time[name] = cust_time.get(name, 0) + time['value']['time']
        report = 'Week {0}:'.format(today.strftime("%V"))
        for key in cust_time:
            report += '\n• {0} - {1} h'.format(key, (cust_time[key]))

        data = {
            "channel": con.slack_id,
            "text": report
        }
        requests.post('https://slack.com/api/chat.postMessage', json=data, headers=hed)
