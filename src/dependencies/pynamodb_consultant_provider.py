# pylint: disable=R0201
"""
    PynamoDB Consultants Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock

from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import PynamoDBConsultant
from src.models.model_consultants import ConsultantsModel


class ConsultantsProvider(Module):
    """
        PynamoDB Consultants Normal dependency
    """
    @singleton
    @provider
    def provide_consultants_model(self) -> PynamoDBConsultant:
        '''
            Returns real Consultants client
        '''
        return ConsultantsModel


class ConsultantsProviderTest(Module):
    """
        PynamoDB Consultants Test dependency
    """
    @singleton
    @provider
    def provide_consultants_model(self) -> PynamoDBConsultant:
        '''
            Returns fake Consultants client (Mock object)
        '''
        consultants = [
            Mock(uuid="BehaveTest1", email="behave1@efio.dk",
                 slack_id="BehaveSlackId1"),
            Mock(uuid="BehaveTest2", email="behave2@efio.dk",
                 slack_id="BehaveSlackId2"),
            Mock(uuid="BehaveTest3", email="behave3@efio.dk",
                 slack_id="BehaveSlackId3")
        ]
        mock_obj = Mock()
        mock_obj.scan.return_value = consultants
        mock_obj.get.return_value = consultants[0]
        mock_obj.email_index.query.return_value = iter([])
        mock_obj.slack_id_index.query.return_value = iter([])
        return mock_obj


def get_consultants_provider(test=False):
    '''
        Returns Consultants client based on enviroment
    '''
    if test:
        injector = Injector([ConsultantsProvider(), ConsultantsProviderTest()])
    else:
        injector = Injector(ConsultantsProvider())
    return injector.get(PynamoDBConsultant)
