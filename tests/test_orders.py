import pytest
from unittest.mock import MagicMock, patch
from weni_utils.tools.proxy import ProxyRequest
from weni_utils.tools.client import OrderDataProxy

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

    @patch("weni_utils.tools.client.ProxyRequest")
    def test_get_order_id_proxy(self, mock_proxy_request_class):
        """Test making a proxy request to get order by ID with mocked proxy."""
        mock_context = MagicMock()
        mock_context.project = {"auth_token": "fake-token"}
        mock_context.credentials = {}
        mock_context.parameters = {}
        mock_context.globals = {}
        mock_context.contact = {}
        mock_context.constants = {}

        expected_response = {"orderId": "123", "email": "example@example.com", "status": "invoiced"}
        mock_proxy_request_class.return_value.make_proxy_request.return_value = expected_response

        order_data_proxy = OrderDataProxy(context=mock_context)
        result = order_data_proxy.get_order_details_proxy(email="example@example.com")

        assert result == expected_response
        mock_proxy_request_class.return_value.make_proxy_request.assert_called_once_with(
            path="/api/oms/pvt/orders/?q=example@example.com&per_page=10",
            method="GET",
        )