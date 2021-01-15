# pylint: disable=R0201
"""
    Boto3 SNS Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock

import boto3
from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import Boto3SNS


class Boto3SNSProvider(Module):
    """
        Boto3 SNS Normal dependency
    """
    @singleton
    @provider
    def provide_boto3sns(self) -> Boto3SNS:
        '''
            Returns real Boto3 SNS client
        '''
        return boto3.client('sns')


class Boto3SNSProviderTest(Module):
    """
        Boto3 SNS Test dependency
    """
    @singleton
    @provider
    def provide_boto3sns(self) -> Boto3SNS:
        '''
            Returns fake Boto3 SNS client (Mock object)
        '''
        return Mock()


def get_sns_provider(test=False):
    '''
        Returns SNS client based on enviroment
    '''
    if test:
        injector = Injector([Boto3SNSProvider(), Boto3SNSProviderTest()])
    else:
        injector = Injector(Boto3SNSProvider())
    return injector.get(Boto3SNS)
