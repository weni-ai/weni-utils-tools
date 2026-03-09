"""
OrderConcierge - Main class for order search

This class orchestrates order search and data handling.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import pytz
from tzlocal.windows_tz import win_tz

from .client import VTEXClient
from .utils import convert_cents


class OrderConcierge:
    """
    Main class for VTEX order search.

    Example:
        concierge = OrderConcierge(
            base_url="https://store.vtexcommercestable.com.br",
            store_url="https://store.com.br"
        )

        orders = concierge.search_orders("12345678900")
        order_details = concierge.get_order_details("123456-01")
    """

    def __init__(
        self,
        base_url: str,
        vtex_app_key: str,
        vtex_app_token: str,
        store_url: Optional[str] = None,
    ):
        """
        Initialize OrderConcierge.

        Args:
            base_url: VTEX API base URL
            vtex_app_key: VTEX App Key
            vtex_app_token: VTEX App Token
            store_url: Store URL (optional)
        """
        self.client = VTEXClient(
            base_url=base_url,
            store_url=store_url,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token,
        )
        self.timezone = self._get_timezone()

    def _get_timezone(self):
        """
        Get store timezone from VTEX (Windows name) and return a pytz timezone object.
        """
        store_details = self.client.get_store_details()

        windows_tz = store_details.get("TimeZone") or "E. South America Standard Time"
        iana_tz = win_tz.get(windows_tz)
        if iana_tz is None:
            iana_tz = win_tz["E. South America Standard Time"]
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
