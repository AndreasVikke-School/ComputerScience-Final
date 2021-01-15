"""
    PynamoDB Consultants Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock

from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import PynamoDBWeights
from src.models.model_weights import WeightModel


class WeightsProvider(Module):
    """
        PynamoDB Weights Normal dependency
    """
    @singleton
    @provider
    def provide_weights_model(self) -> PynamoDBWeights:
        '''
            Returns real Weights client
        '''
        return WeightModel


class WeightsProviderTest(Module):
    """
        PynamoDB Weights Test dependency
    """
    @singleton
    @provider
    def provide_weights_model(self) -> PynamoDBWeights:
        '''
            Returns fake weights client (Mock object)
        '''
        weights = [
            Mock("BehaveTest1","Base", 1),
            Mock("BehaveTest2","Active contract", 5),
            Mock("BehaveTest3","Active contract for consultant", 10),
            Mock("BehaveTest4","Yesterday", 3),
            Mock("BehaveTest5","Two days ago", 2),
            Mock("BehaveTest6","Email sent", 10),
            Mock("BehaveTest7","Email received", 5),

        ]

        mock_obj = Mock()
        mock_obj.scan.return_value = weights
        mock_obj.get.return_value = weights[0]
        mock_obj.name_index.query.return_value = iter([])
        return mock_obj


def get_weights_provider(test=False):
    '''
        Returns Weights client based on enviroment
    '''
    if test:
        injector = Injector([WeightsProvider(), WeightsProviderTest()])
    else:
        injector = Injector(WeightsProvider())
    return injector.get(PynamoDBWeights)
