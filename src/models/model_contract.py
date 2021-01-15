"""
    Model file for pynamodb checkin table.
    :license: MIT
"""
import os

from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.models import Model
from src.modules.get_export import get_export
from src.models.index_contract_reg_number import CustomerIdIndex

class ContractModel(Model):
    '''ContractModel Model Class'''
    class Meta:
        '''Contract Meta Class'''
        if 'ContractTableName' in os.environ:
            table_name = os.environ['ContractTableName']
        else:
            table_name = get_export('database-ContractTableName')

        region = 'eu-central-1'
        host = 'https://dynamodb.eu-central-1.amazonaws.com'

    uuid = UnicodeAttribute(hash_key=True)
    customerId = NumberAttribute()
    theirReference = UnicodeAttribute(null=True)
    rates = UnicodeAttribute(null=True)
    paymentTerms = UnicodeAttribute(null=True)
    broker = UnicodeAttribute(null=True)
    active = UnicodeAttribute(null=True)
    consultants = UnicodeAttribute(null=True)
    startDate = UnicodeAttribute(null=True)
    endDate = UnicodeAttribute()
    requiredDescription = UnicodeAttribute(null=True)
    projects = UnicodeAttribute(null=True)
    customerId_index = CustomerIdIndex()

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
