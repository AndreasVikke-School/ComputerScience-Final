"""
Index Model File
"""
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute

class SlackIdIndex(GlobalSecondaryIndex):
    '''This class represents a global secondary index'''
    class Meta:
        '''Index Meta Class'''
        # index_name is optional, but can be provided to override the default name
        index_name = 'slack-id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        # All attributes are projected
        projection = AllProjection()

    # This attribute is the hash key for the index
    # Note that this attribute must also exist
    # in the model
    slack_id = UnicodeAttribute(hash_key=True)
    