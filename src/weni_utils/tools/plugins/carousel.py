"""
Carousel Plugin - WhatsApp Carousel Sending

Plugin for clients that need to send products as carousel on WhatsApp.
Formats products in XML and sends via Weni API.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import requests

from .base import PluginBase

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class Carousel(PluginBase):
    """
    WhatsApp carousel plugin.

    Features:
    - Formats products in XML for carousel
    - Sends carousel via Weni API
    - Limits number of products in carousel

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[
                Carousel(
                    weni_token="your-token",
                    max_items=10
                )
            ]
        )

        # Carousel is sent automatically after search
        result = concierge.search(
            product_name="t-shirt",
            contact_info={"urn": "whatsapp:5511999999999"}
        )
    """

    name = "carousel"

    def __init__(
        self,
        weni_token: Optional[str] = None,
        weni_jwt_token: Optional[str] = None,
        weni_api_url: str = "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json",
        weni_internal_url: str = "https://flows.weni.ai/api/v2/internals/whatsapp_broadcasts",
        max_items: int = 10,
        auto_send: bool = False,
        timeout: int = 30,
    ):
        """
        Initialize the carousel plugin.

        Args:
            weni_token: Weni authentication token
            weni_jwt_token: Weni JWT authentication token
            weni_api_url: Broadcast API URL
            max_items: Maximum number of items in carousel
            auto_send: If True, sends carousel automatically
            timeout: Request timeout
        """
        self.weni_token = weni_token
        self.weni_jwt_token = weni_jwt_token
        self.weni_api_url = weni_api_url
        self.max_items = max_items
        self.auto_send = auto_send
        self.timeout = timeout

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Send carousel after finalizing result (if auto_send=True).
        """
        if not self.auto_send:
            return result

        contact_urn = context.get_contact("urn")
        if not contact_urn:
            return result

        # Get token (can come from context or initialization)
        token = self.weni_token or context.get_credential("WENI_TOKEN")
        if not token:
            return result

        # Prepare product data for carousel
        products_data = self._extract_products_for_carousel(result)

        if products_data:
            success = self.send_carousel(
                products_data=products_data, contact_urn=contact_urn, auth_token=token
            )

            result["carousel_sent"] = success
            result["carousel_items"] = len(products_data)

        return result

    def _extract_products_for_carousel(self, result: Dict[str, Any]) -> List[Dict]:
        """
        Extract product data from result for carousel format.

        Args:
            result: Search result

        Returns:
            List of formatted products
        """
        products_data = []

        for key, value in result.items():
            # Ignore keys that are not products
            if key in ["region_message", "carousel_sent", "carousel_items"]:
                continue

            if not isinstance(value, dict):
                continue

            # Check if it's a product (has variations)
            if "variations" not in value:
                continue

            # Extract first SKU from each product
            variations = value.get("variations", [])
            if not variations:
                continue

            first_variation = variations[0]

            product_data = {
                "name": first_variation.get("sku_name", key),
                "sku_id": first_variation.get("sku_id"),
                "image": first_variation.get("imageUrl", value.get("imageUrl", "")),
                "price": first_variation.get("price"),
                "list_price": first_variation.get("listPrice"),
                "product_link": value.get("productLink", ""),
            }

            products_data.append(product_data)

            if len(products_data) >= self.max_items:
                break

        return products_data

    def format_price(self, price: Optional[float], list_price: Optional[float] = None) -> str:
        """
        Format price for display.

        Args:
            price: Current price
            list_price: Original price (from/to)

        Returns:
            Formatted string
        """
        if not price:
            return "Price not available"

        price_str = f"R$ {price:.2f}".replace(".", ",")

        if list_price and list_price > price:
            list_price_str = f"R$ {list_price:.2f}".replace(".", ",")
            return f"{price_str} (from {list_price_str})"

        return price_str

    def create_carousel_xml(self, products_data: List[Dict]) -> str:
        """
        Create carousel XML.

        Args:
            products_data: List of product data

        Returns:
            Formatted XML string
        """
        carousel_items = []

        for product in products_data:
            if not product:
                continue

            name = product.get("name", "Product")
            price_display = self.format_price(product.get("price"), product.get("list_price"))
            image_url = product.get("image", "")
            product_link = product.get("product_link", "")

            # Format image in Markdown
            if image_url:
                alt_text = image_url.split("/")[-1] if "/" in image_url else "product"
                formatted_image = f"![{alt_text}]({image_url})"
            else:
                formatted_image = ""

            carousel_item = f"""     <carousel-item>
         <name>{name}</name>
         <price>{price_display}</price>
         <description>{name}</description>
         <product_link>{product_link}</product_link>
         <image>{formatted_image}</image>
     </carousel-item>"""

            carousel_items.append(carousel_item)

        xml_content = """<?xml version="1.0" encoding="UTF-8" ?>
""" + "\n".join(
            carousel_items
        )

        return xml_content

    def send_carousel(self, products_data: List[Dict], contact_urn: str, auth_token: str) -> bool:
        """
        Send carousel via WhatsApp.

        Args:
            products_data: List of product data
            contact_urn: Contact URN
            auth_token: Authentication token

        Returns:
            True if sent successfully
        """
        xml_content = self.create_carousel_xml(products_data)

        headers = {"Authorization": f"Token {auth_token}", "Content-Type": "application/json"}

        payload = {"urns": [contact_urn], "msg": {"text": xml_content}}

        try:
            response = requests.post(
                self.weni_api_url, json=payload, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"ERROR: Error sending carousel: {e}")
            return False

    def send_carousel_for_skus(
        self,
        sku_ids: List[str],
        client: "VTEXClient",
        contact_urn: str,
        auth_token: str,
        seller_id: str = "1",
    ) -> bool:
        """
        Send carousel for a specific list of SKUs.

        Useful for sending carousel manually with selected SKUs.

        Args:
            sku_ids: List of SKU IDs
            client: VTEX client
            contact_urn: Contact URN
            auth_token: Authentication token
            seller_id: Seller ID for price simulation

        Returns:
            True if sent successfully
        """
        products_data = []

        for sku_id in sku_ids[: self.max_items]:
            product = client.get_product_by_sku(sku_id)
            if not product:
                continue

            # Extract product data
            product_name = product.get("productName", "")
            product_link = product.get("link", "")

            # Find specific item
            target_item = None
            for item in product.get("items", []):
                if item.get("itemId") == sku_id:
                    target_item = item
                    break

            if not target_item:
                continue

            # Extract image
            image_url = ""
            images = target_item.get("images", [])
            if images:
                image_url = images[0].get("imageUrl", "")

            # Get price via simulation
            simulation = client.cart_simulation(
                items=[{"id": sku_id, "quantity": 1, "seller": seller_id}]
            )

            price = None
            list_price = None
            items = simulation.get("items", [])
            if items:
                item = items[0]
                price = item.get("price", 0) / 100 if item.get("price") else None
                list_price = item.get("listPrice", 0) / 100 if item.get("listPrice") else None

            products_data.append(
                {
                    "name": target_item.get("nameComplete", product_name),
                    "sku_id": sku_id,
                    "image": image_url,
                    "price": price,
                    "list_price": list_price,
                    "product_link": f"{client.store_url}{product_link}?skuId={sku_id}",
                }
            )

        if not products_data:
            return False

        return self.send_carousel(products_data, contact_urn, auth_token)
