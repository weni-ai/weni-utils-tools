import pytest
from unittest.mock import MagicMock
from weni_utils.tools.proxy import ProxyRequest

class TestProxyRequest:
    """Tests for proxy request functionality."""

    def test_get_order_by_id(self):
        """Test making a proxy request to get order by ID."""
        # Create a mock context
        mock_context = MagicMock()
        mock_context.project = {"auth_token": ""}
        mock_context.credentials = {}
        mock_context.parameters = {}
        mock_context.globals = {}
        mock_context.contact = {}
        mock_context.constants = {}
        
        proxy = ProxyRequest(context=mock_context)
        
        # Note: This test requires mocking the actual HTTP request
        # For now, just test the _format_body_proxy_request method
        result = proxy.make_proxy_request(
            path="/api/orders/pvt/document/1543930505162-01",
            method="GET",
        )

        print(result)
