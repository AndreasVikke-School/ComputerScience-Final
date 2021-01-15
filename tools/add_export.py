"""
File for adding Export to ServiceEndpoint for Serverless API
"""
import json
import sys

JSON_DATA = None
STAGE = sys.argv[1]

with open('../target/{0}/serverless-state.json'.format(STAGE)) as state:
    DATA = json.load(state)

    DATA['service']['provider']['compiledCloudFormationTemplate']['Outputs']['ServiceEndpoint']\
        ['Export'] = {'Name': 'serverless-stg-serviceendpoint'}
    JSON_DATA = DATA

with open('../target/{0}/serverless-state.json'.format(STAGE), 'w') as state:
    json.dump(JSON_DATA, state, indent=4)
