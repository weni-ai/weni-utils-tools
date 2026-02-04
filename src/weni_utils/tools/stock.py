"""
StockManager - Stock and availability management

This module contains the logic to check product availability
and filter results based on stock.
"""

from typing import Any, Dict, List, Optional, Set

from .context import SearchContext


class StockManager():
    """
    Stock and product availability manager.

    Responsible for:
    - Checking availability via cart simulation
    - Filtering products without stock
    - Enriching products with stock information

    Example:
        manager = StockManager()
        products_with_stock = manager.check_availability(
            client, products, context
        )
    """

    def __init__(self):
        """Initialize the stock manager"""
        pass

    def _flatten_products_to_skus(self, products: Dict[str, Dict]) -> List[Dict]:
        """
        Convert product structure to SKU list for simulation.

        Args:
            products: Dictionary of structured products

        Returns:
            List of SKUs with necessary information for simulation
        """
        sku_list = []

        for product_name, product_data in products.items():
            for variation in product_data.get("variations", []):
                sku_list.append(
                    {
                        "sku_id": variation.get("sku_id"),
                        "sku_name": variation.get("sku_name"),
                        "variations": variation.get("variations"),
                        "seller": variation.get("sellerId"),
                        "description": product_data.get("description"),
                        "brand": product_data.get("brand"),
                        "specification_groups": product_data.get("specification_groups"),
                        "categories": product_data.get("categories", []),
                        "imageUrl": variation.get("imageUrl"),
                        "price": variation.get("price"),
                        "spotPrice": variation.get("spotPrice"),
                        "pixPrice": variation.get("pixPrice"),
                        "creditCardPrice": variation.get("creditCardPrice"),
                    }
                )

        return sku_list

    def _select_available_products(
        self, simulation_result: Dict, products_details: List[Dict]
    ) -> List[Dict]:
        """
        Select available products based on cart simulation.

        Args:
            simulation_result: Simulation result
            products_details: List of product details

        Returns:
            List of available products
        """
        available_ids: Set[str] = set()

        for item in simulation_result.get("items", []):
            if item.get("availability", "").lower() == "available":
                original_id = item.get("id")
                if original_id:
                    available_ids.add(original_id)

        return [p for p in products_details if p.get("sku_id") in available_ids]

    def check_availability_simple(
        self, client: Any, products: Dict[str, Dict], context: SearchContext  # VTEXClient
    ) -> List[Dict]:
        """
        Check availability using simple cart simulation.

        Used when there is no regionalization or specific sellers.

        Args:
            client: VTEXClient instance
            products: Dictionary of structured products
            context: Search context

        Returns:
            List of products with available stock
        """
        if not products:
            return []

        # Convert to SKU list
        products_details = self._flatten_products_to_skus(products)

        if not products_details:
            return []

        # Build items for simulation
        items = []
        for product in products_details:
            sku_id = product.get("sku_id")
            seller = product.get("seller", "1")
            items.append({"id": sku_id, "quantity": context.quantity, "seller": seller})

        # Execute simulation
        simulation_result = client.cart_simulation(items=items, country=context.country_code)

        # Filter available products
        return self._select_available_products(simulation_result, products_details)

    def check_availability_with_sellers(
        self,
        client: Any,  # VTEXClient
        products: Dict[str, Dict],
        context: SearchContext,
        priority_categories: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Check availability using batch simulation with specific sellers.

        Used when there is regionalization and a list of sellers.

        Args:
            client: VTEXClient instance
            products: Dictionary of structured products
            context: Search context (must have sellers populated)
            priority_categories: Categories that require special stock logic

        Returns:
            List of products with available stock and seller information
        """
        if not products or not context.sellers:
            return self.check_availability_simple(client, products, context)

        products_details = self._flatten_products_to_skus(products)

        if not products_details:
            return []

        priority_categories = priority_categories or []

        # Build all SKUs with their quantities (single loop)
        skus = []
        for product in products_details:
            sku_id = product.get("sku_id")
            if not sku_id:
                continue

            categories = product.get("categories", [])
            is_priority = self._is_priority_category(categories, priority_categories)
            quantity = max(context.quantity, 1) if is_priority else context.quantity

            skus.append({"sku_id": sku_id, "quantity": quantity})

        if not skus:
            return []

        # Execute batch simulation ONCE for all SKUs
        simulation_result = client.batch_simulation(
            skus=skus,
            sellers=context.sellers,
            postal_code=context.postal_code,
        )

        if not simulation_result:
            return []

        # Process results and enrich products
        products_with_stock = []
        for product in products_details:
            sku_id = product.get("sku_id")
            simulation_item = self._get_best_simulation_item(simulation_result, sku_id)

            if simulation_item and simulation_item.get("availability") == "available":
                product_with_stock = product.copy()
                product_with_stock.update(
                    {
                        "measurementUnit": simulation_item.get("measurementUnit", ""),
                        "unitMultiplier": simulation_item.get("unitMultiplier", 1),
                        "sellerId": simulation_item.get("seller", ""),
                        "available_quantity": simulation_item.get("quantity", 0),
                    }
                )
                products_with_stock.append(product_with_stock)

        return products_with_stock

    def _get_best_simulation_item(
        self, simulation_result: Optional[Dict], sku_id: str
    ) -> Optional[Dict]:
        """
        Extract the best simulation item for a specific SKU.

        Args:
            simulation_result: Full simulation response
            sku_id: SKU ID to find

        Returns:
            Best simulation item or None
        """
        if not simulation_result:
            return None

        items = simulation_result.get("items", [])
        sku_items = [item for item in items if item.get("id") == sku_id]

        if not sku_items:
            return None

        # Return item with highest quantity
        return max(sku_items, key=lambda x: x.get("quantity", 0))

    def _is_priority_category(self, categories: List[str], priority_categories: List[str]) -> bool:
        """
        Check if product belongs to a priority category.

        Args:
            categories: Product categories
            priority_categories: List of priority categories

        Returns:
            True if belongs to priority category
        """
        if not categories or not priority_categories:
            return False

        for category in categories:
            if category in priority_categories:
                return True

        return False

    def filter_products_with_stock(
        self, products_structured: Dict[str, Dict], products_with_stock: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Filter original product structure keeping only those with stock.

        Args:
            products_structured: Original product structure
            products_with_stock: List of SKUs that have stock

        Returns:
            Filtered product structure
        """
        if not products_with_stock:
            return {}

        # Create stock information map by SKU
        stock_info = {}
        for product in products_with_stock:
            sku_id = product.get("sku_id")
            stock_info[sku_id] = {
                "measurementUnit": product.get("measurementUnit", ""),
                "unitMultiplier": product.get("unitMultiplier", 1),
                "deliveryType": product.get("deliveryType", ""),
                "sellerId": product.get("sellerId", ""),
                "available_quantity": product.get("available_quantity", 0),
                "minQuantity": product.get("minQuantity"),
                "valueAtacado": product.get("valueAtacado"),
            }

        # Filter products
        filtered_products = {}

        for product_name, product_data in products_structured.items():
            filtered_variations = []

            for variation in product_data.get("variations", []):
                sku_id = variation.get("sku_id")
                if sku_id in stock_info:
                    # Add stock information to variation
                    variation_with_stock = variation.copy()
                    variation_with_stock.update(stock_info[sku_id])
                    filtered_variations.append(variation_with_stock)

            if filtered_variations:
                filtered_product = product_data.copy()
                filtered_product["variations"] = filtered_variations
                filtered_products[product_name] = filtered_product

        return filtered_products

    def limit_payload_size(
        self, products: Dict[str, Dict], max_size_kb: int = 20
    ) -> Dict[str, Dict]:
        """
        Limit payload size to ensure it doesn't exceed the limit.

        Args:
            products: Product dictionary
            max_size_kb: Maximum size in KB

        Returns:
            Limited product dictionary
        """
        import json

        product_list = [
            {"product_name": name, "product_data": data} for name, data in products.items()
        ]

        json_data = json.dumps(product_list)
        size_kb = len(json_data.encode("utf-8")) / 1024

        while size_kb > max_size_kb and product_list:
            product_list.pop()
            json_data = json.dumps(product_list)
            size_kb = len(json_data.encode("utf-8")) / 1024

        return {item["product_name"]: item["product_data"] for item in product_list}
