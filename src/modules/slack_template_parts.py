"""
    Slack Template Parts Creation Libary
    :license: MIT
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pytz
from src.dependencies.dependency_typing import PynamoDBCustomers


def create_checkboxes_with_initial_values(predictions: List, user_inputs: List,
                                          prediction_type: str, action_id: str, top: int,\
                                          customer_model: PynamoDBCustomers) -> Tuple:
    '''
        Filters, Sorts and creates checkboxes from predictions
        -
        :param predictions: Predictions from database
        :param user_inputs: User Input database
        :param prediction_type: Prediction type to filter
        :param action_id: Action ID to filter
        :param top: Top checkboxes to make
    '''
    # Filter and Sort Predictions
    predictions = list(filter(lambda x: x['header']['prediction-type']
                              == prediction_type, predictions))
    predictions = sorted(predictions, key=lambda x: x['header']['posibility'],
                         reverse=True)

    # Filter UserInput for Action ID
    user_inputs = next((x for x in user_inputs if x['action_id'] == action_id), None)

    initial_values = None
    if user_inputs is not None:
        # Filter Selected Values by unchecked state
        initial_values_db = list(filter(lambda x: not x['unchecked'],
                                        user_inputs['value']))
        print(initial_values_db)
        if len(initial_values_db) > 0:
            initial_values = [create_checkbox(customer_model.get(x['value']).friendlyName,\
                              'activity', x['value'])
                                for x in initial_values_db]

    new_elements = [create_checkbox(customer_model.get(x['body']['customer']).friendlyName,
                                    'activity', x['body']['customer'])
                    for x in predictions[:top]]

    return initial_values, new_elements


def create_checkbox(text: str, checkbox_type: str, value: str) -> Dict:
    '''
        Create Checkbox for Template
        -
        :param text: text for checkbox
        :param checkbox_type: type of checkbox
        :param value: value of checkbox
        :param action_id: action_id of the button
    '''
    return {
        "text": {
            "type": "mrkdwn",
            "text": text,
        },
        "value": "{0};{1}".format(checkbox_type, value)
    }

def create_select_for_drop_down(text: str, select_type: str, value: str):
    '''
        Create Select for Drop down for Template
        -
        :param text: text for select
        :param checkbox_type: type of checkbox
        :param value: value of checkbox
        :param action_id: action_id of the button
    '''
    return {
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": True
        },
        "value": "{0};{1}".format(select_type, value)
    }

def create_time_hint(starttime: str, endtime: str, source: str) -> List:
    '''
        Create Time Hint for Template
        -
        :param starttime: start time of button
        :param endtime: end time of button
        :param source: source for button
    '''
    starttime = datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S.%f').replace(
        tzinfo=timezone.utc).astimezone(pytz.timezone('Europe/Berlin'))
    endtime = datetime.strptime(endtime, '%Y-%m-%d %H:%M:%S.%f').replace(
        tzinfo=timezone.utc).astimezone(pytz.timezone('Europe/Berlin'))

    time = (endtime - starttime).seconds
    minute = time // 60 % 60

    if minute >=35:
        time += 3600 - (minute * 60)
    elif minute >=5:
        time += 1800 - (minute * 60)
    else:
        time -= minute * 60

    return '{0} h - {1}'.format(time/3600, source)


def create_hints_from_precitions(predictions: List, prediction_type: str) -> List:
    '''
        Filters, Sorts and creates hint from predictions
        -
        :param predictions: Predictions from database
        :param prediction_type: Prediction type to filter
    '''
    return_hints = []
    # Filter and sort Predicitons
    hints = list(
        filter(lambda x: x['header']['prediction-type'] == prediction_type, predictions))
    sorted_hints = sorted(
        hints, key=lambda x: x['header']['posibility'], reverse=True)

    for item in sorted_hints[:3]:
        if prediction_type == 'hint':
            return_hints.append(item['body']['message'])
        elif prediction_type == 'duration':
            return_hints.append(create_time_hint(item['body']['starttime'],\
                                                 item['body']['endtime'], item['header']['source']))

    return return_hints


def create_hint(predictions: List) -> Dict:
    '''
        Create Hint for Template
        -
        :param predictions: list of all predictions as string
    '''
    hints = create_hints_from_precitions(predictions, 'duration') +\
            create_hints_from_precitions(predictions, 'hint')
    return {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "*Hints:*\n{0}".format('\n'.join(str(hint) for hint in hints))
            }
        ]
    }


def create_button(text: str, button_type: str, value: str, action_id: str,
                  primary_style: bool = False) -> Dict:
    '''
        Create Checkbox for Template
        -
        :param text: text for button
        :param checkbox_type: type of button
        :param value: value of button
        :param action_id: action_id of the button
        :param primary_style: is the button style primary
    '''
    button = {
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": True
        },
        "action_id": action_id,
        "value": "{0};{1}".format(button_type, value)
    }

    if primary_style:
        button['style'] = 'primary'

    return button

def create_input_box(current_customer: str, action_id: str,
                     initial_value: str = None, multiline: bool = False, default: bool = False,
                     project: str = None) -> Dict:
    '''
        Create Description Box for Template
        -
        :param current_customer: current customer uuid
        :param action_id: Action ID of input box
        :param initial_value: initial value for box
        :param multiline: Multiline Input box
    '''
    input_box = None
    if default:
        input_box = {
            "type": "plain_text_input",
            "action_id": "{0}_{1}".format(action_id, current_customer),
            "multiline": multiline,
        }
    else:
        input_box = {
            "type": "plain_text_input",
            "action_id": "{0}_{1}_{2}".format(action_id, current_customer, project),
            "multiline": multiline,
        }
    if not multiline:
        input_box['placeholder'] = {
            "type": "plain_text",
            "text": "Enter time and description (Format H.M desc)"
        }
    if initial_value is not None:
        input_box["initial_value"] = initial_value
    return input_box


def create_time_block(current_customer, customer_model, contract_model):
    '''
        Creates default box container.

        :param current_customer: current customer uuid
        :param customer_model: PynamoDBCustomer
        :param contract_model: PynamoDBContract
    '''
    customer = customer_model.get(current_customer)
    contract = next(contract_model.customerId_index.query(customer.registrationNo), None)
    projects = json.loads(contract.projects)
    print("Customer: ", contract)
    print("Projects: ", projects)
    blocks = []
    print("Len of projects: ", len(projects))
    if len(projects) > 0:
        for project in projects:
            print("project in slack template parts: ", project)
            if project["active"] is True:
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
                        "text": "Default",
                        "emoji": True
                    }
                }
                block_builder["block_id"] = 'project_time_desc_{0}'.format(project['name'])
                block_builder['label']['text'] = '{0}'.format(project['name'])
                blocks.append(block_builder)
    else:
        block_builder = {
			"type": "input",
			"optional": True,
			"block_id": "default_time_desc_block",
			"element": {
				"type": "plain_text_input",
				"action_id": "time_desc_input",
				"placeholder": {
					"type": "plain_text",
					"text": "Enter time and description (Format H.M desc)"
				}
			},
			"label": {
				"type": "plain_text",
				"text": "Default",
				"emoji": True
			}
		}
        blocks.append(block_builder)
    return blocks
