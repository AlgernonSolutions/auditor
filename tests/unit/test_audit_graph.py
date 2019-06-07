import pytest

from toll_booth.tasks import handler


@pytest.mark.audit_graph
class TestAuditGraph:
    def test_audit_graph(self, audit_graph_event, mock_context, mocks):
        results = handler(audit_graph_event, mock_context)
        assert results
