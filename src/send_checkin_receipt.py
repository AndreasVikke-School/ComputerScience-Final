"""
    Send Receipt StepFunction
    :license: MIT
"""
import datetime
import json
import os

from typing import List
from src.dependencies.dependency_typing import (PynamoDBCheckIn,
                                                PynamoDBCustomers, Requests)
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.requests_provider import get_requests_provider


def send(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    print(event)
    print(context)
    checkin_model = get_checkin_provider()
    customers_model = get_customers_provider()
    requests_client = get_requests_provider()

    send_receipt(event['user_id'], event['checkin_id'], checkin_model,\
        customers_model, requests_client)

def send_receipt(user_id: str, checkin_id: str, checkin_model: PynamoDBCheckIn,\
                customers_model: PynamoDBCustomers, requests_client: Requests):
    '''
        Get receipt after end checkin
        -
        :param user_id: Slack user id
        :param checkin_id: Checkin id
        :param checkin_model: Checkin model
        :param customers_model: Customer model
        :param request_client: Request client
    '''
    checkin = checkin_model.get(checkin_id)
    customers_str = ''

    customers = next((x for x in json.loads(checkin.user_input)\
                         if x['action_id'] == 'customers'), None)
    if customers is not None:
        customers = list(filter(lambda x: not x['unchecked'], customers['value']))
        times = [x for x in json.loads(checkin.user_input)\
                if x['action_id'].startswith('time_desc_input')]
        print('Customers: ', customers)
        print('Times: ', times)
        if len(times) > 0:
            customers = [(customers_model.get(x['value']).friendlyName,\
                        list(filter(lambda z: z['customer'] == x['value'], times)))\
                        for x in customers]
            # customers = [(customers_model.get(x['value']).friendlyName,\
            #             next((z for z in times if z['customer'] == x['value']), None)['value'])\
            #             for x in customers]
            print('Customers: ', customers)
            for cust in customers:
                for proj in cust[1]:
                    print("Project: ", proj)
                    name = proj['action_id'].split('_')
                    if len(name) == 4:
                        customers_str += '\n • {0} hours for {1}'\
                            .format(proj['value']['time'], cust[0])
                    else:
                        customers_str += '\n • {0} hours for {1} at {2}'\
                            .format(proj['value']['time'], name[4], cust[0])
    elif customers is None:
        absence_type = [x for x in json.loads(checkin.user_input)\
                if x['action_id'] == 'absence_type']
        absence_start = [x for x in json.loads(checkin.user_input)\
                if x['action_id'] == 'absence_from_date']
        absence_end = [x for x in json.loads(checkin.user_input)\
                if x['action_id'] == 'absence_to_date']
        customers_str += '\n • {0} from *{1}* to *{2}*'\
                          .format(absence_type[0]['value'], absence_start[0]['value'],\
                                  absence_end[0]['value'])

    data = {
        "channel": user_id,
        "text": 'Thanks for registering for *{0}*:\n{1}'.\
                format(get_yesterday_date(checkin.date), customers_str)
    }

    hed = {'Authorization': 'Bearer ' + os.environ['SlackAuth']}

    delete_button = delete_message(user_id, requests_client, checkin.date)
    print("Delete button: ", delete_button)
    response = requests_client.post('https://slack.com/api/chat.postMessage',\
                json=data, headers=hed)
    return response

def delete_message(user_id: str, requests_client: Requests, checkin_date: str) ->  None:
    '''
        Deletes checkin button from the channel
        -
        :param user_id: str
        :param requests_client: Requests client
        :param checkin_date: Checkin Date
    '''
    channel_id = get_conversation_id(user_id, requests_client)

    timespamps = get_timestamp(channel_id, requests_client, checkin_date)
    responses = []
    hed = {'Authorization': 'Bearer ' + os.environ['SlackAuth']}
    for timestamp in timespamps:
        param = {'channel' : channel_id, 'ts' : timestamp}
        request = requests_client.get('https://slack.com/api/chat.delete',
            params=param, headers=hed)
        responses.append(request.json())
        print("Request: ", request)
        print("Response: ", request.json())
    return responses


def get_timestamp(channel_id: str, requests_client: Requests, checkin_date: str) -> List:
    '''
        Gets all timestamps in the conversation. Returns list of all timestamps
        -
        :param channel_id: str
        :param requests_client: Requests client
        :param checkin_date: Checkin Date
    '''
    hed = {'Authorization': 'Bearer ' + os.environ['SlackAuth']}
    param = {'channel' : channel_id}

    request = requests_client.get('https://slack.com/api/conversations.history',
        params=param, headers=hed)
    response = request.json()
    timestamps = []
    checkin_date = datetime.datetime.strptime(checkin_date, '%Y-%m-%d')
    # checkin_date = checkin_date -\
    #     datetime.timedelta(max(1,(checkin_date.weekday() + 6) % 7 - 3))
    print("Day: ", checkin_date.strftime("%-d"), " Month: ", checkin_date.strftime("%B"))
    date = "{0}'th of {1}".format(checkin_date.strftime("%-d"), checkin_date.strftime("%B"))
    print("Date: ", date)
    for messages in response['messages']:
        if messages['text'] == "Start Checkin":
            if date in messages['blocks'][0]['text']['text']:
                timestamps.append(messages['ts'])
    print("timestamp: ", timestamps)
    return timestamps


def get_conversation_id(user_id: str, requests_client: Requests):
    '''
        Gets conversation ID for Instant Message between user and App.
        -
        :param user_id: str
        :param requests_client: Requests client
    '''
    hed = {'Authorization': 'Bearer ' + os.environ['SlackAuth']}
    param = {'user' : user_id, 'types' : 'im'}
    request = requests_client.get('https://slack.com/api/users.conversations',
        params=param, headers=hed)
    response = request.json()
    print("user&channel ID: ", response['channels'][0]['id'])
    return response['channels'][0]['id']



def get_yesterday_date(checkin_date: datetime):
    '''
        Creates a string with yesterdays date
        -
        :param checkin_date: Checkin date from database
        :param current_customer: Name on current customer
    '''
    last_bus_day = datetime.datetime.strptime(checkin_date, '%Y-%m-%d')
    # last_bus_day = last_bus_day -\
        # datetime.timedelta(max(1,(last_bus_day.weekday() + 6) % 7 - 3))

    return '{0} the {1}\'th of {2}'.format(
        last_bus_day.strftime("%A"), last_bus_day.day, last_bus_day.strftime("%B"))
