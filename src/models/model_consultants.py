# pylint: disable=E0401,R0903,W0221,R0801,C0116
"""
    Consultants Model File
    :license: MIT
"""
import os

from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model
from src.modules.get_export import get_export
from src.models.index_consultant_email import EmailIndex
from src.models.index_consultant_slack_id import SlackIdIndex


class ConsultantsModel(Model):
    '''Consultants Model Class'''
    class Meta:
        '''Consultants Meta Class'''
        if 'ConsultantsTableName' in os.environ:
            table_name = os.environ['ConsultantsTableName']
        else:
            table_name = get_export('database-ConsultantsTableName')

        region = 'eu-central-1'
        host = 'https://dynamodb.eu-central-1.amazonaws.com'

    uuid = UnicodeAttribute(hash_key=True, null=False)
    email = UnicodeAttribute(null=False)
    slack_id = UnicodeAttribute(null=False)
    time_for_checkin = UnicodeAttribute(null=True)
    same_day_checkin = UnicodeAttribute(null=True)
    absence_till = UnicodeAttribute(null=True)
    email_index = EmailIndex()
    slack_id_index = SlackIdIndex()

    def __iter__(self):
        for name, attr in self._get_attributes().items():
            yield name, attr.serialize(getattr(self, name))
