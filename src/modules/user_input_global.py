"""
    Processes user input global actions from slack
    :license: MIT
"""
import datetime
import json
import os
import uuid
from typing import Dict

from src.dependencies.boto3_sfn_provider import get_sfn_provider
from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.requests_provider import get_requests_provider
from src.dependencies.pynamodb_contract_provider import get_contracts_provider
from src.modules.get_export import get_export
from src.modules.private_metedata import create_metadata, read_metadata
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types

class UserInputGlobal():
    '''
        User Input Global Class
    '''

    def __init__(self, payload: Dict, test: bool = False):
        '''
            Init for class
            -
            :param payload: Payload of the event
            :param test: true for test
        '''
        self.payload = payload
        self.metadata = read_metadata(payload)
        self.sqs_client = get_sqs_provider(test)
        self.requests_client = get_requests_provider(test)
        self.checkin_model = get_checkin_provider(test)
        self.customers_model = get_customers_provider(test)
        self.consultant_model = get_consultants_provider(test)
        self.contract_model = get_contracts_provider(test)
        self.stepfunctions_client = get_sfn_provider(test)

    def get_payload_type(self):
        '''
            Get payload type
        '''
        return self.payload['type']

    def get_payload_action_type(self):
        '''
            Get payload action type
        '''
        return self.payload['actions'][0]['type']

    def send_to_sqs(self, action_id: str, action_type: str, value: str,\
            message_type: Types, consultant_uuid = None):
        '''
            Sends message to SQS
            -
            :param action_id: action id of message
            :param action_type: type of message
            :param value: value of message
        '''
        if action_type == 'checkboxes':
            value = [{'value': x['value'].split(';')[1]} for x in value]
        if action_type == 'static_select':
            value = value['value'].split(';')[1]

        message_payload = {
            "action_id": action_id,
            "type": action_type,
            "value": value
        }
        if self.metadata is not None:
            if 'current_activity' in self.metadata and\
                    self.metadata['current_activity'] is not None:
                message_payload['customer'] = self.metadata['current_activity']
            elif 'current_customer' in self.metadata and\
                    self.metadata['current_customer'] is not None:
                message_payload['customer'] = self.metadata['current_customer']

            checkin = self.checkin_model.get(self.metadata['checkin_id'])

            message = write_message(checkin.consultant_uuid, message_type,
                                checkin_id=checkin.uuid, device_id=self.payload['api_app_id'],
                                trigger_id=self.payload['trigger_id'], payload=message_payload)
        else:
            message = write_message(consultant_uuid, message_type,
                                checkin_id=None, device_id=self.payload['api_app_id'],
                                trigger_id=self.payload['trigger_id'], payload=message_payload)

        slack_app_url = get_export('checkin-action-queue-url')
        send = self.sqs_client.send_message(QueueUrl=slack_app_url,
                                    MessageBody='Slack User Input',
                                    MessageAttributes=message,
                                    MessageGroupId='UserInput',
                                    MessageDeduplicationId=str(uuid.uuid4()))
        print("SEND TO SQS:", send)
        return send

    def post(self, url: str, data: Dict):
        '''
            Posts the data
            -
            :param url: Url to slack api
            :param data: The data to post
        '''
        auth_token = os.environ['SlackAuth']
        hed = {'Authorization': 'Bearer ' + auth_token}
        response = self.requests_client.post(url, json=data, headers=hed)
        print('RESPONSE: ', response.json())
        return response

    def reader(self, checkin_id: str, name: str, current_customer: str,\
               current_activity: str = None):
        '''
            Reads the template file from templates
            -
            :param checkin_id: Checkin id from database
            :param name: The name of the file to read
            :param current_customer: The id of the current customer
            :param current_activity: Current activity if any
        '''
        print(self.metadata)
        with open("src/templates/{0}.json".format(name), "r") as body:
            body = json.load(body)
            body['private_metadata'] = create_metadata(
                checkin_id, current_customer, current_activity)
        return body

    def get_yesterday_date(self, checkin_date: datetime,\
                       current_customer: str = None, activity: bool = False):
        '''
            Creates a string with yesterdays date
            -
            :param checkin_date: Checkin date from database
            :param current_customer: Id on current customer
            :param activity: Is activity
        '''
        last_bus_day = datetime.datetime.strptime(checkin_date, '%Y-%m-%d')
        # last_bus_day = last_bus_day -\
        #     datetime.timedelta(max(1,(last_bus_day.weekday() + 6) % 7 - 3))


        if current_customer is not None:
            current_text = current_customer if activity\
                    else self.customers_model.get(current_customer).friendlyName
            return_str = '*{0} the {1}\'th of {2}*\nSpecify the hours for *{3}*'.format(
                last_bus_day.strftime("%A"), last_bus_day.day,
                last_bus_day.strftime("%B"), current_text)
        else:
            return_str = '*{0} the {1}\'th of {2}*'.format(
                last_bus_day.strftime("%A"), last_bus_day.day, last_bus_day.strftime("%B"))
        return return_str
