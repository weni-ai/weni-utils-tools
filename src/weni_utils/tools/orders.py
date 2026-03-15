"""
OrderConcierge - Main class for order search

This class orchestrates order search and data handling.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pytz
import requests
from tzlocal.windows_tz import win_tz
from weni.context import Context

from .client import VTEXClient
from .proxy import ProxyRequest
from .utils import Utils, convert_cents

logger = logging.getLogger(__name__)

DEFAULT_WINDOWS_TZ = "E. South America Standard Time"


class OrderConcierge:
    """
    Main class for VTEX order search.

    Example:
        concierge = OrderConcierge(
            base_url_vtex="https://store.vtexcommercestable.com.br",
            store_url_vtex="https://store.com.br"
        )

        orders = concierge.search_orders("12345678900")
        order_details = concierge.get_order_details("123456-01")
    """

    def __init__(
        self,
        base_url_vtex: str,
        store_url_vtex: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
    ):
        """
        Initialize OrderConcierge.

        Args:
            base_url_vtex: VTEX API base URL
            store_url_vtex: Store URL
            vtex_app_key: VTEX App Key (optional)
            vtex_app_token: VTEX App Token (optional)
        """
        self.client = VTEXClient(
            base_url_vtex=base_url_vtex,
            store_url_vtex=store_url_vtex,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token,
        )
        self.timezone = self._get_timezone()

    def _get_timezone(self):
        """
        Get store timezone from VTEX (Windows name) and return a pytz timezone object.
        """
        store_details = self.client.get_store_details()

        windows_tz = store_details.get("TimeZone") or DEFAULT_WINDOWS_TZ
        iana_tz = win_tz.get(windows_tz)
        if iana_tz is None:
            iana_tz = win_tz[DEFAULT_WINDOWS_TZ]
        return pytz.timezone(iana_tz)

    def search_orders(
        self, document: str = None, email: str = None, incomplete_orders: bool = False
    ) -> Dict[str, Any]:
        """
        Search orders by document or email.

        Args:
            document: Customer document
            email: Customer email
            incomplete_orders: Whether to include incomplete orders
                Default is False (only complete orders)
        Returns:
            Dictionary with orders and current date
        """
        orders_data = self.client.list_orders(
            document=document, email=email, include_incomplete=incomplete_orders
        )
        converted_orders = convert_cents(orders_data)

        return {
            "orders": converted_orders,
            "current_time": datetime.now(self.timezone).strftime("%Y/%m/%d %H:%M:%S"),
        }

    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        Get order details.

        Args:
            order_id: Order ID

        Returns:
            Dictionary with order details and current date
        """
        order_data = self.client.get_order_by_id(order_id)

        if not order_data:
            return {"error": "Order not found", "order": None}

        converted_order = convert_cents(order_data)

        return {
            "order": converted_order,
            "current_time": datetime.now(self.timezone).strftime("%Y/%m/%d %H:%M:%S"),
        }


class OrderDataProxy(Context):
    """
    Proxy for order requests using VTEX API. Receives the same Context
    the platform injects (parameters, credentials, project, etc.).
    """

    def __init__(self, context: Context):
        super().__init__(
            parameters=context.parameters,
            globals=getattr(context, "globals", {}),
            contact=context.contact,
            project=context.project,
            constants=getattr(context, "constants", {}),
            credentials=context.credentials,
        )

        self.proxy = ProxyRequest(self)

        try:
            self.vtex_account = self.proxy.get_vtex_account()
        except requests.exceptions.HTTPError as e:
            resp = e.response
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise ValueError(
                f"Failed to initialize OrderDataProxy: {detail} (HTTP {resp.status_code})"
            ) from None
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to initialize OrderDataProxy: {e}") from None

        self.timezone = self._get_timezone()

    def _get_store_details(self) -> Optional[Dict]:
        """
        Get store details from the VTEX API via proxy using the vtex_account.
        """
        path = f"api/catalog_system/pub/saleschannel/default?an={self.vtex_account}"
        try:
            return self.proxy.make_proxy_request(path=path, method="GET")
        except Exception as e:
            logger.error("Failed to fetch store details via proxy: %s", e)
            return None

    def _get_timezone(self):
        """
        Get store timezone from VTEX (Windows name) and return a pytz timezone object.
        Falls back to E. South America Standard Time if unavailable.
        """
        store_details = self._get_store_details()

        windows_tz = DEFAULT_WINDOWS_TZ
        if store_details:
            windows_tz = store_details.get("TimeZone") or DEFAULT_WINDOWS_TZ

        iana_tz = win_tz.get(windows_tz)
        if iana_tz is None:
            iana_tz = win_tz[DEFAULT_WINDOWS_TZ]

        return pytz.timezone(iana_tz)

    def get_order_details_proxy(
        self,
        order_id: Optional[str] = None,
        document: Optional[str | int] = None,
        email: Optional[str] = None,
        per_page: Optional[int] = 10,
        seller_name: Optional[str] = None,
        sales_channel: Optional[int] = None,
    ) -> Dict:
        """
        Get order details from the VTEX API via proxy.

        Args:
            order_id: Order ID (optional).
            document: Document (optional).
            email: Email (optional).
            per_page: Number of items per page (optional).
            seller_name: Seller name (optional).
            sales_channel: Sales channel (optional).

        One of order_id, document or email must be provided.

        Returns:
            Dictionary with order details or error.
        """
        path = Utils.create_path_order_id(
            order_id=order_id,
            document=document,
            email=email,
            per_page=per_page,
            seller_name=seller_name,
            sales_channel=sales_channel,
        )
        if not path:
            return {"error": "One of the arguments must be provided."}

        order_details = self.proxy.make_proxy_request(path=path, method="GET")

        if "list" not in order_details and "orderId" not in order_details:
            return {"order": order_details}

        converted_order = convert_cents(order_details)

        return {
            "order": converted_order,
            "current_time": datetime.now(self.timezone).strftime("%Y/%m/%d %H:%M:%S"),
        }
