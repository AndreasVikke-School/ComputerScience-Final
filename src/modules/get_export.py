"""
    Module for getting export value of Stack
    :license: MIT
"""
import boto3


def get_export(name: str) -> str:
    '''
        Main function for getting the export value
        -
        :param name: Name of the export value
    '''
    cf_client = boto3.client('cloudformation')
    exports = cf_client.list_exports()

    export_value = ""
    for ex in exports['Exports']:
        if ex['Name'] == name:
            export_value = ex['Value']

    return export_value
