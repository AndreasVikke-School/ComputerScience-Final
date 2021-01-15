# pylint: disable=R0201
"""
    PynamoDB Contracts Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock

from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import PynamoDBContract
from src.models.model_contract import ContractModel


class ContractProvider(Module):
    """
        PynamoDB Contracts Normal dependency
    """
    @singleton
    @provider
    def provide_contract_model(self) -> PynamoDBContract:
        '''
            Returns real Contracts client
        '''
        return ContractModel


class ContractsProviderTest(Module):
    """
        PynamoDB Contracts Test dependency
    """
    @singleton
    @provider
    def provide_contracts_model(self) -> PynamoDBContract:
        '''
            Returns fake Contracts client (Mock object)
        '''
        mock_obj = Mock()
        return mock_obj


def get_contracts_provider(test=False):
    '''
        Returns Contracts client based on enviroment
    '''
    if test:
        injector = Injector([ContractProvider(), ContractsProviderTest()])
    else:
        injector = Injector(ContractProvider())
    return injector.get(PynamoDBContract)
