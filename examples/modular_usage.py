"""
Modular Usage Example - weni-tools-utils v1.1.0

This example shows how to use functions independently,
calling each functionality separately.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from weni_utils.tools import (
    check_stock_availability,
    get_product_price,
    get_region,
    get_sellers_by_region,
    search_products,
    simulate_cart,
)

BASE_URL = ""


def simple_search_example():
    """Example 1: Basic product search"""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Simple Search")
    print("=" * 60)

    products = search_products(
        base_url=BASE_URL, product_name="azeite", max_products=3, max_variations=2, timeout=15
    )

    print(f"\n✅ Found {len(products)} products")
    for name, data in products.items():
        print(f"  - {name}: R$ {data['variations'][0].get('price', 'N/A')}")

    return products


def brand_search_example():
    """Example 2: Search with brand filter"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Search with Brand")
    print("=" * 60)

    products = search_products(base_url=BASE_URL, product_name="azeite", max_products=5)

    print(f"\n✅ Found {len(products)} Bosch products")
    for name in products.keys():
        print(f"  - {name}")

    return products


def regionalization_example():
    """Example 3: Standalone regionalization query"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Regionalization (Postal Code)")
    print("=" * 60)

    POSTAL_CODE = "01310-100"

    region_id, error, sellers = get_region(
        base_url=BASE_URL, postal_code=POSTAL_CODE, country="BRA"
    )

    if error:
        print(f"\n Error: {error}")
    else:
        print(f"\n Region ID: {region_id}")
        print(f" Available sellers: {sellers}")

    sellers_only = get_sellers_by_region(BASE_URL, POSTAL_CODE)
    print(f"✅ Sellers (simplified): {sellers_only}")

    return region_id, sellers


def regionalized_search_example():
    """Example 4: Search with region (2 separate calls)"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Regionalized Search (composition)")
    print("=" * 60)

    POSTAL_CODE = "01310-100"

    # Step 1: Get region
    region_id, error, sellers = get_region(BASE_URL, POSTAL_CODE)

    if error:
        print(f"⚠️ {error}")
        return None

    print(f"1. Region obtained: {region_id}")

    # Step 2: Search products with the region
    products = search_products(
        base_url=BASE_URL, product_name="azeite", region_id=region_id, max_products=3
    )

    print(f"2. Products found: {len(products)}")

    return products


def cart_simulation_example():
    """Example 5: Standalone cart simulation"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Cart Simulation")
    print("=" * 60)

    items = [
        {"id": "61556", "quantity": 1, "seller": "1"},
        {"id": "82598", "quantity": 2, "seller": "1"},
    ]

    result = simulate_cart(base_url=BASE_URL, items=items, country="BRA", postal_code="01310-100")

    print("\n✅ Simulation result:")
    for item in result.get("items", []):
        print(f"  - SKU {item.get('id')}: {item.get('availability', 'N/A')}")

    return result


def stock_check_example():
    """Example 6: Check availability of multiple SKUs"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Stock Check (multiple SKUs)")
    print("=" * 60)

    sku_ids = ["61556", "82598", "40240"]

    availability = check_stock_availability(
        base_url=BASE_URL, sku_ids=sku_ids, quantity=1, seller="1"
    )

    print("\n✅ Availability:")
    for sku_id, available in availability.items():
        status = "✅ Available" if available else "❌ Unavailable"
        print(f"  - SKU {sku_id}: {status}")

    return availability


def product_price_example():
    """Example 7: Get product price"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Product Price")
    print("=" * 60)

    price_info = get_product_price(base_url=BASE_URL, sku_id="61556", seller_id="1", quantity=1)

    print(f"\n✅ Price: R$ {price_info.get('price', 'N/A')}")
    print(f"✅ Original price: R$ {price_info.get('list_price', 'N/A')}")

    return price_info


def full_composition_example():
    """Example 8: Full composition (as an agent would do)"""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Full Composition")
    print("=" * 60)

    POSTAL_CODE = "01310-100"
    PRODUCT = "cimento"

    print(f"\n🔍 Searching '{PRODUCT}' for postal code {POSTAL_CODE}...")

    # 1. Get region
    region_id, error, sellers = get_region(BASE_URL, POSTAL_CODE)
    print(f"1. Region: {region_id or error}")

    # 2. Search products
    products = search_products(
        base_url=BASE_URL, product_name=PRODUCT, region_id=region_id, max_products=5
    )
    print(f"2. Products found: {len(products)}")

    # 3. Extract SKUs to check stock
    sku_ids = []
    for product_data in products.values():
        for variation in product_data.get("variations", []):
            sku_ids.append(variation.get("sku_id"))

    # 4. Check availability
    if sku_ids:
        availability = check_stock_availability(base_url=BASE_URL, sku_ids=sku_ids[:10], quantity=1)
        available_count = sum(1 for v in availability.values() if v)
        print(f"3. Available SKUs: {available_count}/{len(availability)}")

    # 5. Return result
    print("\n✅ Search complete!")
    return products


if __name__ == "__main__":
    print("\n" + "🚀" * 30)
    print("   MODULAR USAGE EXAMPLES")
    print("   weni-tools-utils v1.1.0")
    print("🚀" * 30)

    simple_search_example()
    brand_search_example()
    regionalization_example()
    regionalized_search_example()
    cart_simulation_example()
    stock_check_example()
    product_price_example()
    full_composition_example()

    print("\n" + "=" * 60)
    print("✅ ALL EXAMPLES COMPLETED!")
    print("=" * 60 + "\n")
