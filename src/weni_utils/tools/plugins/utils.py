"""
Plugin Utilities - Standalone functions for direct use

Utility functions that can be called directly without instantiating plugins.
These functions use the plugins internally.
"""

from typing import Any, Dict, List, Optional

from ..client import VTEXClient
from .cart_simulation import CartSimulation
from .capi import CAPI
from .weni_flow import WeniFlowTrigger


def simulate_cart(
    base_url: str,
    items: List[Dict],
    country: str = "BRA",
    postal_code: Optional[str] = None,
    timeout: int = 30,
) -> Dict:
    """
    Perform cart simulation to check availability.

    Args:
        base_url: VTEX API base URL
        items: List of items [{"id": "sku_id", "quantity": 1, "seller": "1"}]
        country: Country code (default: "BRA")
        postal_code: Postal code (optional)
        timeout: Timeout (default: 30)

    Returns:
        Simulation response with availability

    Example:
        result = simulate_cart(
            base_url="https://www.store.com.br",
            items=[
                {"id": "61556", "quantity": 1, "seller": "1"},
                {"id": "82598", "quantity": 2, "seller": "1"}
            ],
            postal_code="01310-100"
        )
    """
    client = VTEXClient(base_url=base_url, store_url=base_url, timeout=timeout)
    cart = CartSimulation(client)
    return cart.simulate(items=items, country=country, postal_code=postal_code)


def simulate_cart_batch(
    base_url: str,
    sku_id: str,
    sellers: List[str],
    postal_code: str,
    quantity: int = 1,
    max_quantity_per_seller: int = 8000,
    max_total_quantity: int = 24000,
    timeout: int = 30,
) -> Optional[Dict]:
    """
    Simulate a specific SKU with multiple sellers (used for regionalization).

    Args:
        base_url: VTEX API base URL
        sku_id: SKU ID
        sellers: List of sellers
        postal_code: Postal code
        quantity: Desired quantity (default: 1)
        max_quantity_per_seller: Maximum quantity per seller (default: 8000)
        max_total_quantity: Maximum total quantity (default: 24000)
        timeout: Timeout (default: 30)

    Returns:
        Best simulation result or None

    Example:
        result = simulate_cart_batch(
            base_url="https://www.store.com.br",
            sku_id="61556",
            sellers=["store1000", "store1003"],
            postal_code="01310-100",
            quantity=10
        )
    """
    client = VTEXClient(base_url=base_url, store_url=base_url, timeout=timeout)
    cart = CartSimulation(client)
    return cart.simulate_batch(
        sku_id=sku_id,
        sellers=sellers,
        postal_code=postal_code,
        quantity=quantity,
        max_quantity_per_seller=max_quantity_per_seller,
        max_total_quantity=max_total_quantity,
    )


def check_stock_availability(
    base_url: str,
    sku_ids: List[str],
    seller: str = "1",
    quantity: int = 1,
    country: str = "BRA",
    postal_code: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, bool]:
    """
    Check stock availability for a list of SKUs.

    Args:
        base_url: VTEX API base URL
        sku_ids: List of SKU IDs
        seller: Seller ID (default: "1")
        quantity: Quantity to check (default: 1)
        country: Country code (default: "BRA")
        postal_code: Postal code (optional)
        timeout: Timeout (default: 30)

    Returns:
        Dictionary {sku_id: available}

    Example:
        availability = check_stock_availability(
            base_url="https://www.store.com.br",
            sku_ids=["61556", "82598", "40240"],
            quantity=2
        )
        # {"61556": True, "82598": True, "40240": False}
    """
    client = VTEXClient(base_url=base_url, store_url=base_url, timeout=timeout)
    cart = CartSimulation(client)
    return cart.check_stock_availability(
        sku_ids=sku_ids,
        seller=seller,
        quantity=quantity,
        country=country,
        postal_code=postal_code,
    )


def get_product_price(
    base_url: str,
    sku_id: str,
    seller_id: str = "1",
    quantity: int = 1,
    country: str = "BRA",
    timeout: int = 30,
) -> Dict[str, Optional[float]]:
    """
    Get product price via cart simulation.

    Args:
        base_url: VTEX API base URL
        sku_id: SKU ID
        seller_id: Seller ID (default: "1")
        quantity: Quantity (default: 1)
        country: Country code (default: "BRA")
        timeout: Timeout (default: 30)

    Returns:
        Dictionary with price and list_price

    Example:
        price = get_product_price(
            base_url="https://www.store.com.br",
            sku_id="61556"
        )
        # {"price": 198.90, "list_price": 249.90}
    """
    client = VTEXClient(base_url=base_url, store_url=base_url, timeout=timeout)
    cart = CartSimulation(client)
    return cart.get_product_price(
        sku_id=sku_id, seller_id=seller_id, quantity=quantity, country=country
    )


