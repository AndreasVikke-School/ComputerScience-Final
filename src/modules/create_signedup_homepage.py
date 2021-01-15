"""
    Creates Singedup Home Tap
    :license: MIT
"""
import json
from src.dependencies.dependency_typing import PynamoDBConsultant

def create_home_tap(consultant_uuid: str, consultant_model: PynamoDBConsultant):
    '''
        Creates Home tap with correct time from Consultant
        -
        :param consultant_uuid: Uuid of Consultant
        :param consultant_model: Consultant Model
    '''
    consultant = consultant_model.get(consultant_uuid)

    with open("src/templates/{0}.json".format('home_tap_template_signedup'), "r") as body:
        home_tap = json.load(body)

        if consultant.time_for_checkin is not None:
            home_tap['blocks'][4]['elements'][0]['initial_time'] = consultant.time_for_checkin

        if consultant_model.same_day_checkin is not None:
            print(consultant.same_day_checkin)
            if str(consultant.same_day_checkin) == 'True':
                home_tap['blocks'][5]['elements'][0]['initial_options'] =\
                        [home_tap['blocks'][5]['elements'][0]['options'][0]]

    print(home_tap)
    return home_tap
