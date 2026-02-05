"""
Weni Tools - Agents and functionalities for VTEX integration

Structure:
- tools/ - Fixed agents (ProductConcierge, OrderConcierge)
- plugins/ - Reusable functionalities (simulation, CAPI, etc)

Usage (agents):
    from weni_utils.tools import ProductConcierge, OrderConcierge

    concierge = ProductConcierge(base_url, store_url)
    result = concierge.search("drill", postal_code="01310-100")

Usage (plugin functionalities):
    from weni_utils.tools.plugins import simulate_cart, get_region, send_capi_event

    # Simulate cart
    result = simulate_cart(base_url, items, postal_code="01310-100")

    # Get region
    region_id, error, sellers = get_region(base_url, "01310-100")

    # Send CAPI event
    send_capi_event(auth_token, channel_uuid, contact_urn)
"""

from .client import VTEXClient
from .concierge import ProductConcierge
from .context import SearchContext
from .functions import get_sku_details, search_product_by_sku, search_products
from .orders import OrderConcierge
from .plugins import (
    check_stock_availability,
    get_product_price,
    get_region,
    get_sellers_by_region,
    send_capi_event,
    simulate_cart,
    simulate_cart_batch,
    trigger_weni_flow,
)
from .stock import StockManager

__all__ = [
    # Fixed agents
    "ProductConcierge",
    "OrderConcierge",
    # Base classes
    "VTEXClient",
    "StockManager",
    "SearchContext",
    # Search functions (kept in functions.py for compatibility)
    "search_products",
    "search_product_by_sku",
    "get_sku_details",
    # Plugin functionalities
    "simulate_cart",
    "simulate_cart_batch",
    "check_stock_availability",
    "get_product_price",
    "get_region",
    "get_sellers_by_region",
    "send_capi_event",
    "trigger_weni_flow",
]
