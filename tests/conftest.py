import json
from os import path
from unittest.mock import patch, MagicMock

import pytest
from botocore.exceptions import ClientError

from tests.test_setup import mock_objs


@pytest.fixture
def mocks(request):
    patches = []
    mocks = {}
    indicated_patches = {}
    test_name = request.node.originalname
    if test_name in [
        'test_audit_graph'
    ]:
        bullhorn_data = [
            json.dumps({'data': {'get_vertex': {}}}),
            json.dumps({'data': {'listStateEntries': {}}}),
        ]
        indicated_patches = {
            's3': (mock_objs.mock_s3_stored_data, (ClientError({'Error': {'Code': 'NoSuchKey'}}, 'get'),)),
            'gql': (mock_objs.mock_notary, (bullhorn_data,)),
            'bullhorn': (mock_objs.mock_bullhorn, ())
        }

    for mock_name, mock_generator in indicated_patches.items():
        mock_obj, patch_obj = mock_generator[0](*mock_generator[1])
        mocks[mock_name] = mock_obj
        patches.append(patch_obj)
    yield mocks
    for patch_obj in patches:
        patch_obj.stop()


@pytest.fixture(params=['review_surgical_graph'])
def audit_graph_event(request):
    event_name = request.param
    return _read_test_event(event_name)


@pytest.fixture(autouse=True)
def silence_x_ray():
    x_ray_patch_all = 'algernon.aws.lambda_logging.patch_all'
    patch(x_ray_patch_all).start()
    yield
    patch.stopall()


@pytest.fixture
def mock_context():
    from unittest.mock import MagicMock
    context = MagicMock(name='context')
    context.__reduce__ = cheap_mock
    context.function_name = 'test_function'
    context.invoked_function_arn = 'test_function_arn'
    context.aws_request_id = '12344_request_id'
    context.get_remaining_time_in_millis.side_effect = [1000001, 500001, 250000, 0]
    return context


def cheap_mock(*args):
    from unittest.mock import Mock
    return Mock, ()


def _read_test_event(event_name):
    with open(path.join('tests', 'test_events', f'{event_name}.json')) as json_file:
        event = json.load(json_file)
        return event
