"""
Regionalization Plugin - Postal Code Based Regionalization

Plugin for clients that need postal code based regionalization.
Determines the region and available sellers before search.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import PluginBase

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class Regionalization(PluginBase):
    """
    Postal code regionalization plugin.

    Features:
    - Gets region_id based on postal code
    - Gets list of available sellers for the region
    - Applies specific seller rules (e.g., Mooca rules)
    - Adds error message if region is not served

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[Regionalization()]
        )

        # With specific seller rules
        concierge = ProductConcierge(
            plugins=[
                Regionalization(
                    seller_rules={
                        "mooca_sellers": ["store1000", "store1003", "store1500"],
                        "pickup_sellers": ["store1000", "store1003"],
                        "delivery_sellers": ["store1000", "store1500"],
                    },
                    priority_categories=[
                        "/Category/Subcategory/",
                    ]
                )
            ]
        )
    """

    name = "regionalization"

    def __init__(
        self,
        seller_rules: Optional[Dict[str, List[str]]] = None,
        priority_categories: Optional[List[str]] = None,
        require_delivery_type_for_priority: bool = False,
        default_seller: str = "1",
    ):
        """
        Initialize the regionalization plugin.

        Args:
            seller_rules: Custom seller rules by region/type
            priority_categories: Categories that require special logic
            require_delivery_type_for_priority: If True, requires delivery_type for priority categories
            default_seller: Default seller when there is no regionalization
        """
        self.seller_rules = seller_rules or {}
        self.priority_categories = priority_categories or []
        self.require_delivery_type_for_priority = require_delivery_type_for_priority
        self.default_seller = default_seller

    def before_search(self, context: "SearchContext", client: "VTEXClient") -> "SearchContext":
        """
        Get region and sellers before search.
        """
        if not context.postal_code:
            # No postal code, use default seller
            context.sellers = [self.default_seller]
            return context

        # Query regionalization API
        region_id, error, sellers = client.get_region(
            context.postal_code, context.trade_policy, context.country_code
        )

        context.region_id = region_id
        context.region_error = error

        if error:
            # Use default seller in case of error
            context.sellers = [self.default_seller]
        else:
            context.sellers = sellers

        # Apply custom seller rules
        context.sellers = self._apply_seller_rules(
            context.sellers, context.delivery_type, context.seller_rules
        )

        return context

    def _apply_seller_rules(
        self, sellers: List[str], delivery_type: Optional[str], seller_rules: Dict[str, List[str]]
    ) -> List[str]:
        """
        Apply custom seller rules.

        Args:
            sellers: List of sellers from the region
            delivery_type: Delivery type (Pickup/Delivery)

        Returns:
            Filtered list of sellers
        """
        if not seller_rules:
            return sellers

        if seller_rules and all(seller in seller_rules for seller in sellers):
            if delivery_type == "Retirada":
                return seller_rules.get("retirada_sellers", sellers)
            elif delivery_type == "Entrega":
                return seller_rules.get("entrega_sellers", sellers)

        return sellers

    def after_search(
        self, products: Dict[str, Dict], context: "SearchContext", client: "VTEXClient"
    ) -> Dict[str, Dict]:
        """
        Check if delivery_type is needed for priority categories.
        """
        if not self.require_delivery_type_for_priority:
            return products

        if not products:
            return products

        # Check if any product is from a priority category
        has_priority = False
        for product_name, product_data in products.items():
            categories = product_data.get("categories", [])
            if self._is_priority_category(categories):
                has_priority = True
                break

        # If has priority category and no delivery_type, add error
        if has_priority and not context.delivery_type:
            mooca_sellers = self.seller_rules.get("mooca_sellers", [])
            if mooca_sellers and all(s in mooca_sellers for s in context.sellers):
                context.add_to_result(
                    "delivery_type_required",
                    "For flooring and tile products in your region, "
                    "you need to specify the delivery type (Pickup or Delivery).",
                )

        return products

    def _is_priority_category(self, categories: List[str]) -> bool:
        """Check if product belongs to a priority category."""
        if not categories or not self.priority_categories:
            return False

        for category in categories:
            if category in self.priority_categories:
                return True

        return False

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Add region message to result if necessary.
        """
        # Region message is already added by ProductConcierge
        # This hook can be used to add extra information
        return result
