"""
    Processes user input block action from slack
    :license: MIT
"""
import json
from typing import Dict, List

from src.modules.private_metedata import read_metadata
from src.modules.slack_template_parts import (
    create_checkbox, create_checkboxes_with_initial_values,
    create_select_for_drop_down, create_input_box)
from src.modules.type_enum import Types
from src.modules.user_input_global import UserInputGlobal


class UserInputHandleBlockAction():
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

    def send_to_sqs(self, value, message_type: Types, action_type = None, consultant_uuid = None):
        '''
            Send message to SQS
        '''
        return self.user_input_global.send_to_sqs(
                            self.payload['actions'][0]['action_id'],
                            self.payload['actions'][0]['type']\
                                if action_type is None else action_type,
                            value,
                            message_type,
                            consultant_uuid)

    def handle_block_action(self):
        '''
            Handle block action
        '''
        if self.payload['actions'][0]['type'] == 'button':
            if self.payload['actions'][0]['value'].split(';')[0] == 'start':
                response = self.make_customers_modal()

            elif self.payload['actions'][0]['value'].split(';')[0] == 'time':
                response = self.send_to_sqs(self.payload['actions'][0]['value'].split(';')[1],\
                    Types.UserInput)
                self.update_time_view()

            elif self.payload['actions'][0]['value'].split(';')[0] == 'signup':
                response = self.make_sign_up_home_tap('signup')

        elif self.payload['actions'][0]['type'] == 'checkboxes':
            if self.payload['actions'][0]['action_id'] == 'same_day_checkin':
                response = self.make_sign_up_home_tap('same_day_checkin')
            else:
                response = self.send_to_sqs(self.payload['actions'][0]['selected_options'],\
                    Types.UserInput)

        elif self.payload['actions'][0]['type'] == 'radio_buttons':
            response = self.send_to_sqs(self.payload['actions'][0]['selected_option'],\
                    Types.UserInput)

        elif self.payload['actions'][0]['type'] == 'static_select':
            self.update_customers_modal()
            response = self.send_to_sqs(self.payload['actions'][0]['selected_option'],\
                Types.UserInput)

        elif self.payload['actions'][0]['type'] == 'timepicker':
            response = self.make_sign_up_home_tap('time_for_checkin')

        elif self.payload['actions'][0]['type'] == 'plain_text_input':
            if self.payload['actions'][0]['block_id'] == 'add_new_project_block':
                self.update_time_modal()
                response = self.send_to_sqs(self.payload['actions'][0]['value'],\
                    Types.Project_Create)
                print("Response: ", response)

        print(response)

    def make_customers_modal(self):
        '''
            Publishes the modal to the user
        '''
        checkin_id = self.payload['actions'][0]['value'].split(';')[1]
        checkin = self.user_input_global.checkin_model.get(checkin_id)
        predictions = json.loads(checkin.predictions)
        customers = sorted(self.user_input_global.customers_model.scan(),\
                        key=lambda x: x.friendlyName)

        # Load UserInput if not none
        if checkin.user_input is not None:
            user_inputs = json.loads(checkin.user_input)
        else:
            user_inputs = []

        # Load Modal view
        body = self.user_input_global.reader(checkin_id, 'modal_customer_template', None, None)

        initial_values, new_elements = create_checkboxes_with_initial_values(
            predictions, user_inputs, 'activity', 'customers', 4,\
            self.user_input_global.customers_model)

        # Append selected customers from dropdown to variables
        selected_customers = next((x for x in user_inputs if x['action_id'] == 'customers'),\
                                        {}).get('value', [])
        for selected in list(filter(lambda x: not x['unchecked'], selected_customers)):
            customer = next((x for x in customers if x.uuid == selected['value']), None)
            checkbox = create_checkbox(customer.friendlyName, 'activity', selected['value'])
            if checkbox not in new_elements:
                initial_values.append(checkbox)
                new_elements.append(checkbox)

        # Append initial_values and new_elements to body
        if initial_values is not None:
            body['blocks'][1]['elements'][0]['initial_options'] = initial_values

        print(new_elements)
        print(len(new_elements))
        if new_elements is None or len(new_elements) <= 0:
            new_elements.append(create_checkbox(customers[0].friendlyName,\
                'activity', customers[0].uuid))
        body['blocks'][1]['elements'][0]['options'] = new_elements

        # Append all customers to drop down
        exclude = list(map(lambda x: x['value'].split(';')[1], new_elements))
        all_customers_block = get_by_block_or_action_id(body['blocks'], 'all_customers')
        if all_customers_block is not None:
            all_customers_block['elements'][0]['options'] =\
                [create_select_for_drop_down(x.friendlyName,'add_customer', x.uuid)\
                    for x in list(filter(lambda x: x.uuid not in exclude, customers))]
        if len(all_customers_block['elements'][0]['options']) == 0:
            body['blocks'].pop(2)

        # Get yesterdays date to set the actual day
        body['blocks'][0]['text']['text'] = self.user_input_global.get_yesterday_date(checkin.date)

        activities = next((x for x in user_inputs if x['action_id'] == 'activity'), None)
        if activities is not None:
            initial_values = [create_checkbox(x['value'], 'activity', x['value'])\
                for x in activities['value'] if not x['unchecked']]
            if len(initial_values) > 0:
                next((x for x in body['blocks'] if 'block_id' in x\
                        and x['block_id'] == 'activities'),\
                    {})['elements'][0]['initial_options'] = initial_values

        print(body)
        return self.user_input_global.post('https://slack.com/api/views.open', {
                "trigger_id": self.payload['trigger_id'],
                "view": body
            })

    def update_time_view(self):
        '''
            Updates the current view on a modal
        '''
        checkin_id = self.metadata['checkin_id']
        checkin = self.user_input_global.checkin_model.get(checkin_id)
        body = self.user_input_global.reader(checkin_id, 'modal_time_template',\
                self.metadata['current_customer'], self.metadata['current_activity'])
        body['blocks'] = self.payload['view']['blocks']

        value = self.payload['actions'][0]['value']
        if value is not None:
            for button in body['blocks'][1]['elements']:
                if button['value'] == value:
                    button['style'] = 'primary'
                else:
                    button.pop('style', None)

        # Get yesterdays date to set the actual day
        current_text = self.metadata['current_activity'] if self.metadata['current_activity']\
            is not None else self.metadata['current_customer']
        if self.metadata['current_customer'] is not None:
            body['blocks'][0]['text']['text'] =\
                    self.user_input_global.get_yesterday_date(checkin.date,\
                        current_text, self.metadata['current_activity'] is not None)

        data = {
            "view_id": self.payload['view']['id'],
            "view": body
        }
        print('DATA FROM BUTTON PRESSED: ', json.dumps(data))
        return self.user_input_global.post('https://slack.com/api/views.update', data)

    def update_customers_modal(self) -> Dict:
        '''
            Update the customer modal
        '''
        checkin_id = self.metadata['checkin_id']
        body = self.user_input_global.reader(checkin_id, 'modal_customer_template', None, None)
        body['blocks'] = self.payload['view']['blocks']
        selected_option = self.payload['actions'][0]['selected_option']

        checkbox = create_checkbox(selected_option['text']['text'], 'activity',\
                                selected_option['value'].split(';')[1])
        if 'initial_options' not in body['blocks'][1]['elements'][0]:
            body['blocks'][1]['elements'][0]['initial_options'] = []
        body['blocks'][1]['elements'][0]['initial_options'].append(checkbox)
        body['blocks'][1]['elements'][0]['options'].append(checkbox)
        data = {
            "view_id": self.payload['view']['id'],
            "view": body
        }
        print('DATA FROM BUTTON PRESSED: ', json.dumps(data))
        return self.user_input_global.post('https://slack.com/api/views.update', data)

    def update_time_modal(self):
        '''
            Update the time modal.
        '''
        checkin_id = self.metadata['checkin_id']
        body = self.user_input_global.reader(checkin_id, 'modal_time_template',\
                self.metadata['current_customer'], self.metadata['current_activity'])
        body['blocks'] = self.payload['view']['blocks']
        index = len(self.payload['view']['blocks']) - 3
        print("index length: ", index)
        block_builder = {
            "type": "input",
            "optional": True,
            "element": {
                "type": "plain_text_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter time and description (Format H.M desc)"
                }
            },
            "label": {
                "type": "plain_text",
                "text": self.payload['actions'][0]['value'],
                "emoji": True
            }
        }
        block_builder['element'] = create_input_box(self.metadata['current_customer'],\
             'time_desc_input', None, False, project = self.payload['actions'][0]['value'])
        body['blocks'].insert(index, block_builder)
        print("BUTTON PRESSED!: ", self.payload)
        print("METADATA!!!: ", self.metadata)
        data = {
            "view_id": self.payload['view']['id'],
            "view": body
        }
        print('DATA FROM BUTTON PRESSED: ', json.dumps(data))
        return self.user_input_global.post('https://slack.com/api/views.update', data)

    def make_sign_up_home_tap(self, action_type: str):
        '''
            Makes the new Home Page Tap for singedup users
            -
            :param action_type: type of home page action
        '''
        user_id = self.payload['user']['id']
        consultant = next(self.user_input_global.consultant_model.slack_id_index.query(user_id),\
                None)
        if action_type == 'signup':
            response = self.send_to_sqs(user_id, Types.Consultant_Update, 'sign_up', "None")
        elif action_type == 'time_for_checkin':
            response = self.send_to_sqs(self.payload['actions'][0]['selected_time'],\
                Types.Consultant_Update, 'checkin_time', consultant.uuid)
        elif action_type == 'same_day_checkin':
            response = self.send_to_sqs(str(len(self.payload['actions'][0]['selected_options'])\
                > 0), Types.Consultant_Update, 'checkin_time', consultant.uuid)

        print(response)
        return "Saved To Consultant"

def get_by_block_or_action_id(blocks: List, block_action_id: str, return_type = None):
    '''
        Get block by block id or action id
        -
        :param blocks: array to look in
        :param block_action_id: block or action id
        :param return_type: the return type if not found
    '''
    output = next((x for x in blocks if 'block_id' in x and x['block_id']\
        == block_action_id), return_type)
    if output is None or not output or output == return_type:
        output = next((x for x in blocks if 'action_id' in x and x['action_id']\
            == block_action_id), return_type)
    return output
