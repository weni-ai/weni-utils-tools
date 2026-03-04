from unittest.mock import MagicMock, patch

import pytest

from weni_utils.tools.client import OrderDataProxy
from weni_utils.tools.utils import Utils


# ---------------------------------------------------------------------------
# Utils.create_path_order_id
# ---------------------------------------------------------------------------
class TestCreatePathOrderId:
    def test_by_order_id(self):
        path = Utils.create_path_order_id(order_id="ORD-123")
        assert path == "/api/oms/pvt/orders/ORD-123"

    def test_by_document(self):
        path = Utils.create_path_order_id(document="123.456.789-00")
        assert "12345678900" in path
        assert path.startswith("/api/oms/pvt/orders/")

    def test_by_document_int(self):
        path = Utils.create_path_order_id(document=12345678900)
        assert "12345678900" in path

    def test_by_email(self):
        path = Utils.create_path_order_id(email="user@example.com")
        assert "user@example.com" in path

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Utils.create_path_order_id(email="invalid-email")

    def test_no_args_returns_empty(self):
        assert Utils.create_path_order_id() == ""

    def test_per_page_param(self):
        path = Utils.create_path_order_id(email="a@b.com", per_page=5)
        assert "per_page=5" in path

    def test_seller_name_param(self):
        path = Utils.create_path_order_id(document="123", seller_name="seller1")
        assert "seller_name=seller1" in path

    def test_sales_channel_param(self):
        path = Utils.create_path_order_id(document="123", sales_channel=2)
        assert "sales_channel=2" in path

    def test_multiple_params(self):
        path = Utils.create_path_order_id(
            email="a@b.com", per_page=10, seller_name="s1", sales_channel=3
        )
        assert "per_page=10" in path
        assert "seller_name=s1" in path
        assert "sales_channel=3" in path

    def test_order_id_ignores_extra_params(self):
        path = Utils.create_path_order_id(order_id="ORD-1", per_page=10)
        assert "per_page" not in path
        assert path == "/api/oms/pvt/orders/ORD-1"


# ---------------------------------------------------------------------------
# OrderDataProxy
# ---------------------------------------------------------------------------
class TestOrderDataProxy:
    def _mock_context(self):
        ctx = MagicMock()
        ctx.project = {"auth_token": "fake-token"}
        ctx.credentials = {}
        ctx.parameters = {}
        ctx.globals = {}
        ctx.contact = {}
        ctx.constants = {}
        return ctx

    @patch("weni_utils.tools.client.ProxyRequest")
    def test_get_order_by_email(self, mock_proxy_cls):
        expected = {"orderId": "123", "status": "invoiced"}
        mock_proxy_cls.return_value.make_proxy_request.return_value = expected

        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy(email="user@example.com")

        assert result == expected
        mock_proxy_cls.return_value.make_proxy_request.assert_called_once_with(
            path="/api/oms/pvt/orders/?q=user@example.com&per_page=10",
            method="GET",
        )

    @patch("weni_utils.tools.client.ProxyRequest")
    def test_get_order_by_order_id(self, mock_proxy_cls):
        expected = {"orderId": "ORD-1"}
        mock_proxy_cls.return_value.make_proxy_request.return_value = expected

        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy(order_id="ORD-1")

        assert result == expected
        mock_proxy_cls.return_value.make_proxy_request.assert_called_once_with(
            path="/api/oms/pvt/orders/ORD-1",
            method="GET",
        )

    @patch("weni_utils.tools.client.ProxyRequest")
    def test_get_order_by_document(self, mock_proxy_cls):
        expected = {"list": []}
        mock_proxy_cls.return_value.make_proxy_request.return_value = expected

        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy(document="12345678900")

        assert result == expected
        call_path = mock_proxy_cls.return_value.make_proxy_request.call_args[1]["path"]
        assert "12345678900" in call_path

    @patch("weni_utils.tools.client.ProxyRequest")
    def test_no_args_returns_error(self, mock_proxy_cls):
        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy()
        assert "error" in result
        mock_proxy_cls.return_value.make_proxy_request.assert_not_called()

    @patch("weni_utils.tools.client.ProxyRequest")
    def test_custom_per_page(self, mock_proxy_cls):
        mock_proxy_cls.return_value.make_proxy_request.return_value = {}

        proxy = OrderDataProxy(context=self._mock_context())
        proxy.get_order_details_proxy(email="a@b.com", per_page=25)

        call_path = mock_proxy_cls.return_value.make_proxy_request.call_args[1]["path"]
        assert "per_page=25" in call_path
