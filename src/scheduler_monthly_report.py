"""
    Scheduler Service for starting flow
    :license: MIT
"""
import calendar
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
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    print("context:", context)
    print("event", event)

    checkin_model = get_checkin_provider()
    consultants_model = get_consultants_provider()
    customers_model = get_customers_provider()
    requests_client = get_requests_provider()

    run_scheduler(checkin_model, consultants_model, customers_model, requests_client)

def run_scheduler(checkin_model: PynamoDBCheckIn, consultants_model: PynamoDBConsultant,
                  customers_model: PynamoDBCustomers, requests_client: Requests) -> None:
    '''
        Runs Scheduler Services
        -
        :param checkin_model: Checkin model
        :param consultants_model: Consultant model
        :param customers_model: Customer model
        :param requests_client: Request client
    '''
    auth_token = os.environ['SlackAuth']
    hed = {'Authorization': 'Bearer ' + auth_token}

    today = datetime.datetime.today()
    first_date = datetime.datetime(today.year, today.month, 1) - datetime.timedelta(days=1)
    last_date = datetime.datetime(today.year, today.month,\
                                  calendar.monthrange(today.year, today.month)[1])


    consultants_list = list(consultants_model.scan())
    customers_list = list(customers_model.scan())
    checkins_list = list(checkin_model.scan(checkin_model.date.between(str(first_date),\
                         str(last_date)) & (checkin_model.completed == 'True')))

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
        print("Cust_time: ", cust_time)
        report = '{0}:'.format(today.strftime("%B"))
        for key in cust_time:
            report += '\n• {0} - {1} h'.format(key, (cust_time[key]))

        data = {
            "channel": con.slack_id,
            "text": report
        }
        requests_client.post('https://slack.com/api/chat.postMessage', json=data, headers=hed)
