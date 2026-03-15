"""
Manual test for OrderDataProxy with mocked Context.

Run from project root:
    python tests/test.py
"""

import os
from unittest.mock import MagicMock, patch

from weni.context import Context

from weni_utils.tools.orders import OrderDataProxy


def make_context(document=None, order_id=None, email=None):
    params = {}
    if document:
        params["document"] = document
    if order_id:
        params["orderID"] = order_id
    if email:
        params["email"] = email

    return Context(
        parameters=params,
        globals={},
        contact={},
        project={"auth_token": os.getenv("AUTH_TOKEN", "mock-token")},
        constants={},
        credentials={},
    )


STORE_DETAILS_RESPONSE = {
    "TimeZone": "E. South America Standard Time",
    "CurrencySymbol": "R$",
}


@patch("weni_utils.tools.orders.ProxyRequest")
def test_search_by_document(mock_proxy_cls):
    mock_proxy = MagicMock()
    mock_proxy_cls.return_value = mock_proxy

    mock_proxy.get_vtex_account.return_value = "teststore"
    mock_proxy.make_proxy_request.side_effect = [
        STORE_DETAILS_RESPONSE,
        {"list": [{"orderId": "ORD-001", "status": "invoiced"}]},
    ]

    ctx = make_context(document="12345678900")
    order_proxy = OrderDataProxy(ctx)
    result = order_proxy.get_order_details_proxy(document="12345678900")

    print("[PASS] Search by document")
    print(f"  Result: {result}")
    assert "order" in result
    assert "current_time" in result


@patch("weni_utils.tools.orders.ProxyRequest")
def test_search_by_order_id(mock_proxy_cls):
    mock_proxy = MagicMock()
    mock_proxy_cls.return_value = mock_proxy

    mock_proxy.get_vtex_account.return_value = "teststore"
    mock_proxy.make_proxy_request.side_effect = [
        STORE_DETAILS_RESPONSE,
        {"orderId": "ORD-001", "status": "invoiced", "value": 15000},
    ]

    ctx = make_context(order_id="ORD-001")
    order_proxy = OrderDataProxy(ctx)
    result = order_proxy.get_order_details_proxy(order_id="ORD-001")

    print("[PASS] Search by order ID")
    print(f"  Result: {result}")
    assert "order" in result
    assert "current_time" in result


@patch("weni_utils.tools.orders.ProxyRequest")
def test_no_args_returns_error(mock_proxy_cls):
    mock_proxy = MagicMock()
    mock_proxy_cls.return_value = mock_proxy

    mock_proxy.get_vtex_account.return_value = "teststore"
    mock_proxy.make_proxy_request.return_value = STORE_DETAILS_RESPONSE

    ctx = make_context()
    order_proxy = OrderDataProxy(ctx)
    result = order_proxy.get_order_details_proxy()

    print("[PASS] No args returns error")
    print(f"  Result: {result}")
    assert "error" in result


@patch("weni_utils.tools.orders.ProxyRequest")
def test_timezone_fallback(mock_proxy_cls):
    """When store details fails, timezone should fall back to Sao Paulo."""
    mock_proxy = MagicMock()
    mock_proxy_cls.return_value = mock_proxy

    mock_proxy.get_vtex_account.return_value = "teststore"
    mock_proxy.make_proxy_request.side_effect = [
        Exception("API unavailable"),
        {"orderId": "ORD-002"},
    ]

    ctx = make_context(order_id="ORD-002")
    order_proxy = OrderDataProxy(ctx)

    assert str(order_proxy.timezone) == "America/Sao_Paulo"
    print("[PASS] Timezone fallback to America/Sao_Paulo")


if __name__ == "__main__":
    test_search_by_document()
    test_search_by_order_id()
    test_no_args_returns_error()
    test_timezone_fallback()
    print("\nAll tests passed!")
