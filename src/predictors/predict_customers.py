"""
    Predict Customers for User
    :license: MIT
"""
import datetime
import json
import os
import uuid
from typing import Dict

from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.dependency_typing import (Boto3SQS, PynamoDBCheckIn,
                                                PynamoDBContract,
                                                PynamoDBCustomers, PynamoDBWeights)
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_contract_provider import get_contracts_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.pynamodb_weights_provider import get_weights_provider
from src.modules.queue_message_loader import load_message
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types


def sub(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    sqs_client = get_sqs_provider()
    customers_model = get_customers_provider()
    checkin_model = get_checkin_provider()
    contract_model = get_contracts_provider()
    weights_model = get_weights_provider()

    make_prediction(event, context, sqs_client, customers_model,\
                    checkin_model, contract_model, weights_model)


def make_prediction(event: Dict, context, sqs_client: Boto3SQS,\
                    customers_model: PynamoDBCustomers, checkin_model: PynamoDBCheckIn,
                    contract_model: PynamoDBContract, \
                    weights_model: PynamoDBWeights) -> None:
    '''
        Subscribes to SNS Topic to predict standup hints
        -
        :param event: AWS event
        :param context: AWS Lambda context
        :param sqs_client: Boto3 SQS client
        :param customers_model: Customer pynamodb
        :param checkin_model: CheckIn pynamodb
        :param contract_model: Contract pynamodb
        :param weights_model: Weights pynamodb
    '''
    print("Request ID:", context)
    print("event", event)

    attributes = load_message(
        event['Records'][0]['Sns']['MessageAttributes'], True)

    if ('type' not in attributes) or (attributes['type'] != Types.Predict):
        print('Type not found')

    date = checkin_model.get(attributes['checkin-id']).date
    date_datetime = datetime.datetime.strptime(date, '%Y-%m-%d')

    customers = customers_model.scan()
    weights = weights_model.scan()
    checkins = list(checkin_model.scan(checkin_model.date.between(\
                                       str(date_datetime - datetime.timedelta(days=3)),\
                                       str(date_datetime - datetime.timedelta(days=1))) &\
                                       (checkin_model.consultant_uuid == attributes['consultant'])&\
                                       (checkin_model.completed == 'True')))

    weights = {
        "default": next((x.value for x in weights if x.name == 'default'), 1),
        "active_contract": next((x.value for x in weights if x.name == 'active_contract'), 5),
        "active_consultant": next((x.value for x in weights if x.name ==\
                                  'active_contract_for_consultant'), 10),
        "yesterday": next((x.value for x in weights if x.name == 'yesterday'), 3),
        "two_days_ago": next((x.value for x in weights if x.name == 'two_days_ago'), 2),
        "email_sent": next((x.value for x in weights if x.name == 'email_sent'), 10),
        "email_received": next((x.value for x in weights if x.name == 'email_received'), 5)
    }


    entries = []
    for customer in customers:
        print("Customer: ", customer)
        print("CustomerId: ", customer.uuid)
        weight = weights['default']

        active_contracts = list(contract_model.scan((contract_model.customerId ==\
                                                    int(customer.registrationNo)) &\
                                                    (contract_model.active == 'True')))

        if active_contracts:
            for contract in active_contracts:
                weight *= weights['active_contract']
                consultant = list(filter(lambda x: x['uuid'] == attributes['consultant'],\
                                         json.loads(contract.consultants)))
                if consultant:
                    weight *= weights['active_consultant']

        for checkin in checkins:
            weight = calc_weight(customer, checkin, date, date_datetime, weight, weights)

        entries.append(create_entrie(customer.uuid, weight))

    send_entries  = sqs_client.send_message(
        QueueUrl=os.environ['CHECKIN_ACTION_URL'],
        MessageBody='Prediction',
        MessageAttributes=write_message(attributes['consultant'], Types.Prediction,
                                            checkin_id=attributes['checkin-id'], payload=entries),
        MessageDeduplicationId=str(uuid.uuid4()).replace('-', '_'),
        MessageGroupId='Prediction')
    print(send_entries)


def calc_weight(customer, checkin: Dict, date: str,
                date_datetime: datetime, weight: int, weights: Dict) -> int:
    '''
        Subscribes to SNS Topic to predict standup hints
        -
        :param checkin: Consultant checkin for the given day
        :param date: Checkin date as string
        :param date_datetime: Checkin date as datetime object
        :param weight: Weight for customer
        :param weights: Weight dict
    '''
    customers = next((x for x in json.loads(checkin.user_input) if\
                              x['action_id'] == 'customers'), None)
    print("customers: ", customers)
    if customers is not None:
        date = datetime.datetime.strptime(checkin.date, '%Y-%m-%d')
        for val in customers['value']:
            if customer.uuid == val['value'] and not val['unchecked']:
                if date == (date_datetime - datetime.timedelta(days=1)):
                    weight *= weights['yesterday']
                if date == (date_datetime - datetime.timedelta(days=2)):
                    weight *= weights['two_days_ago']
    return weight


def create_entrie(customer: str, weight: int) -> Dict:
    '''
        Creates an entrie for sending in message batch
        -
        :param customer: customer id
        :param weight: customer weight
    '''
    payload = {
        "header": {
            "prediction-type": "activity",
            "posibility": weight,
            "source": "geofencing"
        },
        "body": {
            "type": "customer",
            "customer": "",
            "project": "Project Alpha",
            "starttime": None,
            "endtime": None,
            "description": "Description"
        }
    }
    payload['body']['customer'] = customer

    return payload
