"""
Weni Tools - Agentes e funcionalidades para integração VTEX

Estrutura:
- tools/ - Agentes fixos (ProductConcierge, OrderConcierge)
- plugins/ - Funcionalidades reutilizáveis (simulação, CAPI, etc)

Usage (agentes):
    from weni_utils.tools import ProductConcierge, OrderConcierge

    concierge = ProductConcierge(base_url, store_url)
    result = concierge.search("drill", postal_code="01310-100")

Usage (funcionalidades dos plugins):
    from weni_utils.tools.plugins import simulate_cart, get_region, send_capi_event

    # Simular carrinho
    result = simulate_cart(base_url, items, postal_code="01310-100")

    # Obter região
    region_id, error, sellers = get_region(base_url, "01310-100")

    # Enviar evento CAPI
    send_capi_event(auth_token, channel_uuid, contact_urn)
"""

from .client import VTEXClient, OrderDataProxy
from .concierge import ProductConcierge
from .context import SearchContext
from .functions import get_sku_details, search_product_by_sku, search_products
from .orders import OrderConcierge
from .plugins import (
    check_stock_availability,
    get_product_price,
    get_region,
    get_sellers_by_region,
    get_wholesale_price,
    send_capi_event,
    simulate_cart,
    simulate_cart_batch,
    trigger_weni_flow,
)
from .stock import StockManager

__all__ = [
    # Agentes fixos
    "ProductConcierge",
    "OrderConcierge",
    "OrderDataProxy",
    # Classes base
    "VTEXClient",
    "StockManager",
    "SearchContext",
    # Funções de busca (mantidas em functions.py por compatibilidade)
    "search_products",
    "search_product_by_sku",
    "get_sku_details",
    # Funcionalidades dos plugins
    "simulate_cart",
    "simulate_cart_batch",
    "check_stock_availability",
    "get_product_price",
    "get_region",
    "get_sellers_by_region",
    "get_wholesale_price",
    "send_capi_event",
    "trigger_weni_flow",
]
