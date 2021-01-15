# pylint: disable=E0401,R0903,W0221,R0801,C0116
"""
    Customers Model File
    :license: MIT
"""
import os

from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.models import Model
from src.modules.get_export import get_export
from src.models.index_customer_reg_number import RegistrationNoIndex

class CustomersModel(Model):
    '''Online Statuses Model Class'''
    class Meta:
        '''Online Statuses Meta Class'''
        if 'CustomersTableName' in os.environ:
            table_name = os.environ['CustomersTableName']
        else:
            table_name = get_export('database-CustomersTableName')

        region = 'eu-central-1'
        host = 'https://dynamodb.eu-central-1.amazonaws.com'

    uuid = UnicodeAttribute(hash_key=True)
    customerType = NumberAttribute(null=True)
    registrationNo = UnicodeAttribute()
    friendlyName = UnicodeAttribute(null=True)
    legalName = UnicodeAttribute(null=True)
    address = UnicodeAttribute(null=True)
    postalCode = UnicodeAttribute(null=True)
    city = UnicodeAttribute(null=True)
    email = UnicodeAttribute(null=True)
    active = UnicodeAttribute()
    defaultPaymentTerms = NumberAttribute(null=True)
    registrationNo_index = RegistrationNoIndex()

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
