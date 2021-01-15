"""
This is a lambda function that consumes a message from the CheckInActionQueue
and creates a "null" consultant in the database.

:license: MIT
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Tuple, Union

from src.dependencies.boto3_sfn_provider import get_sfn_provider
from src.dependencies.boto3_sns_provider import get_sns_provider
from src.dependencies.dependency_typing import (Boto3SFN, Boto3SNS,
                                                PynamoDBCheckIn,
                                                PynamoDBConsultant,
                                                PynamoDBCustomers,
                                                PynamoDBContract,
                                                Requests)
from src.dependencies.pynamodb_checkin_provider import get_checkin_provider
from src.dependencies.pynamodb_consultant_provider import get_consultants_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.pynamodb_contract_provider import get_contracts_provider
from src.dependencies.requests_provider import get_requests_provider
from src.modules.get_export import get_export
from src.modules.queue_message_loader import load_message
from src.modules.queue_message_writer import write_message
from src.modules.type_enum import Types
from src.modules.sign_up import sign_up

def con(event, context):
    '''
        SQS Consume Handler

        :param event: AWS event
        :param context: AWS Lambda context
    '''
    checkin_model = get_checkin_provider()
    consultant_model = get_consultants_provider()
    sns_client = get_sns_provider()
    stepfunctions_client = get_sfn_provider()
    request_client = get_requests_provider()
    customer_model = get_customers_provider()
    contract_model = get_contracts_provider()
    checkin_consumer(event, context, sns_client,
                     stepfunctions_client, checkin_model,
                     consultant_model, request_client,
                     customer_model, contract_model)


def checkin_consumer(event: Dict, context, sns_client: Boto3SNS, stepfunctions_client: Boto3SFN,\
    checkin_model: PynamoDBCheckIn, consultant_model: PynamoDBConsultant,\
    request_client: Requests, customer_model: PynamoDBCustomers, contract_model: PynamoDBContract)\
    -> Union[Tuple[Boto3SNS, Boto3SFN], PynamoDBCheckIn]:
    '''
        consumes message from SQS, and depending on which type the message is, a function is called.
        :param event: AWS event. dictionary that contains all the information recieved.
        :param context: AWS Lambda context
        :param sns_client: boto3 client for Simple Notification Server.
        :param stepfunctions_client: boto3 client for stepfunctions.
        :param checkin_model: PynamoDB CheckIn Model
        :param customer_model: PynamoDB Customer Model
        :param contract_model: PynamoDB Contract Model
    '''
    print("Request ID: ", context)
    print("Event: ", event)
    # Create checkin
    message = load_message(event['Records'][0]['messageAttributes'])
    unique_id = str(uuid.uuid4())
    print("Message: ", message)
    result = None
    if message['type'] == Types.Scheduled or message['type'] == Types.Scheduled_Reminder:
        scheduled(message, unique_id, sns_client,
                           stepfunctions_client, checkin_model)
    elif message['type'] == Types.Prediction:
        result = prediction(message, checkin_model)
    elif message['type'] == Types.UserInput:
        result = user_input(message, checkin_model, consultant_model)
    elif message['type'] == Types.Consultant_Update:
        result = consultant_update(message, consultant_model, request_client)
    elif message['type'] == Types.Project_Create:
        result = add_projects(message, customer_model, contract_model)
    return result


def scheduled(message: Dict, unique_id: str, sns_client: Boto3SNS,
              stepfunctions_client: Boto3SFN, checkin_model: PynamoDBCheckIn)\
                  -> Tuple[Boto3SNS, Boto3SFN]:
    '''
        Method for scheduled action. Saves "null" checkin in database
        and publish message to prediction queue.
        -
        :param message: The message from start "event" e.g. message will be received at 9am.
        :param unique_id: Unique id for checkin in database.
        :param sns_client: boto3 client for Simple Notification Server.
        :param stepfunctions_client: boto3 client for stepfunctions.
        :param checkin_model: PynamoDB CheckIn Model
    '''
    prediction_arn = get_export('predict-topic-arn')
    times_up_machine = os.environ['TIMES_UP_MACHINE']
    reminder = 'checkin-id' in message

    if not reminder:
        checkin_date = datetime.strptime(message['checkin-date'], '%Y-%m-%d').date()

        checkin = checkin_model(uuid=unique_id,
                                consultant_uuid=message['consultant'],
                                date=str(checkin_date), completed='False',
                                predictions='[]', user_input='[]')
        # Write the checkin to the database
        checkin.save()

        # Send message to predict
        sns_pub = sns_client.publish(
            TopicArn=prediction_arn,
            Message='Ready for prediction',
            MessageAttributes=write_message(
                message['consultant'], Types.Predict, checkin_id=unique_id)
        )
        print(sns_pub)

    # Start TimesUp
    start = stepfunctions_client.start_execution(
        stateMachineArn=times_up_machine,
        input=json.dumps(write_message(
            message['consultant'], Types.Slack if not reminder else Types.Slack_Reminder,\
                checkin_id=unique_id if not reminder else message['checkin-id']))
    )
    print(start)


def prediction(message: Dict, checkin_model: PynamoDBCheckIn) -> PynamoDBCheckIn:
    '''
        Method for prediction action. Updates "null" checkin in database
        and sends message to slack app queue.
        -
        :param message: The message with predictions need for updating user predicitons i database.
        :param checkin_model: PynamoDB CheckIn Model
    '''
    user = checkin_model.get(message['checkin-id'])
    user_predictions = json.loads(user.predictions)
    if isinstance(message['payload'], list):
        for mes in message['payload']:
            user_predictions.append(mes)
    else:
        user_predictions.append(message['payload'])
    user.update(
        actions=[
            checkin_model.predictions.set(json.dumps(user_predictions))
        ]
    )
    return user


def user_input(message: Dict, checkin_model: PynamoDBCheckIn,\
               consultant_model: PynamoDBConsultant) -> PynamoDBCheckIn:
    '''
        Method for user input. Updates checkin in database
        with user inputs from slack.
        -
        :param message: The message with user input needed for updating database.
        :param checkin_model: PynamoDB CheckIn Model
    '''
    user = checkin_model.get(message['checkin-id'])
    incoming = message['payload']['value']
    current = get_current(user)
    actions = list(filter(lambda x: x['action_id'] == message['payload']['action_id'], current))
    if message['payload']['type'] == 'checkboxes':
        if len(actions) == 0:
            create_checkbox_template(message, current, actions)
        add_customers(actions, incoming)
        save_to_user(user, checkin_model, current)
    elif message['payload']['type'] == 'radio_buttons':
        incoming = incoming['value'].split(';')[1]
        if len(actions) == 0:
            create_template_other(message, incoming, current)
        else:
            actions[0]['value'] = incoming
        save_to_user(user, checkin_model, current)
    elif message['payload']['type'] == 'button' or message['payload']['type'] == 'input':
        new_actions = list(
            filter(lambda x: x['customer'] == message['payload']['customer'], actions))
        if len(new_actions) > 0:
            new_actions[0]['value'] = incoming
        else:
            create_template_other(message, incoming, current)

        if message['payload']['action_id'] == 'absence_to_date':
            consultant = consultant_model.get(user.consultant_uuid)
            consultant.update(
                actions=[
                    consultant_model.absence_till.set(message['payload']['value'])
                ]
            )

        save_to_user(user, checkin_model, current)
    return user

def consultant_update(message: Dict, consultant_model: PynamoDBConsultant,\
        request_client: Requests) -> PynamoDBCheckIn:
    '''
        Method for user input. Updates checkin in database
        with user inputs from slack.
        -
        :param message: The message with user input needed for updating database.
        :param checkin_model: PynamoDB CheckIn Model
        :param request_client: Request Client
    '''
    if message['payload']['type'] == 'sign_up':
        response = sign_up(message['payload']['value'], request_client,\
                            consultant_model)
    elif message['payload']['type'] == 'checkin_time':
        consultant = consultant_model.get(message['consultant'])
        if message['payload']['action_id'] == 'time_for_checkin':
            consultant.update(
                actions=[
                    consultant_model.time_for_checkin.set(message['payload']['value'])
                ]
            )
        elif message['payload']['action_id'] == 'same_day_checkin':
            consultant.update(
                actions=[
                    consultant_model.same_day_checkin.set(message['payload']['value'])
                ]
            )
        response = "Consultant updated with ({0})".format(message['payload']['value'])
    else:
        response = "Unkown Type"

    return response

def get_current(user: PynamoDBCheckIn) -> list:
    '''
        Method to get the value of current. if user has a value in the database it
        returns the string and deserializes to a Python Object. If user does not have any values
        in the database current returns an empty list.
        :param user: PynamoDB CheckIn Model for a single user.
    '''
    if user.user_input is not None:
        current = json.loads(user.user_input)
    else:
        current = []
    return current


def save_to_user(user: PynamoDBCheckIn, checkin_model: PynamoDBCheckIn, current: list) -> None:
    '''
        Updates the user's user_input field to contain current. Current must contain valid JSON
        to be saved to the current user.
        :param user: PynamoDB CheckIn Model for a single user.
        :param checkin_model: PynamoDB CheckIn Model.
        :param current: list with dictionaries.
    '''
    user.update(
        actions=[
            checkin_model.user_input.set(json.dumps(current))
        ]
    )


def create_template_other(message: Dict, incoming: Dict, current: list) -> None:
    '''
        creates the template for types that are not checkboxes. Currently supports
        type button and type input.
        :param message: The message with user input needed for updating database.
        :param incoming: incoming data from Slack.
        :param current: list with dictionaries.
    '''
    action_id = message['payload']['action_id']
    create_template = {'action_id': action_id, 'value': incoming,\
    'customer': message['payload']['customer']}
    current.append(create_template)


def create_checkbox_template(message: Dict, current: list, actions: list) -> None:
    '''
        creates the template for checkboxes. Appends to actions as well since this template
        is the first to be created.
        :param message: The message with user input needed for updating database.
        :param current: An empty list.
        :param actions: a filtered list with all values associated with an action_id
    '''
    create_template = {'action_id': message['payload']['action_id'], 'value': []}
    current.append(create_template)
    actions.append(create_template)


def add_customers(actions: list, incoming: Dict) -> None:
    '''
        goes through all customers to check if customer already in database.
        if a customer is not already in the database, it is added.
        if it was previously in the database, customer gets softdeleted.
        if a customer has been softdeleted but is added again, the softdelete is removed.
        :param actions: a filtered list with all values associated with an action_id
        :param incoming: incoming data from Slack.
    '''
    db_customers = list(map(lambda x: x['value'], actions[0]['value']))
    incoming_customers = list(map(lambda x: x['value'], incoming))
    for customer in actions[0]['value']:
        if customer['value'] in incoming_customers:
            customer['unchecked'] = False
        else:
            customer['unchecked'] = True
    for inc in incoming:
        if inc['value'] not in db_customers:
            temp = {
                'value': inc['value'],
                'unchecked': False
            }
            actions[0]['value'].append(temp)

def add_projects(message: Dict, customer_model: PynamoDBCustomers,\
    contract_model: PynamoDBContract) -> None:
    '''
        adds a new project to the database.
        -
        :param message: The message with user input needed for updating database.
        :param customer_model: PynamoDB Customer Model
        :param contract_model: PynamoDB Contract Model
    '''
    customer = customer_model.get(message['payload']['customer'])
    contract = next(contract_model.customerId_index.query(customer.registrationNo), None)
    print("Add Project Customer: ", customer)
    print("Add Project Contract: ", contract)
    print("Value: ", message['payload']['value'])
    projects = json.loads(contract.projects)
    project = {
        'name' : message['payload']['value'],
        'active' : True
    }
    projects.append(project)
    if contract is not None:
        contract.update(
            actions=[
                contract_model.projects.set(json.dumps(projects))
            ]
        )
    return contract
