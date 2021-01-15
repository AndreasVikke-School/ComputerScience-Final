"""
    Processes user input block action from slack
    :license: MIT
"""
import datetime
import json
import os
from datetime import date, datetime, timedelta
from typing import Dict

from src.modules.slack_template_parts import (create_input_box, create_time_block, create_hint)
from src.modules.private_metedata import read_metadata
from src.modules.time_desc_decoder import decode_time_desc
from src.modules.type_enum import Types
from src.modules.user_input_global import UserInputGlobal


class UserInputHandleViewSubmission():
    '''
        User Input Handle Block Action Class
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
        self.user_input_global = UserInputGlobal(payload, test)

    def send_to_sqs(self, action_id, value):
        '''
            Send message to SQS
        '''
        return self.user_input_global.send_to_sqs(
                            action_id,
                            'input',
                            value,
                            Types.UserInput)

    def handle_view_submission(self):
        '''
            Handle View Submission
        '''
        checkin = self.user_input_global.checkin_model.get(self.metadata['checkin_id'])
        current_text = self.metadata['current_activity'] if self.metadata['current_activity']\
                is not None else self.metadata['current_customer']

        customer_uuid = self.metadata['current_customer']
        contract = None
        projects = []
        if customer_uuid is not None:
            customer = self.user_input_global.customers_model.get(customer_uuid)

            contract = next(self.user_input_global.contract_model.customerId_index\
                .query(customer.registrationNo), None)

            projects = json.loads(contract.projects)

        # Add pr. project
        #er der nogen projecter
        #loop hvis det er
        print("Payload: ", self.payload)
        # if contract is not None and len(json.loads(contract.projects)) == 0
        if 'default_time_desc_block' in self.payload['view']['state']['values']:
            time_desc = self.payload['view']['state']['values']['default_time_desc_block']
            if bool(time_desc):
                value = time_desc['time_desc_input_{0}'.format(
                    current_text)]['value']
                if bool(value):
                    value_decoded = decode_time_desc(value, contract.requiredDescription == 'True')
                    if value_decoded != "Decode Error":
                        response = self.send_to_sqs('time_desc_input_{0}'.format(
                                        current_text),
                                        value_decoded)
                    else:
                        return formatting_error()
                else:
                    return formatting_error()
            else:
                return formatting_error()
        else:
            completed = False
            titles = []
            for project in projects:
                project_title = 'project_time_desc_{0}'.format(project['name'])
                titles.append(project_title)
                if project_title in self.payload['view']['state']['values']:
                    time_desc = self.payload['view']['state']['values'][project_title]
                    if bool(time_desc):
                        value = time_desc['time_desc_input_{0}_{1}'.format(
                            current_text, project['name'])]['value']
                        if value is not None:
                            value_decoded = decode_time_desc(value,\
                                 contract.requiredDescription == "True")
                            if value_decoded != "Decode Error":
                                response = self.send_to_sqs('time_desc_input_{0}_{1}'.format(
                                                current_text, project['name']),
                                                value_decoded)
                                completed = True
                            else:
                                return {
                                    "response_action": "errors",
                                    "errors": {
                                        project_title: "Formatting Error"
                                    }
                                }
            if completed is False:
                for project in titles:
                    return {
                        "response_action": "errors",
                        "errors": {
                            project: "At least one project must be filled out."
                        }
                    }

        if 'absence_dates' in self.payload['view']['state']['values']:
            if self.payload['view']['state']['values']['absence_selector']\
                    ['absence_type']['selected_option'] is None:
                return {
                    "response_action": "errors",
                    "errors": {
                        "absence_selector": "No absence type selected"
                    }
                }

            absence_type = self.payload['view']['state']['values']['absence_selector']\
                    ['absence_type']['selected_option']['value'].split(';')[1]
            absence_from_date = self.payload['view']['state']['values']['absence_dates']\
                    ['absence_from_date']['selected_date']
            absence_to_date = self.payload['view']['state']['values']['absence_dates']\
                    ['absence_to_date']['selected_date']

            absence_to_date_epoch = datetime.strptime('{0}'.format(absence_to_date),\
                '%Y-%m-%d').timestamp()

            # Only use Admin for Emojie Status
            auth_token = os.environ['SlackAdminAuth']
            hed = {'Authorization': 'Bearer ' + auth_token}

            url = "https://slack.com/api/users.profile.set"
            if absence_type == "sickness":
                data = { "status_text": "Sickness", "status_emoji": ":face_with_thermometer:",\
                    "status_expiration": absence_to_date_epoch }
            else:
                data = { "status_text": "Vacation", "status_emoji": ":palm_tree:",\
                    "status_expiration": absence_to_date_epoch }
            user = self.payload['user']['id']
            response = self.user_input_global.requests_client\
                .post('{0}?profile={1}&user={2}'.format(url, data, user), headers=hed)
            print(response)

            response = self.send_to_sqs(
                'absence_from_date',
                absence_from_date)
            response = self.send_to_sqs(
                'absence_to_date',
                absence_to_date)


        # Get customer list
        customers = self.get_current_customers(checkin)
        if customers is not None:
            if self.metadata['current_customer'] is None:
                update = self.make_time_modal(customers[0], checkin)
            elif len(customers) > 1 and customers[-1] != self.metadata['current_customer']:
                current_customer_index = customers.index(
                    self.metadata['current_customer'])
                update = self.make_time_modal(customers[current_customer_index+1],\
                        checkin, update=True)
            else:
                # All Selected Customers have been run trough
                current_customer_index = customers.index(
                    self.metadata['current_customer'])
                update = self.activity_check(checkin, customers[current_customer_index])
        else:
            update = self.activity_check(checkin)

        return update

    def activity_check(self, checkin, current_customer = None):
        '''
            Checks for activities selected
            -
            :param checkin: Current checkin
            :param current_customer: Current customer
        '''
        activities = get_current_activities(checkin)
        if activities is not None and len(activities) != 0:
            print(activities)
            if self.metadata['current_activity'] is None:
                if activities[0] == 'Absence':
                    update = self.make_absence_modal(current_customer, checkin,\
                        activities[0])
                else:
                    update = self.make_time_modal(current_customer, checkin, activities[0])
            elif len(activities) > 1 and activities[-1] != self.metadata['current_activity']:
                current_activity_index = activities.index(
                    self.metadata['current_activity'])
                if activities[current_activity_index+1] == 'Absence':
                    update = self.make_absence_modal(current_customer, checkin,\
                        activities[current_activity_index+1], update=True)
                else:
                    update = self.make_time_modal(current_customer, checkin,\
                        activities[current_activity_index+1], update=True)
            else:
                update = {"response_action": "clear"}
                self.complete_checkin(checkin)
                self.user_input_global.stepfunctions_client.start_execution(
                        stateMachineArn=os.environ['SEND_RECEIPT_MACHINE'],
                        input=json.dumps({'user_id': self.payload['user']['id'],\
                            'checkin_id': self.metadata['checkin_id']})
                    )
        else:
            update = {"response_action": "clear"}
            self.complete_checkin(checkin)
            self.user_input_global.stepfunctions_client.start_execution(
                    stateMachineArn=os.environ['SEND_RECEIPT_MACHINE'],
                    input=json.dumps({'user_id': self.payload['user']['id'],\
                        'checkin_id': self.metadata['checkin_id']})
                )

        return update

    def get_current_customers(self, checkin):
        '''
            Creates customer list with checked customers
            -
            :param checkin: The current checkin of modal
        '''
        user_input = json.loads(checkin.user_input)
        customers_db = list(self.user_input_global.customers_model.scan())

        customers = next(
            (x for x in user_input if x['action_id'] == 'customers'), None)
        return_customers = []
        if customers is not None:
            return_customers = [x['value'] for x in list(filter(lambda x: not x['unchecked'],
                                                                customers['value']))]
            print(customers_db, return_customers)
            return_customers = sorted(return_customers, key=lambda x:\
                list(filter(lambda z: z.uuid == x, customers_db))[0].friendlyName)

        if len(return_customers) == 0:
            return_customers = None
        return return_customers

    def make_time_modal(self, current_customer: str, \
                        checkin, current_activity = None, update: bool = False):
        '''
            Pushes a new modal on top of the modal stack
            -
            :param current_customer: Current customer name
            :param checkin: The current checkin of modal
            :param current_activity: current activity if any
            :param update: update view or push view
        '''
        predictions = json.loads(checkin.predictions)

        # if checkin.user_input is not None:
        #     user_inputs = json.loads(checkin.user_input)
        # else:
        #     user_inputs = []

        body = self.user_input_global.reader(self.metadata['checkin_id'],\
                'modal_time_template', current_customer, current_activity)

        current_text = current_activity if current_activity is not None else current_customer

        # default_time_desc = next(
        #     (x for x in body['blocks'] if 'block_id' in x\
        #         and x['block_id'] == 'default_time_desc_block'), None)

        # default_time_desc['element'] = create_input_box(
        #     current_text, 'time_desc_input', None, False, default=True)

        time_desc = create_time_block(current_text, self.user_input_global.customers_model,\
            self.user_input_global.contract_model)
        index = 2
        if len(time_desc) == 1 and time_desc[0]['block_id'] == 'default_time_desc_block':
            block = time_desc[0]
            block['element'] = create_input_box(
                    current_text, 'time_desc_input', None, False, default=True)
            body['blocks'].insert(index, block)
        else:
            print("template: ", body)
            print("Time_desc: ", time_desc)
            for projects in time_desc:
                print("Project: ", projects)
                project_name = projects['block_id'].split('_')
                print("project name:", project_name[3])
                projects['element'] = create_input_box(current_text, 'time_desc_input', None,\
                    False, project = project_name[3])
                body['blocks'].insert(index, projects)
                index += 1
            print("Body: ", body)


        customer = self.user_input_global.customers_model.get(current_customer)
        print("customer: ", customer)

        contract = next(self.user_input_global.contract_model.customerId_index\
            .query(customer.registrationNo), None)
        print('contract: ', contract)

        # Append hints to bottom of view
        body['blocks'].append(create_hint(predictions))

        # Get yesterdays date to set the actual day
        body['blocks'][0]['text']['text'] = self.user_input_global.get_yesterday_date(
            checkin.date, current_text, current_activity is not None)

        data = {
            "response_action": "update" if update else "push",
            "view": body
        }
        return data

    def make_absence_modal(self, current_customer: str, \
                        checkin, current_activity = None, update: bool = False):
        '''
            Pushes a new modal on top of the modal stack
            -
            :param current_customer: Current customer uuid
            :param checkin: The current checkin of modal
            :param current_activity: current activity if any
            :param update: update view or push view
        '''
        if checkin.user_input is not None:
            user_inputs = json.loads(checkin.user_input)
        else:
            user_inputs = []

        body = self.user_input_global.reader(self.metadata['checkin_id'],\
                'modal_absence_template', current_customer, current_activity)

        from_date = next((x for x in user_inputs if x['action_id'] == 'absence_from_date'), None)
        to_date = next((x for x in user_inputs if x['action_id'] == 'absence_to_date'), None)
        body['blocks'][3]['elements'][0]['initial_date'] = from_date \
            if from_date is not None else str(date.today())
        body['blocks'][3]['elements'][1]['initial_date'] = to_date \
            if to_date is not None else str(date.today() + timedelta(1))

        current_text = current_activity if current_activity is not None else current_customer

        # Get yesterdays date to set the actual day
        body['blocks'][0]['text']['text'] = self.user_input_global.get_yesterday_date(
            checkin.date, current_text, current_activity is not None)

        data = {
            "response_action": "update" if update else "push",
            "view": body
        }
        return data

    def complete_checkin(self, checkin) -> None:
        '''
            Sets Completed flag to true on checkin
            -
            :param checkin: The current checkin of modal
        '''
        checkin.update(
            actions=[
                self.user_input_global.checkin_model.completed.set('True')
            ]
        )

def formatting_error():
    '''
        Returns formattion error
    '''
    return {
        "response_action": "errors",
        "errors": {
            'default_time_desc_block': "Formatting Error"
        }
    }

def get_current_activities(checkin):
    '''
        Returns curretn activites
        -
        :param checkin: Current checkin
    '''
    user_input = json.loads(checkin.user_input)
    activities = next(
        (x for x in user_input if x['action_id'] == 'activity'), None)

    if activities is not None:
        return_activities = [x['value'] for x in list(filter(lambda x: not x['unchecked'],
                                                                activities['value']))]
    else:
        return_activities = None

    return return_activities
