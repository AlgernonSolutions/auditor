import json
from unittest.mock import patch, MagicMock

import boto3


def dev_dynamo():
    patch_obj = patch('toll_booth.obj.data_objects.sensitive_data.boto3.resource')
    mock_resource = patch_obj.start()
    mock_resource.return_value = boto3.Session(profile_name='dev').resource('dynamodb')
    return mock_resource, patch_obj


def dev_s3_stored_data():
    patch_obj = patch('toll_booth.obj.data_objects.stored_data.boto3.resource')
    mock_resource = patch_obj.start()
    mock_resource.return_value = boto3.Session(profile_name='dev').resource('s3')
    return mock_resource, patch_obj


def mock_s3_stored_data(*args):
    return_value = None
    for arg in args:
        return_value = arg
    patch_obj = patch('toll_booth.tasks.aws_tasks.boto3.resource')
    mock_obj = patch_obj.start()
    if return_value:
        mock_obj.side_effect = return_value
    return mock_obj, patch_obj


def mock_bullhorn(*args):
    patch_obj = patch('toll_booth.tasks.review.Bullhorn')
    mock_obj = patch_obj.start()
    bullhorn_mock = MagicMock()
    mock_obj.return_value = bullhorn_mock
    return bullhorn_mock, patch_obj


def mock_notary(*args):
    returned_data = args[0]
    if not returned_data:
        returned_data = json.dumps({'data': {'some_result': 'some_value'}})
    patch_obj = patch('toll_booth.tasks.gql_tasks.GqlNotary.send')
    mock_obj = patch_obj.start()
    mock_obj.side_effect = returned_data
    return mock_obj, patch_obj
