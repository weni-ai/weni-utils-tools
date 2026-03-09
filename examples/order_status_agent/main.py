"""
Example: Order Status Agent

This example demonstrates how to use OrderConcierge to search for orders
by document (CPF/CNPJ) or order ID.

Features:
1. Search by Document: Returns a list of orders (complete and incomplete)
2. Search by ID: Returns details of a specific order
"""

from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

from weni_utils.tools import OrderConcierge


class OrderStatusTool(Tool):
    """
    Unified tool for order lookup.

    Accepts 'document' or 'order_id' as parameters.
    """

    def execute(self, context: Context) -> TextResponse:
        # Extract parameters
        document = context.parameters.get("document")
        order_id = context.parameters.get("orderID")

        # Extract credentials
        base_url_vtex = context.credentials.get("BASE_URL_VTEX", "")
        store_url_vtex = context.credentials.get("STORE_URL_VTEX", "")
        vtex_app_key = context.credentials.get("VTEX_API_APPKEY", "")
        vtex_app_token = context.credentials.get("VTEX_API_APPTOKEN", "")

        if not base_url_vtex:
            return TextResponse(data={"error": "BASE_URL_VTEX not configured"})

        # Initialize the concierge
        concierge = OrderConcierge(
            base_url_vtex=base_url_vtex,
            store_url_vtex=store_url_vtex,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token,
        )

        # Search by order ID
        if order_id:
            result = concierge.get_order_details(order_id)
            return TextResponse(data=result)

        # Search by document
        if document:
            result = concierge.search_orders(document)
            return TextResponse(data=result)

        return TextResponse(data={"error": "Either 'document' or 'orderID' parameter is required"})
