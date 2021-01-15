"""
    Customers Model File
    :license: MIT
"""
import os

from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.models import Model
from src.modules.get_export import get_export
from src.models.index_weights_name import NameIndex

class WeightModel(Model):
    '''Weights Model Class'''
    class Meta:
        '''Weights Meta Class'''
        if 'WeightsTableName' in os.environ:
            table_name = os.environ['WeightsTableName']
        else:
            table_name = get_export('database-WeightsTableName')

        region = 'eu-central-1'
        host = 'https://dynamodb.eu-central-1.amazonaws.com'

    uuid = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    value = NumberAttribute()
    name_index = NameIndex()

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
