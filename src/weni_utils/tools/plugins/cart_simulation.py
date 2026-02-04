"""
Cart Simulation Plugin - VTEX Cart Simulation

Plugin for performing cart simulations and checking product availability.
Returns raw data from the VTEX API.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from ..client import VTEXClient


class CartSimulation:
    """
    Plugin for VTEX cart simulation.

    Features:
    - Simple cart simulation
    - Batch cart simulation (multiple sellers)
    - Stock availability check
    - Returns raw API data

    Example:
        from weni_utils.tools.plugins import CartSimulation
        from weni_utils.tools import VTEXClient

        client = VTEXClient(base_url="...", store_url="...")
        cart = CartSimulation(client)

        # Simple simulation
        result = cart.simulate(
            items=[{"id": "61556", "quantity": 1, "seller": "1"}],
            postal_code="01310-100"
        )

        # Batch simulation
        result = cart.simulate_batch(
            sku_id="61556",
            sellers=["store1000", "store1003"],
            postal_code="01310-100",
            quantity=10
        )
    """

    def __init__(self, client: "VTEXClient"):
        """
        Initialize the cart simulation plugin.

        Args:
            client: VTEXClient instance
        """
        self.client = client

    def simulate(
        self,
        items: List[Dict],
        country: str = "BRA",
        postal_code: Optional[str] = None,
    ) -> Dict:
        """
        Perform cart simulation to check availability.

        Args:
            items: List of items [{id, quantity, seller}]
            country: Country code (default: "BRA")
            postal_code: Postal code (optional)

        Returns:
            Raw simulation response from VTEX API

        Example:
            result = cart.simulate(
                items=[
                    {"id": "61556", "quantity": 1, "seller": "1"},
                    {"id": "82598", "quantity": 2, "seller": "1"}
                ],
                postal_code="01310-100"
            )
        """
        return self.client.cart_simulation(
            items=items, country=country, postal_code=postal_code
        )

    def simulate_batch(
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
            max_quantity_per_seller: Maximum quantity per seller (default: 8000)
            max_total_quantity: Maximum total quantity (default: 24000)

        Returns:
            Simulation result or None

        Example:
            result = cart.simulate_batch(
                skus=[{"sku_id": "61556", "quantity": 10}],
                sellers=["store1000", "store1003"],
                postal_code="01310-100",
            )
        """
        return self.client.batch_simulation(
            skus=skus,
            sellers=sellers,
            postal_code=postal_code,
            max_quantity_per_seller=max_quantity_per_seller,
            max_total_quantity=max_total_quantity,
        )

    def check_stock_availability(
        self,
        sku_ids: List[str],
        seller: str = "1",
        quantity: int = 1,
        country: str = "BRA",
        postal_code: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Check stock availability for a list of SKUs.

        Args:
            sku_ids: List of SKU IDs
            seller: Seller ID (default: "1")
            quantity: Quantity to check (default: 1)
            country: Country code (default: "BRA")
            postal_code: Postal code (optional)

        Returns:
            Dictionary {sku_id: available}

        Example:
            availability = cart.check_stock_availability(
                sku_ids=["61556", "82598", "40240"],
                quantity=2
            )
            # {"61556": True, "82598": True, "40240": False}
        """
        items = [
            {"id": sku_id, "quantity": quantity, "seller": seller} for sku_id in sku_ids
        ]

        result = self.simulate(items=items, country=country, postal_code=postal_code)

        availability = {}
        for item in result.get("items", []):
            sku_id = item.get("id")
            is_available = item.get("availability", "").lower() == "available"
            availability[sku_id] = is_available

        # SKUs not present in the response are unavailable
        for sku_id in sku_ids:
            if sku_id not in availability:
                availability[sku_id] = False

        return availability

    def get_product_price(
        self,
        sku_id: str,
        seller_id: str = "1",
        quantity: int = 1,
        country: str = "BRA",
    ) -> Dict[str, Optional[float]]:
        """
        Get product price via cart simulation.

        Args:
            sku_id: SKU ID
            seller_id: Seller ID (default: "1")
            quantity: Quantity (default: 1)
            country: Country code (default: "BRA")

        Returns:
            Dictionary with price and list_price

        Example:
            price = cart.get_product_price(sku_id="61556")
            # {"price": 198.90, "list_price": 249.90}
        """
        result = self.simulate(
            items=[{"id": sku_id, "quantity": quantity, "seller": seller_id}],
            country=country,
        )

        items = result.get("items", [])
        if not items:
            return {"price": None, "list_price": None}

        item = items[0]
        price = item.get("price")
        list_price = item.get("listPrice")

        # Convert from cents if necessary
        if price and price > 1000:
            price = price / 100
        if list_price and list_price > 1000:
            list_price = list_price / 100

        return {"price": price, "list_price": list_price}
