"""
    Creator and Reader for Private Metadata
"""

import json
from typing import Dict


def create_metadata(checkin_id: str, current_customer: str, current_activity: str = None) -> str:
    '''
        Creates metadata for payload
        -
        :param checkin_id: Checkin id
        :param current_customer: Current customer id
        :param current_activity: Current activity if any
    '''
    metadata = {
        'checkin_id': checkin_id,
        'current_customer': current_customer,
        'current_activity': current_activity
    }
    return json.dumps(metadata)

def read_metadata(payload: Dict) -> Dict:
    '''
        Loads metadata from payload
        -
        :param private_metadata: Private metadata as dict
    '''
    if 'view' in payload and 'private_metadata' in payload['view']\
            and payload['view']['private_metadata'] != "":

        return json.loads(payload['view']['private_metadata'])
    return None
