# pylint: disable=R0201
"""
    Requests Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock
import requests
from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import Requests


class RequestsProvider(Module):
    """
        Requests Normal dependency
    """
    @singleton
    @provider
    def provide_requests(self) -> Requests:
        '''
            Returns real Requests client
        '''
        return requests


class RequestsProviderTest(Module):
    """
        Requests Test dependency
    """
    @singleton
    @provider
    def provide_requests(self) -> Requests:
        '''
            Returns fake Requests client (Mock object)
        '''
        response = {
            "user":{
                "profile":{
                    "email":"test@test.dk"
                }
            }
        }

        mock_obj = Mock()
        new_mock = Mock()
        new_mock.json.return_value = response
        mock_obj.get.return_value = new_mock

        return mock_obj


def get_requests_provider(test=False):
    '''
        Returns Requests client based on enviroment
    '''
    if test:
        injector = Injector([RequestsProvider(), RequestsProviderTest()])
    else:
        injector = Injector(RequestsProvider())
    return injector.get(Requests)
