"""
    Slack Queue Publisher Service for stepfunction
    :license: MIT
"""
from typing import Dict

from src.dependencies.boto3_sqs_provider import get_sqs_provider
from src.dependencies.dependency_typing import Boto3SQS
from src.modules.get_export import get_export


def pub(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda context
    '''
    sqs_client = get_sqs_provider()

    publisher(event, context, sqs_client)


def publisher(event: Dict, context, sqs_client: Boto3SQS) -> None:
    '''
        Publishes to Slack App Queue
        -
        :param event: AWS event
        :param context: AWS context
        :param sqs_client: Boto3 SQS client
    '''
    print("Request ID: ", context.aws_request_id)
    print("Event: ", event)

    slack_app_queue_url = get_export('slack-app-queue-url')
    send_message = sqs_client.send_message(
        QueueUrl=slack_app_queue_url,
        MessageBody='Prediction done',
        MessageAttributes=event
    )
    print(send_message)
