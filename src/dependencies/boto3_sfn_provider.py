# pylint: disable=R0201
"""
    Boto3 SFN Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock

import boto3
from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import Boto3SFN


class Boto3SFNProvider(Module):
    """
        Boto3 SFN Normal dependency
    """
    @singleton
    @provider
    def provide_boto3sfn(self) -> Boto3SFN:
        '''
            Returns real Boto3 SFN client
        '''
        return boto3.client('stepfunctions')


class Boto3SFNProviderTest(Module):
    """
        Boto3 SFN Test dependency
    """
    @singleton
    @provider
    def provide_boto3sfn(self) -> Boto3SFN:
        '''
            Returns fake Boto3 SFN client (Mock object)
        '''
        return Mock()


def get_sfn_provider(test=False):
    '''
        Returns SFN client based on enviroment
    '''
    if test:
        injector = Injector([Boto3SFNProvider(), Boto3SFNProviderTest()])
    else:
        injector = Injector(Boto3SFNProvider())
    return injector.get(Boto3SFN)
