# pylint: disable=R0201
"""
    PynamoDB CheckIn Normal and Test dependencies
    :license: MIT
"""
from datetime import date
from unittest.mock import Mock

from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import PynamoDBCheckIn
from src.models.model_checkin import CheckInModel


class CheckInProvider(Module):
    """
        PynamoDB CheckIn Normal dependency
    """
    @singleton
    @provider
    def provide_checkin_model(self) -> PynamoDBCheckIn:
        '''
            Returns real CheckIn client
        '''
        return CheckInModel


class CheckInProviderTest(Module):
    """
        PynamoDB CheckIn Test dependency
    """
    @singleton
    @provider
    def provide_checkin_model(self) -> PynamoDBCheckIn:
        '''
            Returns fake CheckIn client (Mock object)
        '''
        checkins = [
            Mock(uuid='BehaveCheckinId1', consultant_uuid="BehaveTest1",
                date=str(date.today()), device_id="1234", completed=False,
                predictions='[]', user_input='[]'),
            Mock(uuid='BehaveCheckinId2', consultant_uuid="BehaveTest2",
                date=str(date.today()), device_id="1234", completed=False,
                predictions='[]', user_input='[]'),
            Mock(uuid='BehaveCheckinId3', consultant_uuid="BehaveTest3",
                date=str(date.today()), device_id="1234", completed=False,
                predictions='[]', user_input='[]')
        ]
        mock_obj = Mock()
        mock_obj.scan.return_value = checkins
        mock_obj.get.return_value = checkins[0]
        mock_obj.consultant_uuid_date_index.query.return_value = checkins
        mock_obj.date = '2020-01-01'
        mock_obj.completed = 'False'
        return mock_obj


def get_checkin_provider(test=False):
    '''
        Returns CheckIn client based on enviroment
    '''
    if test:
        injector = Injector([CheckInProvider(), CheckInProviderTest()])
    else:
        injector = Injector(CheckInProvider())
    return injector.get(PynamoDBCheckIn)
