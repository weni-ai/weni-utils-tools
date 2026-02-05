from typing import Dict, List, Optional, Tuple


class Utils:
    def process_products(
        self,
        raw_products: List[Dict],
        max_products: int = 20,
        max_variations: int = 5,
        utm_source: Optional[str] = "weni_concierge",
        extra_product_fields: Optional[List] = None,
        remove_specifications: Optional[List[str]] = None,
    ) -> Dict[str, Dict]:
        """
        Process raw products from the VTEX API.

        Formats, filters, and limits products and their variations.

        Args:
            raw_products: List of raw products from the VTEX API
            max_products: Maximum number of products to return
            max_variations: Maximum variations per product
            utm_source: UTM source for product links
            extra_product_fields: Extra fields to include in the result.
                Can be a string or tuple (path, alias).
                Examples: ["clusterHighlights"], [("items.0.images", "images")]
            remove_specifications: List of specifications to remove from the result.
                Examples: ["sellerId"]

        Returns:
            Dictionary with structured products {product_name: data}
        """
        products_structured: Dict[str, Dict] = {}
        product_count = 0

        for product in raw_products:
            if product_count >= max_products:
                break

            if not product.get("items"):
                continue

            product_name = product.get("productName", "")

            # Process variations (SKUs)
            variations = self._extract_variations(product.get("items", []))
            if not variations:
                continue

            # Limit variations per product
            limited_variations = variations[:max_variations]

            # Build product link
            product_link = f"{self.store_url}{product.get('link', '')}"
            if utm_source:
                product_link += f"?utm_source={utm_source}"

            # Build product data
            product_data = {
                "variations": limited_variations,
                "description": self._truncate_description(product.get("description", "")),
                "brand": product.get("brand", ""),
                "specification_groups": self._format_specifications(
                    product.get("specificationGroups", []),
                    remove_specifications=remove_specifications,
                ),
                "productLink": product_link,
                "imageUrl": self._get_product_image(product),
                "categories": product.get("categories", []),
            }

            # Add extra product fields if specified
            if extra_product_fields:
                self._add_extra_fields(product_data, product, extra_product_fields)

            products_structured[product_name] = product_data
            product_count += 1

        return products_structured

    def _extract_variations(self, items: List[Dict]) -> List[Dict]:
        """Extract and format variations from product items."""
        variations = []

        for item in items:
            sku_id = item.get("itemId")
            if not sku_id:
                continue

            seller_data, seller_id = self._select_best_seller(item.get("sellers", []))
            prices = self._extract_prices_from_seller(seller_data) if seller_data else {}

            variations.append(
                {
                    "sku_id": sku_id,
                    "sku_name": item.get("nameComplete"),
                    "variations": self._format_variations(item.get("variations", [])),
                    "price": prices.get("price"),
                    "spotPrice": prices.get("spot_price"),
                    "listPrice": prices.get("list_price"),
                    "pixPrice": prices.get("pix_price"),
                    "creditCardPrice": prices.get("credit_card_price"),
                    "imageUrl": self._get_first_image(item.get("images", [])),
                    "sellerId": seller_id,
                }
            )

        return variations

    def _get_first_image(self, images: List[Dict]) -> str:
        """Get the first valid image URL from a list of images."""
        if not images or not isinstance(images, list):
            return ""

        for img in images:
            img_url = img.get("imageUrl", "")
            if img_url:
                return self._clean_image_url(img_url)

        return ""

    def _get_product_image(self, product: Dict) -> str:
        """Get the main product image from the first item."""
        if not product:
            return ""

        items = product.get("items") or []
        if not items:
            return ""

        first_item = items[0]
        if not isinstance(first_item, dict):
            return ""

        return self._get_first_image(first_item.get("images", []))

    def _truncate_description(self, description: str, max_length: int = 200) -> str:
        """Truncate description if too long."""
        if len(description) > max_length:
            return description[:max_length] + "..."
        return description

    def _add_extra_fields(
        self,
        product_data: Dict,
        product: Dict,
        extra_fields: List,
    ) -> None:
        """Add extra fields to product data."""
        for field in extra_fields:
            if isinstance(field, tuple):
                path, alias = field
            else:
                path = field
                alias = path.split(".")[-1]

            # will define the field's name by the last part of the path if no alias is provided
            product_data[alias] = self._get_nested_value(product, path)

    def _get_nested_value(self, data: Dict, path: str):
        """
        Get a nested value from a dictionary using dot notation.

        Args:
            data: Source dictionary
            path: Path in format "key1.key2.0.key3"

        Returns:
            Value found or None if not exists
        """
        current = data

        for part in path.split("."):
            if isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None

        return current

    def _extract_prices_from_seller(self, seller_data: Dict) -> Dict[str, Optional[float]]:
        """
        Extract prices from a seller, including PIX and credit card.

        Args:
            seller_data: Seller data

        Returns:
            Dictionary with extracted prices
        """
        commercial_offer = seller_data.get("commertialOffer", {})
        installments = commercial_offer.get("Installments", [])

        prices = {
            "price": commercial_offer.get("Price"),
            "spot_price": commercial_offer.get("spotPrice"),
            "list_price": commercial_offer.get("ListPrice"),
            "pix_price": None,
            "credit_card_price": None,
        }

        # Search for PIX price
        for installment in installments:
            if installment.get("PaymentSystemName") == "Pix":
                prices["pix_price"] = installment.get("Value")
                break

        # Search for credit card price (single payment)
        for installment in installments:
            if (
                installment.get("PaymentSystemName") in ["Visa", "Mastercard", "American Express"]
                and installment.get("NumberOfInstallments") == 1
            ):
                prices["credit_card_price"] = installment.get("Value")
                break

        return prices

    def _select_best_seller(self, sellers: List[Dict]) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Select the best seller for an item.

        Priority:
        1. Default seller with stock
        2. First seller with stock
        3. First available seller

        Args:
            sellers: List of item sellers

        Returns:
            Tuple (seller_data, seller_id)
        """
        if not sellers:
            return None, None

        # Try default seller with stock
        for seller in sellers:
            if (
                seller.get("sellerDefault", False)
                and seller.get("commertialOffer", {}).get("AvailableQuantity", 0) > 0
            ):
                return seller, seller.get("sellerId")

        # Try first with stock
        for seller in sellers:
            if seller.get("commertialOffer", {}).get("AvailableQuantity", 0) > 0:
                return seller, seller.get("sellerId")

        # Fallback: first available
        return sellers[0], sellers[0].get("sellerId")

    def _clean_image_url(self, img_url: str) -> str:
        """Remove query parameters from image URL"""
        if not img_url:
            return ""

        # Remove query parameters
        if "?" in img_url:
            img_url = img_url.split("?")[0]

        # Remove fragment identifier
        if "#" in img_url:
            img_url = img_url.split("#")[0]

        return img_url

    def _format_name_value_pairs(self, items: List[Dict]) -> str:
        """
        Format a list of name-value pairs into a compact string.

        Args:
            items: List of dicts with 'name' and 'values' keys

        Returns:
            String in format "[Name1: Value1, Name2: Value2]"
        """
        compact = [
            f"{item.get('name', '')}: {item.get('values', [''])[0]}"
            for item in items
            if item.get("name") and item.get("values")
        ]
        return f"{{{', '.join(compact)}}}" if compact else "{{}}"

    def _format_variations(self, variation_items: List[Dict]) -> str:
        """
        Convert variations to compact format.

        Args:
            variation_items: List of item variations

        Returns:
            String in format "{Color: White, Size: M}"
        """
        return self._format_name_value_pairs(variation_items)

    def _format_specifications(
        self,
        spec_groups: List[Dict],
        max_groups: int = 3,
        max_specifications_per_group: int = 5,
        remove_specifications: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Format specification groups in a simplified way.

        Args:
            spec_groups: Product specification groups
            max_groups: Maximum number of groups to include
            max_specifications_per_group: Maximum number of specifications per group
            remove_specifications: List of specification names to exclude from result

        Returns:
            Simplified specifications list
        """
        remove_set = set(remove_specifications or [])

        def filter_specs(specs: List[Dict]) -> List[Dict]:
            """Filter out unwanted specifications."""
            if not remove_set:
                return specs
            return [s for s in specs if s.get("name") not in remove_set]

        # Try to find the "allSpecifications" group first
        all_specs_group = next(
            (
                g
                for g in spec_groups
                if g.get("name") == "allSpecifications" and g.get("specifications")
            ),
            None,
        )

        if all_specs_group:
            filtered = filter_specs(all_specs_group["specifications"])
            return [
                {
                    "name": "allSpecifications",
                    "specifications": self._format_name_value_pairs(filtered),
                }
            ]

        # Fallback: use the first groups with specifications
        return [
            {
                "name": group.get("name", ""),
                "specifications": self._format_name_value_pairs(
                    filter_specs(group["specifications"])[:max_specifications_per_group]
                ),
            }
            for group in spec_groups[:max_groups]
            if group.get("specifications")
        ]
