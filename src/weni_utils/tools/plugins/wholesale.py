"""
Wholesale Plugin - Wholesale Prices

Plugin for clients that work with wholesale prices (minimum quantity).
Adds minQuantity and valueAtacado information to products.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import requests

from .base import PluginBase

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class Wholesale(PluginBase):
    """
    Wholesale prices plugin.

    Features:
    - Gets wholesale price (valueAtacado) by SKU
    - Gets minimum quantity (minQuantity) for wholesale price
    - Adds information to products after stock check

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[
                Wholesale(
                    fixed_price_url="https://www.store.com.br/fixedprices"
                )
            ]
        )
    """

    name = "wholesale"

    def __init__(self, fixed_price_url: Optional[str] = None, timeout: int = 10):
        """
        Initialize the wholesale plugin.

        Args:
            fixed_price_url: Base URL for fixed prices API
                            If not provided, tries to derive from store URL
            timeout: Request timeout
        """
        self.fixed_price_url = fixed_price_url
        self.timeout = timeout
        self._cache: Dict[str, Dict] = {}

    def after_stock_check(
        self, products_with_stock: List[Dict], context: "SearchContext", client: "VTEXClient"
    ) -> List[Dict]:
        """
        Add wholesale price information after stock check.
        """
        if not products_with_stock:
            return products_with_stock

        # Define base URL if not provided
        base_url = self.fixed_price_url
        if not base_url:
            # Try to derive from client's store_url
            base_url = f"{client.store_url}/fixedprices"

        enriched_products = []

        for product in products_with_stock:
            sku_id = product.get("sku_id")
            seller_id = product.get("sellerId")

            if sku_id and seller_id:
                fixed_price_data = self._get_fixed_price(base_url, seller_id, sku_id)

                product_enriched = product.copy()
                product_enriched.update(
                    {
                        "minQuantity": fixed_price_data.get("minQuantity"),
                        "valueAtacado": fixed_price_data.get("valueAtacado"),
                    }
                )
                enriched_products.append(product_enriched)
            else:
                enriched_products.append(product)

        return enriched_products

    def _get_fixed_price(
        self, base_url: str, seller_id: str, sku_id: str
    ) -> Dict[str, Optional[Any]]:
        """
        Get fixed price (wholesale) for a SKU.

        Args:
            base_url: Base URL for fixed prices API
            seller_id: Seller ID
            sku_id: SKU ID

        Returns:
            Dictionary with minQuantity and valueAtacado
        """
        cache_key = f"{seller_id}:{sku_id}"

        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = f"{base_url}/{seller_id}/{sku_id}/1"

        default_response = {"minQuantity": None, "valueAtacado": None}

        try:
            response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                return default_response

            data = response.json()

            result = {
                "minQuantity": data.get("minQuantity") if isinstance(data, dict) else None,
                "valueAtacado": data.get("value") if isinstance(data, dict) else None,
            }

            # Save to cache
            self._cache[cache_key] = result

            return result

        except Exception as e:
            print(f"ERROR: Error getting wholesale price: {e}")
            return default_response

    def clear_cache(self) -> None:
        """Clear the price cache."""
        self._cache.clear()
