# pylint: disable=R0201
"""
    PynamoDB Customers Normal and Test dependencies
    :license: MIT
"""
from unittest.mock import Mock, PropertyMock

from injector import Injector, Module, provider, singleton
from src.dependencies.dependency_typing import PynamoDBCustomers
from src.models.model_customers import CustomersModel


class CustomersProvider(Module):
    """
        PynamoDB Customers Normal dependency
    """
    @singleton
    @provider
    def provide_customers_model(self) -> PynamoDBCustomers:
        '''
            Returns real Customers client
        '''
        return CustomersModel


class CustomersProviderTest(Module):
    """
        PynamoDB Customers Test dependency
    """
    @singleton
    @provider
    def provide_customers_model(self) -> PynamoDBCustomers:
        '''
            Returns fake Customers client (Mock object)
        '''
        customer = Mock(uuid="BehaveTest1")
        name = PropertyMock(return_value='Customer A')
        type(customer).friendlyName = name

        customers = [
            customer,
            customer,
            customer
        ]
        mock_obj = Mock()
        mock_obj.scan.return_value = customers
        mock_obj.get.return_value = customers[0]
        return mock_obj


def get_customers_provider(test=False):
    '''
        Returns Customers client based on enviroment
    '''
    if test:
        injector = Injector(
            [CustomersProvider(), CustomersProviderTest()])
    else:
        injector = Injector(CustomersProvider())
    return injector.get(PynamoDBCustomers)
