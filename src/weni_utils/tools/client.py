"""
VTEXClient - Client for VTEX APIs

This module contains all communication logic with VTEX APIs,
extracted and consolidated from existing agents.
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

from .proxy import ProxyRequest
from .utils import Utils

logger = logging.getLogger(__name__)


@dataclass
class ProductVariation:
    """Represents a product variation (SKU)"""

    sku_id: str
    sku_name: str
    variations: str  # Format: "[Color: White, Size: M]"
    price: Optional[float] = None
    spot_price: Optional[float] = None
    list_price: Optional[float] = None
    pix_price: Optional[float] = None
    credit_card_price: Optional[float] = None
    image_url: str = ""
    seller_id: Optional[str] = None
    available_quantity: int = 0


@dataclass
class Product:
    """Represents a product with its variations"""

    name: str
    description: str
    brand: str
    product_link: str
    image_url: str
    categories: List[str]
    specification_groups: List[Dict]
    variations: List[ProductVariation]


class VTEXClient(ProxyRequest, Utils):
    """
    Client for communication with VTEX APIs.

    Centralizes all API calls for:
    - Intelligent Search (product search)
    - Cart Simulation (stock verification)
    - Regions (regionalization)
    - SKU Details (product details)

    Example:
        client = VTEXClient(
            base_url_vtex="https://store.vtexcommercestable.com.br",
            store_url_vtex="https://store.com.br"
        )

        products = client.intelligent_search("drill")
    """

    def __init__(
        self,
        base_url_vtex: str,
        store_url_vtex: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the VTEX client.

        Args:
            base_url_vtex: VTEX API base URL (e.g., https://store.vtexcommercestable.com.br)
            store_url_vtex: Store URL (e.g., https://store.com.br)
            vtex_app_key: App Key for authenticated APIs (optional)
            vtex_app_token: App Token for authenticated APIs (optional)
            timeout: Request timeout in seconds
        """
        self.base_url_vtex = base_url_vtex.rstrip("/")
        self.store_url_vtex = store_url_vtex.rstrip("/")
        if not self._validate_base_url_and_store_url_vtex():
            raise ValueError("Base URL or store URL VTEX is invalid")

        self.vtex_app_key = vtex_app_key
        self.vtex_app_token = vtex_app_token
        self.timeout = timeout

    def _get_auth_headers(self) -> Dict[str, str]:
        """Return authentication headers if available"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.vtex_app_key and self.vtex_app_token:
            headers["X-VTEX-API-AppKey"] = self.vtex_app_key
            headers["X-VTEX-API-AppToken"] = self.vtex_app_token

        return headers

    def _validate_base_url_and_store_url_vtex(self) -> bool:
        """Validate if the base URL and store URL VTEX are valid"""
        if not self.base_url_vtex or not self.store_url_vtex:
            return False

        if not self.base_url_vtex.startswith("https://") or not self.store_url_vtex.startswith(
            "https://"
        ):
            return False

        if not self.base_url_vtex.endswith((".vtexcommercestable.com.br", ".myvtex.com")):
            return False

        return True

    def intelligent_search(
        self,
        product_name: str,
        brand_name: str = "",
        region_id: Optional[str] = None,
        hide_unavailable: bool = True,
        trade_policy_id: Optional[int] = None,
        cluster_id: Optional[int] = None,
        allow_redirect: bool = False,
        vtex_segment: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search products using VTEX Intelligent Search API.

        Returns only raw data from the API, without processing.
        Formatting, filtering, and limiting logic should be done by the agent.

        Args:
            product_name: Product name to search
            brand_name: Product brand (optional)
            region_id: Region ID for regionalization (optional)
            hide_unavailable: Whether to hide unavailable products
            trade_policy_id: Trade policy / sales channel ID (optional)
            cluster_id: Filter by collection ID (optional)
            allow_redirect: Whether to allow redirects (optional)

        Returns:
            List of raw products from VTEX API
        """
        # Build URL with or without regionalization
        query = f"{product_name} {brand_name}".strip()

        path_segments = []
        if trade_policy_id:
            path_segments.append(f"trade-policy/{trade_policy_id}")
        if region_id:
            path_segments.append(f"region-id/{region_id}")
        if cluster_id:
            path_segments.append(f"productClusterIds/{cluster_id}")

        path = "/".join(path_segments)
        if path:
            path = f"{path}/"

        search_url = (
            f"{self.base_url_vtex}/api/io/_v/api/intelligent-search/product_search/{path}"
            f"?query={quote(query)}&simulationBehavior=default"
            f"&hideUnavailableItems={str(hide_unavailable).lower()}"
            f"&allowRedirect={str(allow_redirect).lower()}"
        )

        headers = {}
        if vtex_segment:
            headers["Cookie"] = f"vtex_segment={vtex_segment}"

        try:
            response = requests.get(search_url, timeout=self.timeout, headers=headers or None)
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])

        except requests.exceptions.RequestException as e:
            logger.error("Intelligent search failed for query=%r: %s", query, e)
            return []
        except json.JSONDecodeError as e:
            logger.error("Intelligent search JSON decode error for query=%r: %s", query, e)
            return []

    def cart_simulation(
        self,
        items: List[Dict],
        country: str = "BRA",
        postal_code: Optional[str] = None,
        sales_channel: Optional[int] = None,
    ) -> Dict:
        """
        Perform cart simulation to check availability.

        Args:
            items: List of items [{id, quantity, seller}]
            country: Country code
            postal_code: Postal code (optional)
            sales_channel: Sales channel ID (optional)

        Returns:
            Simulation response
        """
        url = f"{self.base_url_vtex}/api/checkout/pub/orderForms/simulation"
        if sales_channel is not None:
            url += f"?sc={sales_channel}"

        payload: Dict = {"items": items, "country": country}
        if postal_code:
            payload["postalCode"] = postal_code

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error("Cart simulation failed (%d items): %s", len(items), e)
            return {"items": []}

    def _build_batch_items(
        self,
        skus: List[Dict[str, int]],
        sellers: List[str],
        max_quantity_per_seller: int = 8000,
        max_total_quantity: int = 24000,
    ) -> List[Dict]:
        """
        Build items list for batch simulation (SKUs × sellers cross-product).

        Args:
            skus: List of SKUs with quantities
            sellers: List of sellers
            max_quantity_per_seller: Maximum quantity per seller
            max_total_quantity: Maximum total quantity

        Returns:
            List of items for simulation
        """
        num_sellers = len(sellers)
        items = []

        for sku in skus:
            sku_id = sku.get("sku_id")
            quantity = int(sku.get("quantity", 1))

            if not sku_id:
                continue

            total_quantity = min(quantity * num_sellers, max_total_quantity)
            quantity_per_seller = min(total_quantity // num_sellers, max_quantity_per_seller)

            items.extend(
                {"id": sku_id, "quantity": quantity_per_seller, "seller": seller}
                for seller in sellers
            )

        return items

    def batch_simulation(
        self,
        skus: List[Dict[str, int]],
        sellers: List[str],
        postal_code: str,
        max_quantity_per_seller: int = 8000,
        max_total_quantity: int = 24000,
    ) -> Optional[Dict]:
        """
        Simulate multiple SKUs with multiple sellers (used for regionalization).

        Args:
            skus: List of SKUs with quantities, e.g. [{"sku_id": "123", "quantity": 2}, ...]
            sellers: List of sellers
            postal_code: Postal code
            max_quantity_per_seller: Maximum quantity per seller
            max_total_quantity: Maximum total quantity

        Returns:
            Simulation result or None
        """
        if not sellers or not skus:
            return None

        items = self._build_batch_items(skus, sellers, max_quantity_per_seller, max_total_quantity)
        if not items:
            return None

        result = self.cart_simulation(items, postal_code=postal_code, sales_channel=1)
        return result if result.get("items") else None

    def get_region(
        self, postal_code: str, trade_policy: int, country_code: str
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Query the regionalization API to get region and sellers.

        Args:
            postal_code: Postal code
            trade_policy: Trade policy / sales channel ID
            country_code: Country code
        Returns:
            Tuple (region_id, error_message, sellers)
        """
        region_url = f"{self.base_url_vtex}/api/checkout/pub/regions?country={country_code}&postalCode={postal_code}&sc={trade_policy}"

        try:
            response = requests.get(region_url, timeout=self.timeout)
            response.raise_for_status()
            regions_data = response.json()

            if not regions_data:
                logger.warning(
                    "No region found for postal_code=%s country=%s", postal_code, country_code
                )
                return (
                    None,
                    "We don't serve your region.",
                    [],
                )

            region = regions_data[0]
            sellers = region.get("sellers", [])

            if not sellers:
                logger.warning("Region found but no sellers for postal_code=%s", postal_code)
                return (
                    None,
                    "We don't serve your region.",
                    [],
                )

            region_id = region.get("id")
            seller_ids = [seller.get("id") for seller in sellers]

            logger.info(
                "Region resolved: region_id=%s sellers=%d postal_code=%s",
                region_id,
                len(seller_ids),
                postal_code,
            )
            return region_id, None, seller_ids

        except requests.exceptions.RequestException as e:
            logger.error("Region lookup failed for postal_code=%s: %s", postal_code, e)
            return None, f"Error querying regionalization: {e}", []

    def get_sku_details(self, sku_id: str) -> Dict:
        """
        Get SKU details (dimensions, weight, etc).
        Requires VTEX credentials.

        Args:
            sku_id: SKU ID

        Returns:
            Dictionary with SKU details
        """
        default_response = {
            "PackagedHeight": None,
            "PackagedLength": None,
            "PackagedWidth": None,
            "PackagedWeightKg": None,
            "Height": None,
            "Length": None,
            "Width": None,
            "WeightKg": None,
            "CubicWeight": None,
        }

        if not self.vtex_app_key or not self.vtex_app_token:
            return default_response

        url = f"{self.base_url_vtex}/api/catalog/pvt/stockkeepingunit/{sku_id}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)

            if response.status_code != 200:
                return default_response

            data = response.json()

            return {
                "PackagedHeight": data.get("PackagedHeight"),
                "PackagedLength": data.get("PackagedLength"),
                "PackagedWidth": data.get("PackagedWidth"),
                "PackagedWeightKg": data.get("PackagedWeightKg"),
                "Height": data.get("Height"),
                "Length": data.get("Length"),
                "Width": data.get("Width"),
                "WeightKg": data.get("WeightKg"),
                "CubicWeight": data.get("CubicWeight"),
            }

        except Exception:
            return default_response

    def get_product_by_sku(self, sku_id: str) -> Optional[Dict]:
        """
        Search for a specific product by SKU ID.

        Args:
            sku_id: SKU ID

        Returns:
            Product data or None
        """
        search_url = f"{self.base_url_vtex}/api/io/_v/api/intelligent-search/product_search/?query=sku.id:{sku_id}"

        try:
            response = requests.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            products = data.get("products", [])
            if not products:
                return None

            return products[0]

        except Exception as e:
            logger.error("SKU lookup failed for sku_id=%s: %s", sku_id, e)
            return None

    def _fetch_orders(
        self, document: str = None, email: str = None, include_incomplete: bool = False
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Fetch orders from OMS API.

        Args:
            document: Customer document
            include_incomplete: Whether to include incomplete orders

        Returns:
            Tuple of (orders_data, error_message)
        """
        if document:
            url = f"{self.base_url_vtex}/api/oms/pvt/orders?q={document}"
        elif email:
            url = f"{self.base_url_vtex}/api/oms/pvt/orders?q={email}"
        else:
            return None, "Document or email is required"

        if include_incomplete:
            url += "&incompleteOrders=true"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            return None, str(e)

    def list_orders(
        self, document: str = None, email: str = None, include_incomplete: bool = False
    ) -> Dict:
        """
        List orders by document or email.

        Args:
            document: Customer document
            email: Customer email
            include_incomplete: Whether to also fetch incomplete orders

        Returns:
            Dictionary with orders list
        """
        if not document and not email:
            return {"error": "Document or email is required", "list": []}

        # Fetch complete orders (never include incomplete on first call)
        orders_data, error = self._fetch_orders(document, email, include_incomplete=False)
        if error:
            logger.error("Order search failed: %s", error)
            return {"error": f"Error searching orders: {error}", "list": []}

        if not include_incomplete:
            return orders_data

        # Fetch incomplete orders and merge
        incomplete_data, error = self._fetch_orders(document, email, include_incomplete=True)
        if error:
            logger.warning(
                "Incomplete orders fetch failed, returning complete orders only: %s", error
            )
            return orders_data

        # Merge avoiding duplicates by order ID
        existing_ids = {order.get("orderId") for order in orders_data.get("list", [])}
        new_orders = [
            order
            for order in incomplete_data.get("list", [])
            if order.get("orderId") not in existing_ids
        ]
        orders_data.setdefault("list", []).extend(new_orders)

        return orders_data

    def create_order_form(self, sales_channel: int = 1) -> Optional[Dict]:
        """
        Create an order form.
        """
        url = f"{self.base_url_vtex}/api/checkout/pub/orderForms?sc={sales_channel}"
        try:
            response = requests.post(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Order form creation failed: %s", e)
            return None
        except json.JSONDecodeError as e:
            logger.error("Order form JSON decode error: %s", e)
            return None

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Search order by ID.

        Args:
            order_id: Order ID

        Returns:
            Dictionary with order data or None
        """
        if not order_id:
            return None

        url = f"{self.base_url_vtex}/api/oms/pvt/orders/{order_id}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Order fetch failed for order_id=%s: %s", order_id, e)
            return None

    def get_store_details(self) -> Optional[Dict]:
        """
        Get store details from the VTEX API.
        """

        vtex_account = self.format_vtex_account()
        url = f"https://api.vtexcommercestable.com.br/api/catalog_system/pub/saleschannel/default?an={vtex_account}"
        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Store details fetch failed: %s", e)
            return None
