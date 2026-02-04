"""
ProductConcierge - Main class for product search

This is the main class that orchestrates the entire search flow,
integrating the VTEX client, stock manager, and plugins.
"""

from typing import Any, Dict, List, Optional

from .client import VTEXClient
from .context import SearchContext
from .stock import StockManager
from .utils import Utils


class PluginBase:
    """
    Base class for plugins.

    Plugins can implement these hooks:
    - before_search: Executed before searching (can modify context)
    - after_search: Executed after searching (can modify products)
    - after_stock_check: Executed after stock check
    - enrich_products: Enrich products with additional data
    """

    def before_search(self, context: SearchContext, client: VTEXClient) -> SearchContext:
        """
        Hook executed before searching.

        Args:
            context: Search context
            client: VTEX client

        Returns:
            Modified context
        """
        return context

    def after_search(
        self, products: Dict[str, Dict], context: SearchContext, client: VTEXClient
    ) -> Dict[str, Dict]:
        """
        Hook executed after searching.

        Args:
            products: Found products
            context: Search context
            client: VTEX client

        Returns:
            Modified products
        """
        return products

    def after_stock_check(
        self, products_with_stock: List[Dict], context: SearchContext, client: VTEXClient
    ) -> List[Dict]:
        """
        Hook executed after stock check.

        Args:
            products_with_stock: Products with available stock
            context: Search context
            client: VTEX client

        Returns:
            Modified products
        """
        return products_with_stock

    def enrich_products(
        self, products: Dict[str, Dict], context: SearchContext, client: VTEXClient
    ) -> Dict[str, Dict]:
        """
        Hook to enrich products with additional data.

        Args:
            products: Products to enrich
            context: Search context
            client: VTEX client

        Returns:
            Enriched products
        """
        return products

    def finalize_result(self, result: Dict[str, Any], context: SearchContext) -> Dict[str, Any]:
        """
        Hook to finalize the result before returning.

        Args:
            result: Final result
            context: Search context

        Returns:
            Modified result
        """
        return result


class ProductConcierge(Utils, VTEXClient, StockManager, PluginBase):
    """
    Main class for VTEX product search.

    Orchestrates the complete search flow:
    1. Executes before_search hooks from plugins
    2. Performs intelligent search
    3. Executes after_search hooks from plugins
    4. Checks stock availability
    5. Executes after_stock_check hooks from plugins
    6. Enriches products with plugins
    7. Filters and formats the final result

    Example:
        from weni_utils.tools import ProductConcierge
        from weni_utils.tools.plugins import Regionalization, Wholesale

        concierge = ProductConcierge(
            base_url="https://loja.vtexcommercestable.com.br",
            store_url="https://loja.com.br",
            plugins=[Regionalization(), Wholesale()]
        )

        # Full search with plugins and stock verification
        result = concierge.search(
            product_name="furadeira",
            postal_code="01310-100"
        )

        # Or direct access to VTEXClient methods
        raw_products = concierge.intelligent_search("furadeira")
    """

    def __init__(
        self,
        base_url: str,
        store_url: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
        plugins: Optional[List[PluginBase]] = None,
        max_products: int = 20,
        max_variations: int = 5,
        max_payload_kb: int = 20,
        utm_source: Optional[str] = None,
        priority_categories: Optional[List[str]] = None,
    ):
        """
        Initializes ProductConcierge.

        Args:
            base_url: VTEX API base URL
            store_url: Store URL
            vtex_app_key: VTEX App Key (optional)
            vtex_app_token: VTEX App Token (optional)
            plugins: List of plugins to use
            max_products: Maximum products to return
            max_variations: Maximum variations per product
            max_payload_kb: Maximum payload size in KB
            utm_source: UTM source for links
            priority_categories: Categories with special stock logic
        """
        super().__init__(base_url=base_url, 
                        store_url=store_url, 
                        vtex_app_key=vtex_app_key, 
                        vtex_app_token=vtex_app_token
                        )
        self.plugins = plugins or []

        # Configurations
        self.max_products = max_products
        self.max_variations = max_variations
        self.max_payload_kb = max_payload_kb
        self.utm_source = utm_source
        self.priority_categories = priority_categories or []

    def search(
        self,
        product_name: str,
        brand_name: str = "",
        postal_code: Optional[str] = None,
        quantity: int = 1,
        delivery_type: Optional[str] = None,
        credentials: Optional[Dict[str, Any]] = None,
        contact_info: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Performs a full product search.

        Args:
            product_name: Name of the product to search
            brand_name: Brand of the product (optional)
            postal_code: Postal code for regionalization (optional)
            quantity: Desired quantity
            delivery_type: Delivery type (optional)
            credentials: Extra credentials for plugins
            contact_info: Contact info for plugins
            **kwargs: Extra parameters for plugins

        Returns:
            Dictionary with found products and extra information
        """
        # 1. Create search context
        context = SearchContext(
            product_name=product_name,
            brand_name=brand_name,
            postal_code=postal_code,
            quantity=quantity,
            delivery_type=delivery_type,
            credentials=credentials or {},
            contact_info=contact_info or {},
        )

        # Add extra kwargs to context
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)

        # 2. Get region
        if context.postal_code:
            context.region_id, context.region_error, context.sellers = self.get_region(
                postal_code=context.postal_code,
                trade_policy=context.trade_policy,
                country_code=context.country_code
            )

        # 2. Perform intelligent search (returns raw data)
        raw_products = self.intelligent_search(
            product_name=context.product_name,
            brand_name=context.brand_name,
            region_id=context.region_id,
        )

        # 3. Process raw products (format, filter, limit)
        products = self.process_products(
            raw_products=raw_products,
            max_products=self.max_products,
            max_variations=self.max_variations,
            utm_source=self.utm_source,
        )

        products_with_stock = self.check_availability_with_sellers(
            client=self,
            products=products,
            context=context,
            sellers=context.sellers,
            priority_categories=self.priority_categories,
        )


        # 5. Filter products, keeping only those with stock
        filtered_products = self.filter_products_with_stock(
            products, products_with_stock
        )

        # 6. Limit payload size
        filtered_products = self.limit_payload_size(
            filtered_products, self.max_payload_kb
        )

        return filtered_products

    def _build_result(self, products: Dict[str, Dict], context: SearchContext) -> Dict[str, Any]:
        """
        Builds the final search result.

        Args:
            products: Filtered products
            context: Search context

        Returns:
            Formatted result
        """
        result = {}

        # Add extra data from context first
        if context.extra_data:
            result.update(context.extra_data)

        # Add region message if present
        if context.region_error:
            result["region_message"] = context.region_error

        # Add products
        result.update(products)

        return result

    def search_by_sku(self, sku_id: str) -> Optional[Dict]:
        """
        Search for a specific product by SKU.

        Args:
            sku_id: SKU ID

        Returns:
            Product data or None
        """
        return self.get_product_by_sku(sku_id)

    def get_sku_details(self, sku_id: str) -> Dict:
        """
        Get details of a SKU (dimensions, weight, etc).

        Args:
            sku_id: SKU ID

        Returns:
            SKU details
        """
        return self.get_sku_details(sku_id)