def send_capi_event(
    auth_token: str,
    channel_uuid: str,
    contact_urn: str,
    event_type: str = "lead",
    api_url: str = "https://flows.weni.ai/conversion/",
    timeout: int = 10,
) -> bool:
    """
    Send conversion event to Meta (CAPI - Conversions API).

    Args:
        auth_token: Authentication token
        channel_uuid: Channel UUID
        contact_urn: Contact URN (e.g., whatsapp:5511999999999)
        event_type: Event type - "lead" or "purchase" (default: "lead")
        api_url: Conversions API URL (default: Weni)
        timeout: Timeout (default: 10)

    Returns:
        True if sent successfully

    Example:
        success = send_capi_event(
            auth_token="your-token",
            channel_uuid="channel-uuid",
            contact_urn="whatsapp:5511999999999",
            event_type="lead"
        )
    """
    capi = CAPI(event_type=event_type, auto_send=False, weni_capi_url=api_url, timeout=timeout)
    return capi.send_event(
        auth_token=auth_token, channel_uuid=channel_uuid, contact_urn=contact_urn, event_type=event_type
    )


def trigger_weni_flow(
    api_token: str,
    flow_uuid: str,
    contact_urn: str,
    params: Optional[Dict[str, Any]] = None,
    api_url: str = "https://flows.weni.ai/api/v2/flow_starts.json",
    timeout: int = 10,
) -> bool:
    """
    Trigger a Weni flow for a contact.

    Args:
        api_token: Weni API authentication token
        flow_uuid: Flow UUID to trigger
        contact_urn: Contact URN
        params: Extra parameters for the flow (default: {"executions": 1})
        api_url: Flows API URL (default: Weni)
        timeout: Timeout (default: 10)

    Returns:
        True if triggered successfully

    Example:
        success = trigger_weni_flow(
            api_token="your-token",
            flow_uuid="flow-uuid",
            contact_urn="whatsapp:5511999999999",
            params={"source": "concierge"}
        )
    """
    weni_flow = WeniFlowTrigger(
        flow_uuid=flow_uuid, weni_api_url=api_url, trigger_once=False, timeout=timeout
    )
    return weni_flow.trigger_flow(
        api_token=api_token, flow_uuid=flow_uuid, contact_urn=contact_urn, params=params
    )


def get_region(
    base_url: str,
    postal_code: str,
    country: str = "BRA",
    sales_channel: int = 1,
    timeout: int = 30,
) -> tuple[Optional[str], Optional[str], List[str]]:
    """
    Query the regionalization API to get region and sellers.

    Args:
        base_url: VTEX API base URL
        postal_code: Postal code (format: 00000-000 or 00000000)
        country: Country code (default: "BRA")
        sales_channel: Sales channel (default: 1)
        timeout: Request timeout (default: 30)

    Returns:
        Tuple (region_id, error_message, sellers_list)

    Example:
        region_id, error, sellers = get_region(
            base_url="https://www.store.com.br",
            postal_code="01310-100"
        )

        if error:
            print(f"Error: {error}")
        else:
            print(f"Region: {region_id}, Sellers: {sellers}")
    """
    client = VTEXClient(base_url=base_url, store_url=base_url, timeout=timeout)
    region_id, error_message, sellers = client.get_region(
        postal_code=postal_code, trade_policy=sales_channel, country_code=country
    )

    return region_id, error_message, sellers


def get_sellers_by_region(
    base_url: str,
    postal_code: str,
    country: str = "BRA",
    sales_channel: int = 1,
    timeout: int = 30,
) -> List[str]:
    """
    Return only the list of sellers for a region.

    Args:
        base_url: VTEX API base URL
        postal_code: Postal code
        country: Country code (default: "BRA")
        sales_channel: Sales channel (default: 1)
        timeout: Timeout (default: 30)

    Returns:
        List of seller IDs

    Example:
        sellers = get_sellers_by_region(
            base_url="https://www.store.com.br",
            postal_code="01310-100"
        )
        # ['store1000', 'store1003', 'store1500']
    """
    _, _, sellers = get_region(
        base_url, postal_code, country, sales_channel=sales_channel, timeout=timeout
    )
    return sellers


