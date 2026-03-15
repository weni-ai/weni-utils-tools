"""
ProductConcierge - Main class for product search

This is the main class that orchestrates the entire search flow,
integrating the VTEX client, stock manager, and plugins.
"""

import logging
from typing import Any, Dict, List, Optional

from weni.context import Context

from .client import VTEXClient
from .context import SearchContext
from .stock import StockManager

logger = logging.getLogger(__name__)


class ProductConcierge(VTEXClient, StockManager):
    """
    Main class for VTEX product search.

    Orchestrates the complete search flow:
    1. Performs intelligent search
    2. Checks stock availability
    3. Filters and formats the final result

    Example:
        from weni_utils.tools import ProductConcierge
        from weni_utils.tools.plugins import Regionalization

        concierge = ProductConcierge(
            base_url_vtex="https://loja.vtexcommercestable.com.br",
            store_url_vtex="https://loja.com.br",
            plugins=[Regionalization()]
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
        base_url_vtex: str,
        store_url_vtex: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
        max_products: int = 20,
        max_variations: int = 5,
        max_payload_kb: int = 20,
        utm_source: Optional[str] = "weni_concierge",
        priority_categories: Optional[List[str]] = None,
    ):
        """
        Initializes ProductConcierge.

        Args:
            base_url_vtex: VTEX API base URL
            store_url_vtex: Store URL
            vtex_app_key: VTEX App Key (optional)
            vtex_app_token: VTEX App Token (optional)
            max_products: Maximum products to return
            max_variations: Maximum variations per product
            max_payload_kb: Maximum payload size in KB
            utm_source: UTM source for links
            priority_categories: Categories with special stock logic
        """
        super().__init__(
            base_url_vtex=base_url_vtex,
            store_url_vtex=store_url_vtex,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token,
        )

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
        context: Optional[Context] = None,
        vtex_segment_raw: Optional[str] = None,
        prefer_default_seller: bool = True,
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
            context: Weni Context object. When provided, vtex_segment is
                automatically extracted from context.contact fields.
            vtex_segment_raw: Raw JSON string with segment data. Overrides
                the value from context if both are provided.
            prefer_default_seller: Prioritize the default seller over
                the first seller with stock
            **kwargs: Extra parameters for plugins

        Returns:
            Dictionary with found products and extra information
        """
        # 1. Create search context
        search_ctx = SearchContext(
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
            if hasattr(search_ctx, key):
                setattr(search_ctx, key, value)

        # 2. Get region
        if search_ctx.postal_code:
            search_ctx.region_id, search_ctx.region_error, search_ctx.sellers = self.get_region(
                postal_code=search_ctx.postal_code,
                trade_policy=search_ctx.trade_policy,
                country_code=search_ctx.country_code,
            )

        # 3. Resolve vtex_segment: explicit param > auto-extract from Weni Context
        if not vtex_segment_raw and context is not None:
            fields = context.contact.get("fields", {}) or {}
            vtex_segment_raw = fields.get("vtex_segment")

        vtex_segment_cookie = self.encode_vtex_segment(vtex_segment_raw)

        # 4. Perform intelligent search (returns raw data)
        raw_products = self.intelligent_search(
            product_name=search_ctx.product_name,
            brand_name=search_ctx.brand_name,
            region_id=search_ctx.region_id,
            vtex_segment=vtex_segment_cookie,
        )

        # 5. Process raw products (format, filter, limit)
        products = self.process_products(
            raw_products=raw_products,
            max_products=self.max_products,
            max_variations=self.max_variations,
            utm_source=self.utm_source,
            prefer_default_seller=prefer_default_seller,
        )

        # 6. Limit payload size
        filtered_products = self.limit_payload_size(products, self.max_payload_kb)

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
            logger.warning("Region error in result: %s", context.region_error)
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
