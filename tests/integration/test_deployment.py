import pytest
from algernon.aws import Bullhorn


@pytest.mark.test_deployment
class TestDeployment:
    def test_deployment(self):
        bullhorn = Bullhorn.retrieve(profile='dev')
        msg = {
            'task_name': 'review',
            'task_kwargs': {},
            'flow_id': ''
        }
