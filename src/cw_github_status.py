# pylint: disable=E0401,R0801
"""
    Cloud Watch GitHub Status Converter
    :license: MIT
"""
import os
from typing import Dict

import boto3

from src.dependencies.dependency_typing import Requests
from src.dependencies.requests_provider import get_requests_provider

BASEURL = 'https://api.github.com/repos'
PROJECTNAME = os.environ['GITHUB_BUCKET']

CODEBUILD = boto3.client('codebuild')

AUTH_TOKEN = os.environ['ACCESS_TOKEN']


def handler(event, context):
    '''
        AWS Serverless Handler
        -
        :param event: AWS event
        :param context: AWS Lambda Context
    '''
    print("Request ID:", context.aws_request_id)
    requests_client = get_requests_provider()

    region = event['region']
    pipeline_name = event['detail']['pipeline']
    state = transform_state(event['detail']['state'])

    result = get_pipeline_execution(pipeline_name)
    payload = create_payload(pipeline_name, region, state)
    post_status_to_github(
        result['owner'], result['repository'], result['sha'], payload, requests_client)


def transform_state(state: str) -> str:
    '''
        Tranforms CloudWatch States To GitHub States
        -
        :param state: Cloudwatch State
    '''
    states = {
        'STARTED': 'pending',
        'SUCCEEDED': 'success',
        'FAILED': 'failure'
    }
    return states[state]


def create_payload(pipeline_name: str, region: str, status: str) -> Dict:
    '''
        Creates JSON Payload for GitHub POST
        -
        :param pipeline_name: name of the pipeline
        :param region: AWS Region
        :param status: Github Status
    '''
    descriptions = {
        'pending': 'Build started',
        'success': 'Build succeeded',
        'failure': 'Build failed!'
    }

    return {
        'state': status,
        'target_url': build_code_pipeline_url(pipeline_name, region),
        'description': descriptions[status],
        'context': 'continuous-integration' if pipeline_name == 'ci-pipeline'\
            else 'continuous-deployment'
    }


def build_code_pipeline_url(pipeline_name: str, region: str) -> str:
    '''
        Builds the Code Pipeline URL
        -
        :param pipeline_name: name of the pipeline
        :param region: AWS Region
    '''
    return 'https://{0}.console.aws.amazon.com/codepipeline/home?region={0}#/view/{1}'\
        .format(region, pipeline_name)


def get_pipeline_execution(pipeline_name: str) -> Dict:
    '''
        Gets The Source Version from CodeBuild which is the Commit SHA
        -
        :param pipeline_name: name of the pipeline
    '''
    if pipeline_name == 'ci-pipeline':
        name = '{0}-{1}'.format(PROJECTNAME, 'feature-branch')
    elif pipeline_name == 'cd-pipeline':
        name = '{0}-{1}'.format(PROJECTNAME, 'master-branch')
    else:
        name = PROJECTNAME

    build_list = CODEBUILD.list_builds_for_project(
        projectName=name
    )

    print(build_list)

    build = CODEBUILD.batch_get_builds(
        ids=[build_list['ids'][0]]
    )

    print(build)

    return {
        'owner': 'efio-dk',
        'repository': 'sterling',
        'sha': build['builds'][0]['sourceVersion']
    }


def post_status_to_github(owner: str, repository: str, sha: str,
                          payload: Dict, requests_client: Requests) -> None:
    '''
        Posts the New Status to the gitHub commit
        -
        :param owner: Github owner
        :param repository: Github repository
        :param sha: Source Version from CodeBuild which is the Commit SHA
        :param payload: payload for requests
        :param requests_client: Request Client Provider
    '''
    url = '{0}/{1}/{2}/statuses/{3}'.format(BASEURL, owner, repository, sha)

    hed = {'Content-Type': 'application/json'}

    requests_client.post(url, json=payload, headers=hed, auth=('', AUTH_TOKEN))
