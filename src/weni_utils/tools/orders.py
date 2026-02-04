"""
OrderConcierge - Main class for order search

This class orchestrates order search and data handling.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import pytz

from .client import VTEXClient


class OrderConcierge:
    """
    Main class for VTEX order search.

    Example:
        concierge = OrderConcierge(
            base_url="https://store.vtexcommercestable.com.br",
            store_url="https://store.com.br"
        )

        orders = concierge.search_orders("12345678900")
        order_details = concierge.get_order_details("123456")
    """

    def __init__(
        self,
        base_url: str,
        store_url: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
    ):
        """
        Initialize OrderConcierge.

        Args:
            base_url: VTEX API base URL
            store_url: Store URL
            vtex_app_key: VTEX App Key (optional)
            vtex_app_token: VTEX App Token (optional)
        """
        self.client = VTEXClient(
            base_url=base_url,
            store_url=store_url,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token,
        )

    def _convert_cents(self, data: Any) -> Any:
        """
        Convert values from cents to currency.

        Args:
            data: Data to convert

        Returns:
            Converted data
        """
        currency_fields = [
            "totalValue",
            "value",
            "totals",
            "itemPrice",
            "sellingPrice",
            "price",
            "listPrice",
            "costPrice",
            "basePrice",
            "fixedPrice",
            "shippingEstimate",
            "tax",
            "discount",
            "total",
            "subtotal",
            "freight",
            "marketingData",
            "paymentData",
        ]

        if isinstance(data, dict):
            converted_data = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    converted_data[key] = self._convert_cents(value)
                elif isinstance(value, (int, float)) and any(
                    field in key.lower() for field in currency_fields
                ):
                    converted_data[key] = round(value / 100, 2) if value is not None else value
                else:
                    converted_data[key] = value
            return converted_data
        elif isinstance(data, list):
            return [self._convert_cents(item) for item in data]
        else:
            return data

    def search_orders(self, document: str, incomplete_orders: bool = False) -> Dict[str, Any]:
        """
        Search orders by document.

        Args:
            document: Customer document
            incomplete_orders: Whether to include incomplete orders
                Default is False (only complete orders)
        Returns:
            Dictionary with orders and current date
        """
        orders_data = self.client.get_orders_by_document(document, incomplete_orders=incomplete_orders)
        converted_orders = self._convert_cents(orders_data)

        return {
            "orders": converted_orders,
            "brazil_time": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
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

        converted_order = self._convert_cents(order_data)

        return {
            "order": converted_order,
            "brazil_time": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
        }
