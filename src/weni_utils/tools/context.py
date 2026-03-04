"""
SearchContext - Shared context during search

This object is passed between the core and plugins, allowing each
plugin to add/modify information as needed.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchContext:
    """
    Search context that flows through the plugin pipeline.

    Attributes:
        product_name: Name of the product to search
        brand_name: Product brand (optional)
        postal_code: Postal code for regionalization (optional)
        quantity: Desired quantity
        country_code: Country code (default: BRA)

        # Fields that plugins can populate
        region_id: Region ID (populated by Regionalization plugin)
        sellers: List of available sellers
        region_error: Region error message
        delivery_type: Delivery type (Pickup/Delivery)

        # Fields for result
        extra_data: Extra data that plugins can add to the result
    """

    # Input parameters
    product_name: str
    brand_name: str = ""
    postal_code: Optional[str] = None
    quantity: int = 1
    country_code: str = "BRA"
    delivery_type: Optional[str] = None
    trade_policy: Optional[int] = 1

    # Fields populated by plugins
    region_id: Optional[str] = None
    sellers: List[str] = field(default_factory=list)
    seller_rules: Dict[str, List[str]] = field(default_factory=dict)
    region_error: Optional[str] = None

    # Credentials and extra settings
    credentials: Dict[str, Any] = field(default_factory=dict)
    contact_info: Dict[str, Any] = field(default_factory=dict)

    # Extra data for final result
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def add_to_result(self, key: str, value: Any) -> None:
        """Add extra data that will be included in the final result"""
        self.extra_data[key] = value

    def get_credential(self, key: str, default: Any = None) -> Any:
        """Get a credential by name"""
        return self.credentials.get(key, default)

    def get_contact(self, key: str, default: Any = None) -> Any:
        """Get contact information"""
        return self.contact_info.get(key, default)
