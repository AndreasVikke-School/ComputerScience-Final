# pylint: disable=R0201
"""
    PynamoDB OnlineStatuses Normal and Test dependencies
    :license: MIT
"""
from datetime import date
from unittest.mock import Mock

from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import PynamoDBOnlineStatuses
from src.models.model_online_statuses import OnlineStatusesModel


class OnlineStatusesProvider(Module):
    """
        PynamoDB OnlineStatuses Normal dependency
    """
    @singleton
    @provider
    def provide_online_statuses_model(self) -> PynamoDBOnlineStatuses:
        '''
            Returns real OnlineStatuses client
        '''
        return OnlineStatusesModel


class OnlineStatusesProviderTest(Module):
    """
        PynamoDB OnlineStatuses Test dependency
    """
    @singleton
    @provider
    def provide_online_statuses_model(self) -> PynamoDBOnlineStatuses:
        '''
            Returns fake OnlineStatuses client (Mock object)
        '''
        online_statuses = [
            Mock(consultant_uuid="BehaveTest1", date=str(date.today()),
                 statuses='[{"time": "2020-09-29 07:20:08.064296", "status": "away"},\
                    {"time": "2020-09-29 07:21:06.744258", "status": "active"}]'),
            Mock(consultant_uuid="BehaveTest2", date=str(date.today()),
                 statuses='[{"time": "2020-09-29 07:20:08.064296", "status": "away"},\
                    {"time": "2020-09-29 07:21:06.744258", "status": "active"}]'),
            Mock(consultant_uuid="BehaveTest3", date=str(date.today()),
                 statuses='[{"time": "2020-09-29 07:20:08.064296", "status": "away"},\
                    {"time": "2020-09-29 07:21:06.744258", "status": "active"}]')
        ]
        mock_obj = Mock()
        mock_obj.scan.return_value = online_statuses
        mock_obj.get.return_value = online_statuses[0]
        return mock_obj


def get_online_statuses_provider(test=False):
    '''
        Returns OnlineStatuses client based on enviroment
    '''
    if test:
        injector = Injector(
            [OnlineStatusesProvider(), OnlineStatusesProviderTest()])
    else:
        injector = Injector(OnlineStatusesProvider())
    return injector.get(PynamoDBOnlineStatuses)
