from unittest.mock import MagicMock, patch

import pytest

from weni_utils.tools.orders import OrderDataProxy
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
# Utils.remove_fields_orders
# ---------------------------------------------------------------------------
class TestRemoveFieldsOrders:
    """Tests for remove_fields_orders covering list, detail, and edge cases."""

    def _make_order_list(self):
        return {
            "orders": {
                "list": [
                    {
                        "orderId": "ORD-1",
                        "hostname": "store.example.com",
                        "status": "invoiced",
                        "nested": {"hostname": "should-also-go"},
                    },
                    {
                        "orderId": "ORD-2",
                        "hostname": "store.example.com",
                        "status": "payment-approved",
                    },
                ],
                "paging": {"total": 2, "pages": 1},
                "stats": {"totalValue": 100},
            },
            "current_time": "2026-03-05",
        }

    def _make_order_detail(self):
        return {
            "order": {
                "orderId": "ORD-1",
                "followUpEmail": "test@ct.vtex.com.br",
                "hostname": "store.example.com",
                "paymentData": {
                    "transactions": [
                        {
                            "merchantName": "STORE",
                            "payments": [
                                {
                                    "paymentSystemName": "Visa",
                                    "value": 100,
                                },
                                {
                                    "paymentSystemName": "Pix",
                                    "value": 95,
                                },
                            ],
                        }
                    ]
                },
            },
            "current_time": "2026-03-05",
        }

    # --- Order list structure (orders.list[]) ---

    def test_list_remove_field_from_each_order(self):
        data = self._make_order_list()
        result = Utils.remove_fields_orders(data, ["hostname"])
        for order in result["orders"]["list"]:
            assert "hostname" not in order
        assert "orderId" in result["orders"]["list"][0]

    def test_list_recursive_removes_nested_occurrences(self):
        data = self._make_order_list()
        result = Utils.remove_fields_orders(data, ["hostname"])
        assert "hostname" not in result["orders"]["list"][0].get("nested", {})

    def test_list_remove_from_orders_dict(self):
        data = self._make_order_list()
        result = Utils.remove_fields_orders(data, ["paging"])
        assert "paging" not in result["orders"]
        assert "stats" in result["orders"]

    def test_list_remove_from_root(self):
        data = self._make_order_list()
        result = Utils.remove_fields_orders(data, ["current_time"])
        assert "current_time" not in result
        assert "orders" in result

    def test_list_remove_mixed_levels(self):
        data = self._make_order_list()
        result = Utils.remove_fields_orders(data, ["hostname", "paging", "current_time"])
        assert "paging" not in result["orders"]
        assert "current_time" not in result
        for order in result["orders"]["list"]:
            assert "hostname" not in order

    # --- Single order structure (order) ---

    def test_detail_remove_simple_field(self):
        data = self._make_order_detail()
        result = Utils.remove_fields_orders(data, ["followUpEmail"])
        assert "followUpEmail" not in result["order"]
        assert "orderId" in result["order"]

    def test_detail_recursive_removes_deeply_nested(self):
        data = self._make_order_detail()
        result = Utils.remove_fields_orders(data, ["paymentSystemName"])
        for payment in result["order"]["paymentData"]["transactions"][0]["payments"]:
            assert "paymentSystemName" not in payment
        assert result["order"]["paymentData"]["transactions"][0]["payments"][0]["value"] == 100

    def test_detail_dot_notation_path(self):
        data = self._make_order_detail()
        result = Utils.remove_fields_orders(data, ["paymentData.transactions.0.merchantName"])
        assert "merchantName" not in result["order"]["paymentData"]["transactions"][0]
        assert "payments" in result["order"]["paymentData"]["transactions"][0]

    def test_detail_multiple_strategies_combined(self):
        data = self._make_order_detail()
        result = Utils.remove_fields_orders(
            data,
            ["followUpEmail", "paymentSystemName", "paymentData.transactions.0.merchantName"],
        )
        assert "followUpEmail" not in result["order"]
        assert "merchantName" not in result["order"]["paymentData"]["transactions"][0]
        for payment in result["order"]["paymentData"]["transactions"][0]["payments"]:
            assert "paymentSystemName" not in payment

    # --- Edge cases ---

    def test_nonexistent_field_is_ignored(self):
        data = self._make_order_detail()
        result = Utils.remove_fields_orders(data, ["doesNotExist"])
        assert result["order"]["orderId"] == "ORD-1"

    def test_invalid_dot_path_is_ignored(self):
        data = self._make_order_detail()
        result = Utils.remove_fields_orders(data, ["a.b.c.999.nope"])
        assert result["order"]["orderId"] == "ORD-1"

    def test_empty_fields_list(self):
        data = self._make_order_detail()
        result = Utils.remove_fields_orders(data, [])
        assert result["order"]["orderId"] == "ORD-1"
        assert result["order"]["followUpEmail"] == "test@ct.vtex.com.br"

    def test_plain_dict_without_orders_or_order_key(self):
        data = {"foo": "bar", "baz": 42}
        result = Utils.remove_fields_orders(data, ["baz"])
        assert "baz" not in result
        assert result["foo"] == "bar"


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

    @patch("weni_utils.tools.orders.ProxyRequest")
    def test_get_order_by_email(self, mock_proxy_cls):
        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy
        mock_proxy.get_vtex_account.return_value = "teststore"

        order_response = {"orderId": "123", "status": "invoiced"}
        mock_proxy.make_proxy_request.side_effect = [
            {"TimeZone": "E. South America Standard Time"},
            order_response,
        ]

        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy(email="user@example.com")

        assert "order" in result
        assert "current_time" in result
        assert result["order"]["orderId"] == "123"

    @patch("weni_utils.tools.orders.ProxyRequest")
    def test_get_order_by_order_id(self, mock_proxy_cls):
        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy
        mock_proxy.get_vtex_account.return_value = "teststore"

        mock_proxy.make_proxy_request.side_effect = [
            {"TimeZone": "E. South America Standard Time"},
            {"orderId": "ORD-1"},
        ]

        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy(order_id="ORD-1")

        assert "order" in result
        assert "current_time" in result
        assert result["order"]["orderId"] == "ORD-1"

    @patch("weni_utils.tools.orders.ProxyRequest")
    def test_get_order_by_document(self, mock_proxy_cls):
        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy
        mock_proxy.get_vtex_account.return_value = "teststore"

        mock_proxy.make_proxy_request.side_effect = [
            {"TimeZone": "E. South America Standard Time"},
            {"list": [{"orderId": "ORD-DOC", "status": "invoiced"}]},
        ]

        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy(document="12345678900")

        assert "order" in result
        assert "current_time" in result

    @patch("weni_utils.tools.orders.ProxyRequest")
    def test_no_args_returns_error(self, mock_proxy_cls):
        mock_proxy = MagicMock()
        mock_proxy_cls.return_value = mock_proxy
        mock_proxy.get_vtex_account.return_value = "teststore"
        mock_proxy.make_proxy_request.return_value = {"TimeZone": "E. South America Standard Time"}

        proxy = OrderDataProxy(context=self._mock_context())
        result = proxy.get_order_details_proxy()
        assert "error" in result

    @patch("weni_utils.tools.orders.ProxyRequest")
    def test_custom_per_page(self, mock_proxy_cls):
        mock_proxy_cls.return_value.make_proxy_request.return_value = {}

        proxy = OrderDataProxy(context=self._mock_context())
        proxy.get_order_details_proxy(email="a@b.com", per_page=25)

        call_path = mock_proxy_cls.return_value.make_proxy_request.call_args[1]["path"]
        assert "per_page=25" in call_path
