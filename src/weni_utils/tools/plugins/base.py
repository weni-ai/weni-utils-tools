"""
PluginBase - Base class for all plugins

Defines the interface that all plugins must follow.
"""

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class PluginBase:
    """
    Abstract base class for plugins.

    Plugins are extensions that can modify ProductConcierge behavior
    at different points in the search flow.

    Available hooks (in order of execution):
    1. before_search - Before search (modify context)
    2. after_search - After search (modify products)
    3. after_stock_check - After stock check
    4. enrich_products - Enrich with additional data
    5. finalize_result - Last modification before returning

    Example:
        class MyPlugin(PluginBase):
            def before_search(self, context, client):
                # Add region_id to context
                context.region_id = self.get_region(context.postal_code)
                return context
    """

    name: str = "base"

    def before_search(self, context: "SearchContext", client: "VTEXClient") -> "SearchContext":
        """
        Hook executed BEFORE intelligent search.

        Use this hook to:
        - Modify search parameters
        - Get region_id for regionalization
        - Get list of sellers
        - Validate input data

        Args:
            context: Search context
            client: VTEX client

        Returns:
            Modified context (or the same)
        """
        return context

    def after_search(
        self, products: Dict[str, Dict], context: "SearchContext", client: "VTEXClient"
    ) -> Dict[str, Dict]:
        """
        Hook executed AFTER intelligent search.

        Use this hook to:
        - Filter products by custom criteria
        - Modify product data
        - Add extra information

        Args:
            products: Products found in search
            context: Search context
            client: VTEX client

        Returns:
            Modified products
        """
        return products

    def after_stock_check(
        self, products_with_stock: List[Dict], context: "SearchContext", client: "VTEXClient"
    ) -> List[Dict]:
        """
        Hook executed AFTER stock check.

        Use this hook to:
        - Add special price information
        - Modify stock data
        - Filter products by custom availability

        Args:
            products_with_stock: List of products with stock
            context: Search context
            client: VTEX client

        Returns:
            Modified product list
        """
        return products_with_stock

    def enrich_products(
        self, products: Dict[str, Dict], context: "SearchContext", client: "VTEXClient"
    ) -> Dict[str, Dict]:
        """
        Hook to enrich products with additional data.

        Use this hook to:
        - Add dimensions/weight
        - Add special prices
        - Add seller information

        Args:
            products: Filtered products
            context: Search context
            client: VTEX client

        Returns:
            Enriched products
        """
        return products

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Hook to finalize the result before returning.

        Use this hook to:
        - Add messages to result
        - Send events (analytics, webhooks)
        - Modify final structure

        Args:
            result: Final result
            context: Search context

        Returns:
            Modified result
        """
        return result
