# pylint: disable=E0401,R0903,W0221,R0801,C0116
"""
    Online Statuses Model File
    :license: MIT
"""
import os

from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model
from src.modules.get_export import get_export

class OnlineStatusesModel(Model):
    '''Online Statuses Model Class'''
    class Meta:
        '''Online Statuses Meta Class'''
        if 'OnlineStatusesTableName' in os.environ:
            table_name = os.environ['OnlineStatusesTableName']
        else:
            table_name = get_export('database-OnlineStatusesTableName')

        region = 'eu-central-1'
        host = 'https://dynamodb.eu-central-1.amazonaws.com'

    consultant_uuid = UnicodeAttribute(hash_key=True, null=False)
    date = UnicodeAttribute(range_key=True, null=False)
    statuses = UnicodeAttribute(null=False)

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
