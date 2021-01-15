"""
    Get Slack User statutes each minute
    :license: MIT
"""
import datetime
import json
import os
from typing import Dict

from pynamodb.exceptions import DoesNotExist

from src.dependencies.dependency_typing import (PynamoDBConsultant,
                                                PynamoDBOnlineStatuses,
                                                Requests)
from src.dependencies.pynamodb_consultant_provider import \
    get_consultants_provider
from src.dependencies.pynamodb_online_statuses_provider import \
    get_online_statuses_provider
from src.dependencies.requests_provider import get_requests_provider


def get(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda Context
    '''
    consultants_model = get_consultants_provider()
    online_status_model = get_online_statuses_provider()
    requests_client = get_requests_provider()

    run(event, context, consultants_model, online_status_model, requests_client)


def run(event: Dict, context, consultants_model: PynamoDBConsultant,
        online_status_model: PynamoDBOnlineStatuses,
        requests_client: Requests) -> None:
    '''
        Function for running the status getter
        -
        :param event: AWS event
        :param context: AWS Lambda Context
        :param consultants_model: PynamoDB Consultants Model
        :param online_status_model: PynamoDB Online Statuses Model
        :param requests_client: Requests Client
    '''
    print("context:", context)
    print("event", event)

    consultants = consultants_model.scan()

    for consultant in consultants:
        slack_status = get_status(consultant.slack_id, requests_client).content
        status = {
            "time": str(datetime.datetime.now()),
            "status": json.loads(slack_status)['presence']
        }
        print(slack_status)
        try:
            found_status = online_status_model.get(hash_key=consultant.uuid,
                                                   range_key=str(datetime.date.today()))
            user_status = json.loads(found_status.statuses)
            sorted_user_status = sorted(
                user_status, key=lambda x: x['time'], reverse=True)
            print(sorted_user_status)
            if sorted_user_status[0]['status'] != status['status']:
                user_status.append(status)
                found_status.update(
                    actions=[
                        online_status_model.statuses.set(
                            json.dumps(user_status))
                    ]
                )
        except DoesNotExist:
            new_status = online_status_model(consultant_uuid=consultant.uuid,
                                             date=str(datetime.date.today()),
                                             statuses=json.dumps([status]))
            new_status.save()


def get_status(slack_id: str, requests_client: Requests) -> Requests:
    '''
        Function for getting user status from slack
        -
        :param slack_id: id of the user
        :param requests_client: Requests client
    '''
    auth_token = os.environ['SlackAuth']
    hed = {'Authorization': 'Bearer ' + auth_token}

    url = 'https://slack.com/api/users.getPresence?user={0}'.format(slack_id)
    return requests_client.get(url, headers=hed)
