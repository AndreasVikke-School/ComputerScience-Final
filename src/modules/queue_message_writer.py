"""
    Module for creating AWS MessageAttribute
    :license: MIT
"""
import json
from typing import Dict

from src.modules.type_enum import Types


def write_message(consultant: str, mes_type: Types, checkin_id: str = None,
                  device_id: str = None, trigger_id: str = None,\
                  payload: Dict = None, checkin_date: str = None) -> Dict:
    '''
        Main function for starting the write, returns the message
        -
        :param consultant: The consultant email
        :param mes_type: The type of message
        :param checkin_id=None: The id of the checkin
        :param device_id=None: The id of the device
        :param payload=None: The payload as a dict
    '''
    if not isinstance(mes_type, Types):
        raise Exception("Type has to be one of Types")

    mes = {}
    mes.update(create_attribute("consultant", consultant, "String"))
    mes.update(create_attribute("type", mes_type.name.lower(), "String.type"))

    if checkin_id is not None:
        mes.update(create_attribute("checkin-id", checkin_id, "String"))

    if device_id is not None:
        mes.update(create_attribute("device-id", device_id, "String"))

    if trigger_id is not None:
        mes.update(create_attribute("trigger-id", trigger_id, "String"))

    if checkin_date is not None:
        mes.update(create_attribute("checkin-date", checkin_date, "String"))

    if payload is not None:
        mes.update(create_attribute(
            "payload", json.dumps(payload), "String.json"))

    return mes


def create_attribute(name: str, value: str, data_type: str) -> Dict:
    '''
        Creates a attribute for the message
        -
        :param name: The name og the attribute
        :param value: The value of the attribute
        :param data_type: The data type of the attribute
    '''
    return {
        name: {
            "StringValue": value,
            "DataType": data_type
        }
    }
