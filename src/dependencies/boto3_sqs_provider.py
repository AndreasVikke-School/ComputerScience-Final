# pylint: disable=R0201
"""
    Boto3 SQS Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock

import boto3
from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import Boto3SNS


class Boto3SQSProvider(Module):
    """
        Boto3 SQS Normal dependency
    """
    @singleton
    @provider
    def provide_boto3sqs(self) -> Boto3SNS:
        '''
            Returns real Boto3 SQS client
        '''
        return boto3.client('sqs')


class Boto3SQSProviderTest(Module):
    """
        Boto3 SQS Test dependency
    """
    @singleton
    @provider
    def provide_boto3sqs(self) -> Boto3SNS:
        '''
            Returns fake Boto3 SQS client (Mock object)
        '''
        return Mock()


def get_sqs_provider(test=False):
    '''
        Returns SQS client based on enviroment
    '''
    if test:
        injector = Injector([Boto3SQSProvider(), Boto3SQSProviderTest()])
    else:
        injector = Injector(Boto3SQSProvider())
    return injector.get(Boto3SNS)
