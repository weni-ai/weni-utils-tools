"""
Modular functions for VTEX integration

Each function is independent and can be called separately.
All parameters are configurable with sensible defaults.

This module uses VTEXClient internally to avoid code duplication.
All functions maintain the same public API for backward compatibility.
"""

from typing import Any, Dict, List, Optional

from .client import VTEXClient

# =============================================================================
# PRODUCT SEARCH
# =============================================================================


def search_products(
    base_url: str,
    product_name: str,
    brand_name: str = "",
    color: Optional[str] = None,
    region_id: Optional[str] = None,
    trade_policy_id: Optional[int] = None,
    cluster_id: Optional[int] = None,
    store_url: Optional[str] = None,
    hide_unavailable: bool = True,
    max_products: int = 20,
    max_variations: int = 5,
    utm_source: Optional[str] = None,
    timeout: int = 30,
    allow_redirect: bool = False,
) -> Dict[str, Dict]:
    """
    Search products using VTEX Intelligent Search API.

    Args:
        base_url: VTEX API base URL (e.g., https://store.vtexcommercestable.com.br)
        product_name: Product name to search
        brand_name: Product brand (optional)
        color: Product color (optional)
        region_id: Region ID for regionalization (optional)
        trade_policy_id: Trade policy / sales channel ID to filter products (optional)
        cluster_id: Filter the search by collection, following the format (optional)
        store_url: Store URL for product links (optional, uses base_url if not provided)
        hide_unavailable: Whether to hide unavailable products (default: True)
        max_products: Maximum number of products (default: 20)
        max_variations: Maximum variations per product (default: 5)
        utm_source: UTM source for links (optional)
        timeout: Request timeout in seconds (default: 30)
        allow_redirect: Whether to allow redirects (default: False)

    Returns:
        Dictionary with structured products {product_name: data}

    Example:
        products = search_products(
            base_url="https://www.store.com.br",
            product_name="drill",
            max_products=10
        )

        # With trade policy (sales channel)
        products = search_products(
            base_url="https://www.store.com.br",
            product_name="drill",
            trade_policy_id=2
        )
    """
    store_url = store_url or base_url

    # Create client instance
    client = VTEXClient(
        base_url=base_url,
        store_url=store_url,
        timeout=timeout,
    )

    # Build query with color if provided
    query_name = f"{product_name} {brand_name} {color}".strip() if color else f"{product_name} {brand_name}".strip()

    # Get raw products from API
    raw_products = client.intelligent_search(
        product_name=query_name,
        brand_name="",  # Already included in query_name
        region_id=region_id,
        hide_unavailable=hide_unavailable,
        trade_policy_id=trade_policy_id,
        cluster_id=cluster_id,
        allow_redirect=allow_redirect,
    )

    # Process products (format, filter, limit)
    return client.process_products(
        raw_products=raw_products,
        max_products=max_products,
        max_variations=max_variations,
        utm_source=utm_source,
    )


def search_product_by_sku(
    base_url: str,
    sku_id: str,
    region_id: Optional[str] = None,
    trade_policy_id: Optional[int] = None,
    cluster_id: Optional[int] = None,
    store_url: Optional[str] = None,
    timeout: int = 30,
) -> Optional[Dict]:
    """
    Search for a specific product by SKU ID.

    Args:
        base_url: VTEX API base URL
        sku_id: SKU ID
        region_id: Region ID for regionalization (optional)
        trade_policy_id: Trade policy / sales channel ID to filter products (optional)
        cluster_id: Filter the search by collection (optional)
        store_url: Store URL (optional)
        timeout: Request timeout (default: 30)

    Returns:
        Product data or None if not found

    Example:
        product = search_product_by_sku(
            base_url="https://www.store.com.br",
            sku_id="61556"
        )

        # With trade policy
        product = search_product_by_sku(
            base_url="https://www.store.com.br",
            sku_id="61556",
            trade_policy_id=2
        )
    """
    store_url = store_url or base_url

    # Create client instance
    client = VTEXClient(
        base_url=base_url,
        store_url=store_url,
        timeout=timeout,
    )

    # Use get_product_by_sku from client
    # Note: get_product_by_sku doesn't support region_id, trade_policy_id, cluster_id yet
    # For now, we use the basic method
    return client.get_product_by_sku(sku_id)

def get_nested_value(data, path: str):
        """
        Get a nested value from a dictionary.
        """
        current = data

        for part in path.split("."):
            if isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    return None

            elif isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]

            else:
                return None

        return current
    
def normalize_field_name(field_path: str) -> str:
    """
    Normalize a field name.
    """
    return field_path.split(".")[-1]



# =============================================================================
# SKU DETAILS
# =============================================================================


def get_sku_details(
    base_url: str,
    sku_id: str,
    vtex_app_key: Optional[str] = None,
    vtex_app_token: Optional[str] = None,
    timeout: int = 30,
) -> Dict:
    """
    Get SKU details (dimensions, weight, etc).
    Requires VTEX credentials for private API.

    Args:
        base_url: VTEX API base URL
        sku_id: SKU ID
        vtex_app_key: VTEX App Key (optional, required for complete data)
        vtex_app_token: VTEX App Token (optional, required for complete data)
        timeout: Timeout (default: 30)

    Returns:
        Dictionary with SKU details

    Example:
        details = get_sku_details(
            base_url="https://www.store.com.br",
            sku_id="61556",
            vtex_app_key="your-app-key",
            vtex_app_token="your-app-token"
        )
    """
    # Create client instance with credentials
    client = VTEXClient(
        base_url=base_url,
        store_url=base_url,  # store_url not needed for this call
        vtex_app_key=vtex_app_key,
        vtex_app_token=vtex_app_token,
        timeout=timeout,
    )

    # Use get_sku_details from client
    return client.get_sku_details(sku_id)