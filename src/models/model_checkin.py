# pylint: disable=E0401,R0903,W0221,R0801,C0116
"""
    Model file for pynamodb checkin table.
    :license: MIT
"""
import os

from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model
from src.modules.get_export import get_export
from src.models.index_checkin import ConsultantDateIndex

class CheckInModel(Model):
    '''CheckInModel Model Class'''
    class Meta:
        '''CheckIn Meta Class'''
        if 'CheckInTableName' in os.environ:
            table_name = os.environ['CheckInTableName']
        else:
            table_name = get_export('database-CheckInTableName')

        region = 'eu-central-1'
        host = 'https://dynamodb.eu-central-1.amazonaws.com'

    uuid = UnicodeAttribute(hash_key=True)
    consultant_uuid = UnicodeAttribute()
    date = UnicodeAttribute()
    device_id = UnicodeAttribute(null=True)
    completed = UnicodeAttribute(null=False)
    predictions = UnicodeAttribute()
    consultant_uuid_date_index = ConsultantDateIndex()
    user_input = UnicodeAttribute(null=True)

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
