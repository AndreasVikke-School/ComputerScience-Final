"""
    Module for converting AWS MessageAttribute to readable and usable dict
    :license: MIT
"""
import json
from typing import Dict, List

from src.modules.type_enum import Types


def load_message(attributes: List, sns: bool = False) -> Dict:
    '''
        Main function for starting the load, returns the convertet message
        -
        :param attributes: Attributes to be convertet
        :param sns=False: SQS or SNS Message
    '''
    value = {}
    for att in attributes:
        value.update(load_att(att, attributes[att], sns))

    return value


def get_type(att_type: str) -> str:
    '''
        Converts string type to enum Type
        -
        :param att_type: The string type
    '''
    att_types = {
        'scheduled': Types.Scheduled,
        'predict': Types.Predict,
        'prediction': Types.Prediction,
        'slack': Types.Slack,
        'userinput': Types.UserInput,
        'scheduled_reminder': Types.Scheduled_Reminder,
        'slack_reminder': Types.Slack_Reminder,
        'consultant_update': Types.Consultant_Update,
        'project_create' : Types.Project_Create
    }

    return att_types[att_type]


def get_data_type(att_value: Dict) -> str:
    '''
        Returns the DataType
        -
        :param att_value: The value of the key
    '''
    return att_value['dataType']


def load_att(att_name: str, att_value: Dict, sns: bool) -> Dict:
    '''
        Loads an attribute by its DataType
        -
        :param att_name: Attribute name
        :param att_value: Attribute value
        :param sns=False: Boolean SQS or SNS
    '''
    att = None
    if sns:
        if att_name == 'type':
            att = load_type_att(att_name, att_value, sns)
        elif att_name == 'payload':
            att = load_json_att(att_name, att_value, sns)
        else:
            att = load_string_att(att_name, att_value, sns)
    else:
        data_type = get_data_type(att_value)
        if data_type == 'String':
            att = load_string_att(att_name, att_value, sns)
        elif data_type == 'String.type':
            att = load_type_att(att_name, att_value, sns)
        elif data_type == 'String.json':
            att = load_json_att(att_name, att_value, sns)

    return att


def load_string_att(att_name: str, att_value: Dict, sns: bool) -> Dict:
    '''
        Loads a string attribute
        -
        :param att_name: Attribute name
        :param att_value: Attribute value
        :param sns=False: SQS or SNS
    '''
    return {att_name: att_value['Value' if sns else 'stringValue']}


def load_type_att(att_name: str, att_value: Dict, sns: bool) -> Dict:
    '''
        Loads a Type attribute
        -
        :param att_name: Attribute name
        :param att_value: Attribute value
        :param sns=False: SQS or SNS
    '''
    return {att_name: get_type(att_value['Value' if sns else 'stringValue'])}


def load_json_att(att_name: str, att_value: Dict, sns: bool) -> Dict:
    '''
        Loads a JSON attribute
        -
        :param att_name: Attribute name
        :param att_value: Attribute value
        :param sns=False: SQS or SNS
    '''
    return {att_name: json.loads(att_value['Value' if sns else 'stringValue'])}
